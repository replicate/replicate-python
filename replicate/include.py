import os
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable, Dict, Literal, Optional, Tuple

import replicate

from .exceptions import ModelError
from .model import Model
from .prediction import Prediction
from .run import _has_output_iterator_array_type
from .version import Version

__all__ = ["include"]


_RUN_STATE: ContextVar[Literal["load", "setup", "run"] | None] = ContextVar(
    "run_state",
    default=None,
)
_RUN_TOKEN: ContextVar[str | None] = ContextVar("run_token", default=None)


@contextmanager
def run_state(state: Literal["load", "setup", "run"]) -> Any:
    """
    Internal context manager for execution state.
    """
    s = _RUN_STATE.set(state)
    try:
        yield
    finally:
        _RUN_STATE.reset(s)


@contextmanager
def run_token(token: str) -> Any:
    """
    Sets the API token for the current context.
    """
    t = _RUN_TOKEN.set(token)
    try:
        yield
    finally:
        _RUN_TOKEN.reset(t)


def _find_api_token() -> str:
    token = os.environ.get("REPLICATE_API_TOKEN")
    if token:
        print("Using Replicate API token from environment", file=sys.stderr)
        return token

    token = _RUN_TOKEN.get()

    if not token:
        raise ValueError("No run token found")

    return token


@dataclass
class Run:
    """
    Represents a running prediction with access to its version.
    """

    prediction: Prediction
    version: Version

    def wait(self) -> Any:
        """
        Wait for the prediction to complete and return its output.
        """
        self.prediction.wait()

        if self.prediction.status == "failed":
            raise ModelError(self.prediction)

        if _has_output_iterator_array_type(self.version):
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

    def _client(self) -> replicate.Client:
        return replicate.Client(api_token=_find_api_token())

    def _split_function_ref(self) -> Tuple[str, str, Optional[str]]:
        owner, name = self.function_ref.split("/")
        name, version = name.split(":") if ":" in name else (name, None)
        return owner, name, version

    def _model(self) -> Model:
        client = self._client()
        model_owner, model_name, _ = self._split_function_ref()
        return client.models.get(f"{model_owner}/{model_name}")

    def _version(self) -> Version:
        client = self._client()
        model_owner, model_name, model_version = self._split_function_ref()
        model = client.models.get(f"{model_owner}/{model_name}")
        version = (
            model.versions.get(model_version) if model_version else model.latest_version
        )
        return version

    def __call__(self, **inputs: Dict[str, Any]) -> Any:
        run = self.start(**inputs)
        return run.wait()

    def start(self, **inputs: Dict[str, Any]) -> Run:
        """
        Start a prediction with the specified inputs.
        """
        version = self._version()
        prediction = self._client().predictions.create(version=version, input=inputs)
        print(f"Running {self.function_ref}: https://replicate.com/p/{prediction.id}")

        return Run(prediction, version)

    @property
    def default_example(self) -> Optional[Prediction]:
        """
        Get the default example for this model.
        """
        return self._model().default_example

    @property
    def openapi_schema(self) -> dict[Any, Any]:
        """
        Get the OpenAPI schema for this model version.
        """
        return self._version().openapi_schema


def include(function_ref: str) -> Callable[..., Any]:
    """
    Include a Replicate model as a function.

    This function can only be called at the top level.
    """
    if _RUN_STATE.get() != "load":
        raise RuntimeError("You may only call replicate.include at the top level.")

    return Function(function_ref)
