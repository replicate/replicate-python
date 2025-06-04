# TODO
# - [ ] Support text streaming
# - [ ] Support file streaming
import hashlib
import inspect
import os
import sys
import tempfile
from dataclasses import dataclass
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
from urllib.parse import urlparse

import httpx

from replicate.client import Client
from replicate.exceptions import ModelError, ReplicateError
from replicate.identifier import ModelVersionIdentifier
from replicate.model import Model
from replicate.prediction import Prediction
from replicate.run import make_schema_backwards_compatible
from replicate.version import Version

__all__ = ["use", "get_path_url"]


def _in_repl() -> bool:
    return bool(
        sys.flags.interactive  # python -i
        or hasattr(sys, "ps1")  # prompt strings exist
        or (
            sys.stdin.isatty()  # tty
            and sys.stdout.isatty()
        )
        or ("get_ipython" in globals())
    )


def _in_module_scope() -> bool:
    """
    Returns True when called from top level module scope.
    """
    if os.getenv("REPLICATE_ALWAYS_ALLOW_USE"):
        return True

    # If we're running in a REPL.
    if _in_repl():
        return True

    if frame := inspect.currentframe():
        print(frame)
        if caller := frame.f_back:
            print(caller.f_code.co_name)
            return caller.f_code.co_name == "<module>"

    return False


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


def _has_iterator_output_type(openapi_schema: dict) -> bool:
    """
    Returns true if the model output type is an iterator (non-concatenate).
    """
    output = openapi_schema.get("components", {}).get("schemas", {}).get("Output", {})
    return (
        output.get("type") == "array" and output.get("x-cog-array-type") == "iterator"
    )


def _download_file(url: str) -> Path:
    """
    Download a file from URL to a temporary location and return the Path.
    """
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)

    if not filename or "." not in filename:
        filename = "download"

    _, ext = os.path.splitext(filename)
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        with httpx.stream("GET", url) as response:
            response.raise_for_status()
            for chunk in response.iter_bytes():
                temp_file.write(chunk)

    return Path(temp_file.name)


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


def _process_output_with_schema(output: Any, openapi_schema: dict) -> Any:
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
    if output_schema.get("type") == "object" and isinstance(output, dict):
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
        else:
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
            else:
                # For regular iterators, return the list of items
                items = []
                async for item in self:
                    items.append(item)
                return items

        return _collect_result().__await__()


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
    name: str

    __call__: Callable[Input, Output]


@dataclass
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
                    lambda: self._prediction.output_iterator(),
                    lambda: self._prediction.async_output_iterator(),
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


@dataclass
class Function(Generic[Input, Output]):
    """
    A wrapper for a Replicate model that can be called as a function.
    """

    _ref: str

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
            prediction=prediction, schema=self.openapi_schema, streaming=self._streaming
        )

    @property
    def default_example(self) -> Optional[dict[str, Any]]:
        """
        Get the default example for this model.
        """
        raise NotImplementedError("This property has not yet been implemented")

    @cached_property
    def openapi_schema(self) -> dict[str, Any]:
        """
        Get the OpenAPI schema for this model version.
        """
        latest_version = self._model.latest_version
        if latest_version is None:
            msg = f"Model {self._model.owner}/{self._model.name} has no latest version"
            raise ValueError(msg)

        schema = latest_version.openapi_schema
        if cog_version := latest_version.cog_version:
            schema = make_schema_backwards_compatible(schema, cog_version)
        return schema

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


@dataclass
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
                    lambda: self._prediction.output_iterator(),
                    lambda: self._prediction.async_output_iterator(),
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


@dataclass
class AsyncFunction(Generic[Input, Output]):
    """
    An async wrapper for a Replicate model that can be called as a function.
    """

    function_ref: str
    streaming: bool

    def _client(self) -> Client:
        return Client()

    @cached_property
    def _parsed_ref(self) -> Tuple[str, str, Optional[str]]:
        return ModelVersionIdentifier.parse(self.function_ref)

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
            streaming=self.streaming,
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
        model = await self._model()
        latest_version = model.latest_version
        if latest_version is None:
            msg = f"Model {model.owner}/{model.name} has no latest version"
            raise ValueError(msg)

        schema = latest_version.openapi_schema
        if cog_version := latest_version.cog_version:
            schema = make_schema_backwards_compatible(schema, cog_version)
        return schema


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
    hint: Callable[Input, Output] | None = None,
    streaming: Literal[False] = False,
    use_async: Literal[False] = False,
) -> Function[Input, Output]: ...


@overload
def use(
    ref: str,
    *,
    hint: Callable[Input, Output] | None = None,
    streaming: Literal[True],
    use_async: Literal[False] = False,
) -> Function[Input, Iterator[Output]]: ...


@overload
def use(
    ref: str,
    *,
    hint: Callable[Input, Output] | None = None,
    use_async: Literal[True],
) -> AsyncFunction[Input, Output]: ...


@overload
def use(
    ref: str,
    *,
    hint: Callable[Input, Output] | None = None,
    streaming: Literal[True],
    use_async: Literal[True],
) -> AsyncFunction[Input, AsyncIterator[Output]]: ...


def use(
    ref: str | FunctionRef[Input, Output],
    *,
    hint: Callable[Input, Output] | None = None,
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

    This function can only be called at the top level of a module.

    Example:

        flux_dev = replicate.use("black-forest-labs/flux-dev")
        output = flux_dev(prompt="make me a sandwich")

    """
    if not _in_module_scope():
        raise RuntimeError("You may only call replicate.use() at the top level.")

    try:
        ref = ref.name  # type: ignore
    except AttributeError:
        pass

    if use_async:
        return AsyncFunction(str(ref), streaming=streaming)

    return Function(str(ref), streaming=streaming)


# class Model:
#     name = "foo"

#     def __call__(self) -> str: ...


# def model() -> AsyncIterator[int]: ...


# flux = use("")
# flux_sync = use("", use_async=False)
# streaming_flux_sync = use("", streaming=True, use_async=False)
# flux_async = use("", use_async=True)
# streaming_flux_async = use("", streaming=True, use_async=True)

# flux = use("", hint=model)
# flux_sync = use("", hint=model, use_async=False)
# streaming_flux_sync = use("", hint=model, streaming=False, use_async=False)
# flux_async = use("", hint=model, use_async=True)
# streaming_flux_async = use("", hint=model, streaming=True, use_async=True)

# flux = use(Model())
# flux_sync = use(Model(), use_async=False)
# streaming_flux_sync = use(Model(), streaming=False, use_async=False)
# flux_async = use(Model(), use_async=True)
# streaming_flux_async = use(Model(), streaming=True, use_async=True)
