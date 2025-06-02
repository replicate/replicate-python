# TODO
# - [ ] Support downloading files and conversion into Path when schema is URL
# - [ ] Support asyncio variant
# - [ ] Support list outputs
# - [ ] Support iterator outputs
# - [ ] Support text streaming
# - [ ] Support file streaming
# - [ ] Support reusing output URL when passing to new method
# - [ ] Support lazy downloading of files into Path
# - [ ] Support helpers for working with ContatenateIterator
import inspect
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Dict, Optional, Tuple

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
    import os
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


@dataclass
class Run:
    """
    Represents a running prediction with access to its version.
    """

    prediction: Prediction
    schema: dict

    def wait(self) -> Any:
        """
        Wait for the prediction to complete and return its output.
        """
        self.prediction.wait()

        if self.prediction.status == "failed":
            raise ModelError(self.prediction)

        if _has_concatenate_iterator_output_type(self.schema):
            return "".join(self.prediction.output)

        return self.prediction.output

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
        version = self._version

        if version:
            prediction = self._client().predictions.create(
                version=version, input=inputs
            )
        else:
            prediction = self._client().models.predictions.create(
                model=self._model, input=inputs
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
        schema = self._model.latest_version.openapi_schema
        if cog_version := self._model.latest_version.cog_version:
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
        raise RuntimeError(
            "You may only call cog.ext.pipelines.include at the top level."
        )

    return Function(function_ref)
