# TODO
# - [x] Support downloading files and conversion into Path when schema is URL
# - [x] Support list outputs
# - [x] Support iterator outputs
# - [x] Support helpers for working with ContatenateIterator
# - [ ] Support reusing output URL when passing to new method
# - [ ] Support lazy downloading of files into Path
# - [ ] Support text streaming
# - [ ] Support file streaming
# - [ ] Support asyncio variant
import inspect
import os
import tempfile
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple, Union
from urllib.parse import urlparse

import httpx

from replicate.client import Client
from replicate.exceptions import ModelError, ReplicateError
from replicate.identifier import ModelVersionIdentifier
from replicate.model import Model
from replicate.prediction import Prediction
from replicate.run import make_schema_backwards_compatible
from replicate.version import Version


def _in_module_scope() -> bool:
    """
    Returns True when called from top level module scope.
    """
    if os.getenv("REPLICATE_ALWAYS_ALLOW_USE"):
        return True

    if frame := inspect.currentframe():
        if caller := frame.f_back:
            return caller.f_code.co_name == "<module>"
    return False


__all__ = ["use"]


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
                return PathProxy(item)

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
            return _download_file(output)
        return output

    # Handle array of strings with format=uri
    if output_schema.get("type") == "array":
        items = output_schema.get("items", {})
        if items.get("type") == "string" and items.get("format") == "uri":
            if isinstance(output, list):
                return [
                    _download_file(url)
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
                        result[prop_name] = _download_file(value)

                # Array of files property
                elif prop_schema.get("type") == "array":
                    items = prop_schema.get("items", {})
                    if items.get("type") == "string" and items.get("format") == "uri":
                        if isinstance(value, list):
                            result[prop_name] = [
                                _download_file(url)
                                if isinstance(url, str)
                                and url.startswith(("http://", "https://"))
                                else url
                                for url in value
                            ]

        return result

    return output


class OutputIterator:
    """
    An iterator wrapper that handles both regular iteration and string conversion.
    """

    def __init__(self, iterator_factory, schema: dict, *, is_concatenate: bool) -> None:
        self.iterator_factory = iterator_factory
        self.schema = schema
        self.is_concatenate = is_concatenate

    def __iter__(self) -> Iterator[Any]:
        """Iterate over output items."""
        for chunk in self.iterator_factory():
            if self.is_concatenate:
                yield str(chunk)
            else:
                yield _process_iterator_item(chunk, self.schema)

    def __str__(self) -> str:
        """Convert to string by joining segments with empty string."""
        if self.is_concatenate:
            return "".join([str(segment) for segment in self.iterator_factory()])
        else:
            return str(self.iterator_factory())


class PathProxy(Path):
    def __init__(self, target: str) -> None:
        path: Path | None = None

        def ensure_path() -> Path:
            nonlocal path
            if path is None:
                path = _download_file(target)
            return path

        object.__setattr__(self, "__target__", target)
        object.__setattr__(self, "__path__", ensure_path)

    def __getattribute__(self, name) -> Any:
        if name in ("__path__", "__target__"):
            return object.__getattribute__(self, name)

        # TODO: We should cover other common properties on Path...
        if name == "__class__":
            return Path

        return getattr(object.__getattribute__(self, "__path__")(), name)

    def __setattr__(self, name, value) -> None:
        if name in ("__path__", "__target__"):
            raise ValueError()

        object.__setattr__(object.__getattribute__(self, "__path__")(), name, value)

    def __delattr__(self, name) -> None:
        if name in ("__path__", "__target__"):
            raise ValueError()
        delattr(object.__getattribute__(self, "__path__")(), name)


@dataclass
class Run:
    """
    Represents a running prediction with access to its version.
    """

    prediction: Prediction
    schema: dict

    def wait(self) -> Union[Any, Iterator[Any]]:
        """
        Wait for the prediction to complete and return its output.
        """
        self.prediction.wait()

        if self.prediction.status == "failed":
            raise ModelError(self.prediction)

        # Return an OutputIterator for iterator output types (including concatenate iterators)
        if _has_iterator_output_type(self.schema):
            is_concatenate = _has_concatenate_iterator_output_type(self.schema)
            return OutputIterator(
                lambda: self.prediction.output_iterator(),
                self.schema,
                is_concatenate=is_concatenate,
            )

        # Process output for file downloads based on schema
        return _process_output_with_schema(self.prediction.output, self.schema)

    def logs(self) -> Optional[str]:
        """
        Fetch and return the logs from the prediction.
        """
        self.prediction.reload()

        return self.prediction.logs


@dataclass
class Function:
    """
    A wrapper for a Replicate model that can be called as a function.
    """

    function_ref: str

    def _client(self) -> Client:
        return Client()

    @cached_property
    def _parsed_ref(self) -> Tuple[str, str, Optional[str]]:
        return ModelVersionIdentifier.parse(self.function_ref)

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

    def __call__(self, **inputs: Dict[str, Any]) -> Any:
        run = self.create(**inputs)
        return run.wait()

    def create(self, **inputs: Dict[str, Any]) -> Run:
        """
        Start a prediction with the specified inputs.
        """
        # Process inputs to convert concatenate OutputIterators to strings and PathProxy to URLs
        processed_inputs = {}
        for key, value in inputs.items():
            if isinstance(value, OutputIterator) and value.is_concatenate:
                processed_inputs[key] = str(value)
            elif isinstance(value, PathProxy):
                processed_inputs[key] = object.__getattribute__(value, "__target__")
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

        return Run(prediction, self.openapi_schema)

    @property
    def default_example(self) -> Optional[Prediction]:
        """
        Get the default example for this model.
        """
        raise NotImplementedError("This property has not yet been implemented")

    @cached_property
    def openapi_schema(self) -> dict[Any, Any]:
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


def use(function_ref: str) -> Function:
    """
    Use a Replicate model as a function.

    This function can only be called at the top level of a module.

    Example:

        flux_dev = replicate.use("black-forest-labs/flux-dev")
        output = flux_dev(prompt="make me a sandwich")

    """
    if not _in_module_scope():
        raise RuntimeError("You may only call replicate.use() at the top level.")

    return Function(function_ref)
