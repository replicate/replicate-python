# TODO
# - [ ] Support text streaming
# - [ ] Support file streaming
import copy
import hashlib
import os
import tempfile
from functools import cached_property
from pathlib import Path
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Generator,
    Generic,
    Iterator,
    List,
    Literal,
    Optional,
    ParamSpec,
    Protocol,
    Tuple,
    TypeVar,
    cast,
    overload,
)

import httpx

from replicate.client import Client
from replicate.exceptions import ModelError, ReplicateError
from replicate.identifier import ModelVersionIdentifier
from replicate.model import Model
from replicate.prediction import Prediction
from replicate.run import make_schema_backwards_compatible
from replicate.version import Version

__all__ = ["use", "get_path_url"]


def _has_concatenate_iterator_output_type(openapi_schema: dict) -> bool:
    """
    Returns true if the model output type is ConcatenateIterator or
    AsyncConcatenateIterator.
    """
    output = openapi_schema.get("components", {}).get("schemas", {}).get("Output", {})

    if output.get("type") != "array":
        return False

    if output.get("items", {}).get("type") != "string":
        return False

    if output.get("x-cog-array-type") != "iterator":
        return False

    if output.get("x-cog-array-display") != "concatenate":
        return False

    return True


def _process_iterator_item(item: Any, openapi_schema: dict) -> Any:
    """
    Process a single item from an iterator output based on schema.
    """
    output_schema = (
        openapi_schema.get("components", {}).get("schemas", {}).get("Output", {})
    )

    # For array/iterator types, check the items schema
    if (
        output_schema.get("type") == "array"
        and output_schema.get("x-cog-array-type") == "iterator"
    ):
        items_schema = output_schema.get("items", {})
        # If items are file URLs, download them
        if items_schema.get("type") == "string" and items_schema.get("format") == "uri":
            if isinstance(item, str) and item.startswith(("http://", "https://")):
                return URLPath(item)

    return item


def _process_output_with_schema(output: Any, openapi_schema: dict) -> Any:  # pylint: disable=too-many-branches,too-many-nested-blocks
    """
    Process output data, downloading files based on OpenAPI schema.
    """
    output_schema = (
        openapi_schema.get("components", {}).get("schemas", {}).get("Output", {})
    )

    # Handle direct string with format=uri
    if output_schema.get("type") == "string" and output_schema.get("format") == "uri":
        if isinstance(output, str) and output.startswith(("http://", "https://")):
            return URLPath(output)
        return output

    # Handle array of strings with format=uri
    if output_schema.get("type") == "array":
        items = output_schema.get("items", {})
        if items.get("type") == "string" and items.get("format") == "uri":
            if isinstance(output, list):
                return [
                    URLPath(url)
                    if isinstance(url, str) and url.startswith(("http://", "https://"))
                    else url
                    for url in output
                ]
        return output

    # Handle object with properties
    if output_schema.get("type") == "object" and isinstance(output, dict):  # pylint: disable=too-many-nested-blocks
        properties = output_schema.get("properties", {})
        result = output.copy()

        for prop_name, prop_schema in properties.items():
            if prop_name in result:
                value = result[prop_name]

                # Direct file property
                if (
                    prop_schema.get("type") == "string"
                    and prop_schema.get("format") == "uri"
                ):
                    if isinstance(value, str) and value.startswith(
                        ("http://", "https://")
                    ):
                        result[prop_name] = URLPath(value)

                # Array of files property
                elif prop_schema.get("type") == "array":
                    items = prop_schema.get("items", {})
                    if items.get("type") == "string" and items.get("format") == "uri":
                        if isinstance(value, list):
                            result[prop_name] = [
                                URLPath(url)
                                if isinstance(url, str)
                                and url.startswith(("http://", "https://"))
                                else url
                                for url in value
                            ]

        return result

    return output


