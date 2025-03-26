import os
import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Dict, Literal, Optional, Tuple

import replicate

from .exceptions import ModelError
from .model import Model
from .prediction import Prediction
from .run import _has_output_iterator_array_type
from .version import Version

__all__ = ["get_run_state", "get_run_token", "include", "run_state", "run_token"]


_run_state: Optional[Literal["load", "setup", "run"]] = None
_run_token: Optional[str] = None

_state_stack = []
_token_stack = []

_state_lock = threading.RLock()
_token_lock = threading.RLock()


def get_run_state() -> Optional[Literal["load", "setup", "run"]]:
    """
    Get the current run state.
    """
    return _run_state


def get_run_token() -> Optional[str]:
    """
    Get the current API token.
    """
    return _run_token


@contextmanager
def run_state(state: Literal["load", "setup", "run"]) -> Any:
    """
    Context manager for setting the current run state.
    """
    global _run_state

    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("Only the main thread can modify run state")

    with _state_lock:
        _state_stack.append(_run_state)

        _run_state = state

    try:
        yield
    finally:
        with _state_lock:
            _run_state = _state_stack.pop()


@contextmanager
def run_token(token: str) -> Any:
    """
    Context manager for setting the current API token.
    """
    global _run_token

    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("Only the main thread can modify API token")

    with _token_lock:
        _token_stack.append(_run_token)

        _run_token = token

    try:
        yield
    finally:
        with _token_lock:
            _run_token = _token_stack.pop()


def _find_api_token() -> str:
    token = os.environ.get("REPLICATE_API_TOKEN")
    if token:
        print("Using Replicate API token from environment", file=sys.stderr)
        return token

    current_token = get_run_token()
    if current_token is None:
        raise ValueError("No run token found")

    return current_token


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
    if get_run_state() != "load":
        raise RuntimeError("You may only call replicate.include at the top level.")

    return Function(function_ref)