def _dereference_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Performs basic dereferencing on an OpenAPI schema based on the current schemas generated
    by Replicate. This code assumes that:

    1) References will always point to a field within #/components/schemas and will error
       if the reference is more deeply nested.
    2) That the references when used can be discarded.

    Should something more in-depth be required we could consider using the jsonref package.
    """
    dereferenced = copy.deepcopy(schema)
    schemas = dereferenced.get("components", {}).get("schemas", {})
    dereferenced_refs = set()

    def _resolve_ref(obj: Any) -> Any:
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_path = obj["$ref"]
                if ref_path.startswith("#/components/schemas/"):
                    parts = ref_path.replace("#/components/schemas/", "").split("/", 2)

                    if len(parts) > 1:
                        raise NotImplementedError(
                            f"Unexpected nested $ref found in schema: {ref_path}"
                        )

                    (schema_name,) = parts
                    if schema_name in schemas:
                        dereferenced_refs.add(schema_name)
                        return _resolve_ref(schemas[schema_name])
                    else:
                        return obj
                else:
                    return obj
            else:
                return {key: _resolve_ref(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [_resolve_ref(item) for item in obj]
        else:
            return obj

    result = _resolve_ref(dereferenced)

    # Remove "paths" as these aren't relevant to models.
    result["paths"] = {}

    # Retain Input and Output schemas as these are important.
    dereferenced_refs.discard("Input")
    dereferenced_refs.discard("Output")

    dereferenced_refs.discard("TrainingInput")
    dereferenced_refs.discard("TrainingOutput")

    # Filter out any remaining references that have been inlined.
    result["components"]["schemas"] = {
        k: v
        for k, v in result["components"]["schemas"].items()
        if k not in dereferenced_refs
    }

    return result


T = TypeVar("T")


class OutputIterator[T]:
    """
    An iterator wrapper that handles both regular iteration and string conversion.
    Supports both sync and async iteration patterns.
    """

    def __init__(
        self,
        iterator_factory: Callable[[], Iterator[T]],
        async_iterator_factory: Callable[[], AsyncIterator[T]],
        schema: dict,
        *,
        is_concatenate: bool,
    ) -> None:
        self.iterator_factory = iterator_factory
        self.async_iterator_factory = async_iterator_factory
        self.schema = schema
        self.is_concatenate = is_concatenate

    def __iter__(self) -> Iterator[T]:
        """Iterate over output items synchronously."""
        for chunk in self.iterator_factory():
            if self.is_concatenate:
                yield chunk
            else:
                yield _process_iterator_item(chunk, self.schema)

    async def __aiter__(self) -> AsyncIterator[T]:
        """Iterate over output items asynchronously."""
        async for chunk in self.async_iterator_factory():
            if self.is_concatenate:
                yield chunk
            else:
                yield _process_iterator_item(chunk, self.schema)

    def __str__(self) -> str:
        """Convert to string by joining segments with empty string."""
        if self.is_concatenate:
            return "".join([str(segment) for segment in self.iterator_factory()])
        return str(list(self.iterator_factory()))

    def __await__(self) -> Generator[Any, None, List[T] | str]:
        """Make OutputIterator awaitable, returning appropriate result based on concatenate mode."""

        async def _collect_result() -> List[T] | str:
            if self.is_concatenate:
                # For concatenate iterators, return the joined string
                segments = []
                async for segment in self:
                    segments.append(segment)
                return "".join(segments)
            # For regular iterators, return the list of items
            items = []
            async for item in self:
                items.append(item)
            return items

        return _collect_result().__await__()  # pylint: disable=no-member # return type confuses pylint


class URLPath(os.PathLike):
    """
    A PathLike that defers filesystem ops until first use. Can be used with
    most Python file interfaces like `open()` and `pathlib.Path()`.
    See: https://docs.python.org/3.12/library/os.html#os.PathLike
    """

    def __init__(self, url: str) -> None:
        # store the original URL
        self.__url__ = url

        # compute target path without touching the filesystem
        base = Path(tempfile.gettempdir())
        h = hashlib.sha256(self.__url__.encode("utf-8")).hexdigest()[:16]
        name = Path(httpx.URL(self.__url__).path).name or h
        self.__path__ = base / h / name

    def __fspath__(self) -> str:
        # on first access, create dirs and download if missing
        if not self.__path__.exists():
            subdir = self.__path__.parent
            subdir.mkdir(parents=True, exist_ok=True)
            if not os.access(subdir, os.W_OK):
                raise PermissionError(f"Cannot write to {subdir!r}")

            with httpx.Client() as client, client.stream("GET", self.__url__) as resp:
                resp.raise_for_status()
                with open(self.__path__, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=16_384):
                        f.write(chunk)

        return str(self.__path__)

    def __str__(self) -> str:
        return self.__fspath__()

    def __repr__(self) -> str:
        return f"<URLPath url={self.__url__!r} path={self.__path__!r}>"


def get_path_url(path: Any) -> str | None:
    """
    Return the remote URL (if any) for a Path output from a model.
    """
    try:
        return object.__getattribute__(path, "__url__")
    except AttributeError:
        return None


Input = ParamSpec("Input")
Output = TypeVar("Output")


class FunctionRef(Protocol, Generic[Input, Output]):
    """Represents a Replicate model, providing the model identifier and interface."""

    name: str

    __call__: Callable[Input, Output]


class Run[O]:
    """
    Represents a running prediction with access to the underlying schema.
    """

    _prediction: Prediction
    _schema: dict

    def __init__(
        self, *, prediction: Prediction, schema: dict, streaming: bool
    ) -> None:
        self._prediction = prediction
        self._schema = schema
        self._streaming = streaming

    def output(self) -> O:
        """
        Return the output. For iterator types, returns immediately without waiting.
        For non-iterator types, waits for completion.
        """
        # Return an OutputIterator immediately when streaming, we do this for all
        # model return types regardless of whether they return an iterator.
        if self._streaming:
            is_concatenate = _has_concatenate_iterator_output_type(self._schema)
            return cast(
                O,
                OutputIterator(
                    self._prediction.output_iterator,
                    self._prediction.async_output_iterator,
                    self._schema,
                    is_concatenate=is_concatenate,
                ),
            )

        # For non-streaming, wait for completion and process output
        self._prediction.wait()

        if self._prediction.status == "failed":
            raise ModelError(self._prediction)

        # Handle concatenate iterators - return joined string
        if _has_concatenate_iterator_output_type(self._schema):
            if isinstance(self._prediction.output, list):
                return cast(O, "".join(str(item) for item in self._prediction.output))
            return self._prediction.output

        # Process output for file downloads based on schema
        return _process_output_with_schema(self._prediction.output, self._schema)

    def logs(self) -> Optional[str]:
        """
        Fetch and return the logs from the prediction.
        """
        self._prediction.reload()

        return self._prediction.logs


class Function(Generic[Input, Output]):
    """
    A wrapper for a Replicate model that can be called as a function.
    """

    _ref: str
    _streaming: bool

    def __init__(self, ref: str, *, streaming: bool) -> None:
        self._ref = ref
        self._streaming = streaming

    def __call__(self, *args: Input.args, **inputs: Input.kwargs) -> Output:
        return self.create(*args, **inputs).output()

    def create(self, *_: Input.args, **inputs: Input.kwargs) -> Run[Output]:
        """
        Start a prediction with the specified inputs.
        """
        # Process inputs to convert concatenate OutputIterators to strings and URLPath to URLs
        processed_inputs = {}
        for key, value in inputs.items():
            if isinstance(value, OutputIterator):
                if value.is_concatenate:
                    processed_inputs[key] = str(value)
                else:
                    processed_inputs[key] = list(value)
            elif url := get_path_url(value):
                processed_inputs[key] = url
            else:
                processed_inputs[key] = value

        version = self._version

        if version:
            prediction = self._client().predictions.create(
                version=version, input=processed_inputs
            )
        else:
            prediction = self._client().models.predictions.create(
                model=self._model, input=processed_inputs
            )

        return Run(
            prediction=prediction,
            schema=self.openapi_schema(),
            streaming=self._streaming,
        )

    @property
    def default_example(self) -> Optional[dict[str, Any]]:
        """
        Get the default example for this model.
        """
        raise NotImplementedError("This property has not yet been implemented")

    def openapi_schema(self) -> dict[str, Any]:
        """
        Get the OpenAPI schema for this model version.
        """
        return self._openapi_schema

    @cached_property
    def _openapi_schema(self) -> dict[str, Any]:
        _, _, model_version = self._parsed_ref
        model = self._model

        version = (
            model.versions.get(model_version) if model_version else model.latest_version
        )
        if version is None:
            msg = f"Model {self._model.owner}/{self._model.name} has no version"
            raise ValueError(msg)

        schema = version.openapi_schema
        if cog_version := version.cog_version:
            schema = make_schema_backwards_compatible(schema, cog_version)
        return _dereference_schema(schema)

    def _client(self) -> Client:
        return Client()

    @cached_property
    def _parsed_ref(self) -> Tuple[str, str, Optional[str]]:
        return ModelVersionIdentifier.parse(self._ref)

    @cached_property
    def _model(self) -> Model:
        client = self._client()
        model_owner, model_name, _ = self._parsed_ref
        return client.models.get(f"{model_owner}/{model_name}")

    @cached_property
    def _version(self) -> Version | None:
        _, _, model_version = self._parsed_ref
        model = self._model
        try:
            versions = model.versions.list()
            if len(versions) == 0:
                # if we got an empty list when getting model versions, this
                # model is possibly a procedure instead and should be called via
                # the versionless API
                return None
        except ReplicateError as e:
            if e.status == 404:
                # if we get a 404 when getting model versions, this is an official
                # model and doesn't have addressable versions (despite what
                # latest_version might tell us)
                return None
            raise

        version = (
            model.versions.get(model_version) if model_version else model.latest_version
        )

        return version


class AsyncRun[O]:
    """
    Represents a running prediction with access to its version (async version).
    """

    _prediction: Prediction
    _schema: dict

    def __init__(
        self, *, prediction: Prediction, schema: dict, streaming: bool
    ) -> None:
        self._prediction = prediction
        self._schema = schema
        self._streaming = streaming

    async def output(self) -> O:
        """
        Return the output. For iterator types, returns immediately without waiting.
        For non-iterator types, waits for completion.
        """
        # Return an OutputIterator immediately when streaming, we do this for all
        # model return types regardless of whether they return an iterator.
        if self._streaming:
            is_concatenate = _has_concatenate_iterator_output_type(self._schema)
            return cast(
                O,
                OutputIterator(
                    self._prediction.output_iterator,
                    self._prediction.async_output_iterator,
                    self._schema,
                    is_concatenate=is_concatenate,
                ),
            )

        # For non-streaming, wait for completion and process output
        await self._prediction.async_wait()

        if self._prediction.status == "failed":
            raise ModelError(self._prediction)

        # Handle concatenate iterators - return joined string
        if _has_concatenate_iterator_output_type(self._schema):
            if isinstance(self._prediction.output, list):
                return cast(O, "".join(str(item) for item in self._prediction.output))
            return self._prediction.output

        # Process output for file downloads based on schema
        return _process_output_with_schema(self._prediction.output, self._schema)

    async def logs(self) -> Optional[str]:
        """
        Fetch and return the logs from the prediction asynchronously.
        """
        await self._prediction.async_reload()

        return self._prediction.logs


class AsyncFunction(Generic[Input, Output]):
    """
    An async wrapper for a Replicate model that can be called as a function.
    """

    _ref: str
    _streaming: bool
    _openapi_schema: dict[str, Any] | None = None

    def __init__(self, ref: str, *, streaming: bool) -> None:
        self._ref = ref
        self._streaming = streaming

    def _client(self) -> Client:
        return Client()

    @cached_property
    def _parsed_ref(self) -> Tuple[str, str, Optional[str]]:
        return ModelVersionIdentifier.parse(self._ref)

    async def _model(self) -> Model:
        client = self._client()
        model_owner, model_name, _ = self._parsed_ref
        return await client.models.async_get(f"{model_owner}/{model_name}")

    async def _version(self) -> Version | None:
        _, _, model_version = self._parsed_ref
        model = await self._model()
        try:
            versions = await model.versions.async_list()
            if len(versions) == 0:
                # if we got an empty list when getting model versions, this
                # model is possibly a procedure instead and should be called via
                # the versionless API
                return None
        except ReplicateError as e:
            if e.status == 404:
                # if we get a 404 when getting model versions, this is an official
                # model and doesn't have addressable versions (despite what
                # latest_version might tell us)
                return None
            raise

        if model_version:
            version = await model.versions.async_get(model_version)
        else:
            version = model.latest_version

        return version

    async def __call__(self, *args: Input.args, **inputs: Input.kwargs) -> Output:
        run = await self.create(*args, **inputs)
        return await run.output()

    async def create(self, *_: Input.args, **inputs: Input.kwargs) -> AsyncRun[Output]:
        """
        Start a prediction with the specified inputs asynchronously.
        """
        # Process inputs to convert concatenate OutputIterators to strings and URLPath to URLs
        processed_inputs = {}
        for key, value in inputs.items():
            if isinstance(value, OutputIterator):
                processed_inputs[key] = await value
            elif url := get_path_url(value):
                processed_inputs[key] = url
            else:
                processed_inputs[key] = value

        version = await self._version()

        if version:
            prediction = await self._client().predictions.async_create(
                version=version, input=processed_inputs
            )
        else:
            model = await self._model()
            prediction = await self._client().models.predictions.async_create(
                model=model, input=processed_inputs
            )

        return AsyncRun(
            prediction=prediction,
            schema=await self.openapi_schema(),
            streaming=self._streaming,
        )

    @property
    def default_example(self) -> Optional[dict[str, Any]]:
        """
        Get the default example for this model.
        """
        raise NotImplementedError("This property has not yet been implemented")

    async def openapi_schema(self) -> dict[str, Any]:
        """
        Get the OpenAPI schema for this model version asynchronously.
        """
        if not self._openapi_schema:
            _, _, model_version = self._parsed_ref

            model = await self._model()
            if model_version:
                version = await model.versions.async_get(model_version)
            else:
                version = model.latest_version

            if version is None:
                msg = f"Model {model.owner}/{model.name} has no version"
                raise ValueError(msg)

            schema = version.openapi_schema
            if cog_version := version.cog_version:
                schema = make_schema_backwards_compatible(schema, cog_version)

            self._openapi_schema = _dereference_schema(schema)

        return self._openapi_schema


@overload
def use(ref: FunctionRef[Input, Output]) -> Function[Input, Output]: ...


@overload
def use(
    ref: FunctionRef[Input, Output], *, streaming: Literal[False]
) -> Function[Input, Output]: ...


@overload
def use(
    ref: FunctionRef[Input, Output], *, use_async: Literal[False]
) -> Function[Input, Output]: ...


@overload
def use(
    ref: FunctionRef[Input, Output], *, use_async: Literal[True]
) -> AsyncFunction[Input, Output]: ...


@overload
def use(
    ref: FunctionRef[Input, Output],
    *,
    streaming: Literal[False],
    use_async: Literal[True],
) -> AsyncFunction[Input, Output]: ...


@overload
def use(
    ref: FunctionRef[Input, Output],
    *,
    streaming: Literal[True],
    use_async: Literal[True],
) -> AsyncFunction[Input, AsyncIterator[Output]]: ...


@overload
def use(
    ref: FunctionRef[Input, Output],
    *,
    streaming: Literal[False],
    use_async: Literal[False],
) -> AsyncFunction[Input, AsyncIterator[Output]]: ...


@overload
def use(
    ref: str,
    *,
    hint: Callable[Input, Output] | None = None,  # pylint: disable=unused-argument
    streaming: Literal[False] = False,
    use_async: Literal[False] = False,
) -> Function[Input, Output]: ...


@overload
def use(
    ref: str,
    *,
    hint: Callable[Input, Output] | None = None,  # pylint: disable=unused-argument
    streaming: Literal[True],
    use_async: Literal[False] = False,
) -> Function[Input, Iterator[Output]]: ...


@overload
def use(
    ref: str,
    *,
    hint: Callable[Input, Output] | None = None,  # pylint: disable=unused-argument
    use_async: Literal[True],
) -> AsyncFunction[Input, Output]: ...


@overload
def use(
    ref: str,
    *,
    hint: Callable[Input, Output] | None = None,  # pylint: disable=unused-argument
    streaming: Literal[True],
    use_async: Literal[True],
) -> AsyncFunction[Input, AsyncIterator[Output]]: ...


def use(
    ref: str | FunctionRef[Input, Output],
    *,
    hint: Callable[Input, Output] | None = None,  # pylint: disable=unused-argument # required for type inference
    streaming: bool = False,
    use_async: bool = False,
) -> (
    Function[Input, Output]
    | AsyncFunction[Input, Output]
    | Function[Input, Iterator[Output]]
    | AsyncFunction[Input, AsyncIterator[Output]]
):
    """
    Use a Replicate model as a function.

    Example:

        flux_dev = replicate.use("black-forest-labs/flux-dev")
        output = flux_dev(prompt="make me a sandwich")

    """
    try:
        ref = ref.name  # type: ignore
    except AttributeError:
        pass

    if use_async:
        return AsyncFunction(str(ref), streaming=streaming)

    return Function(str(ref), streaming=streaming)
