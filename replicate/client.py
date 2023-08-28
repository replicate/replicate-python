import os
import re
from typing import Any, Iterator, Optional, Union

import httpx

from .__about__ import __version__
from .deployment import DeploymentCollection
from .exceptions import ModelError, ReplicateError
from .model import ModelCollection
from .prediction import PredictionCollection
from .training import TrainingCollection


class Client:
    """A Replicate API client library"""

    def __init__(
        self,
        api_token: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[httpx.Timeout] = None,
        **kwargs,
    ) -> None:
        super().__init__()

        api_token = api_token or os.environ.get("REPLICATE_API_TOKEN")

        base_url = base_url or os.environ.get(
            "REPLICATE_API_BASE_URL", "https://api.replicate.com"
        )

        timeout = timeout or httpx.Timeout(
            5.0, read=30.0, write=30.0, connect=5.0, pool=10.0
        )

        self.poll_interval = float(os.environ.get("REPLICATE_POLL_INTERVAL", "0.5"))

        headers = {
            "Authorization": f"Token {api_token}",
            "User-Agent": f"replicate-python/{__version__}",
        }

        transport = kwargs.pop("transport", httpx.HTTPTransport())

        self._client = self._build_client(
            **kwargs,
            base_url=base_url,
            headers=headers,
            timeout=timeout,
            transport=transport,
        )

    def _build_client(self, **kwargs) -> httpx.Client:
        return httpx.Client(**kwargs)

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        resp = self._client.request(method, path, **kwargs)

        if 400 <= resp.status_code < 600:
            raise ReplicateError(resp.json()["detail"])

        return resp

    @property
    def models(self) -> ModelCollection:
        return ModelCollection(client=self)

    @property
    def predictions(self) -> PredictionCollection:
        return PredictionCollection(client=self)

    @property
    def trainings(self) -> TrainingCollection:
        return TrainingCollection(client=self)

    @property
    def deployments(self) -> DeploymentCollection:
        return DeploymentCollection(client=self)

    def run(self, model_version: str, **kwargs) -> Union[Any, Iterator[Any]]:
        """
        Run a model and wait for its output.

        Args:
            model_version: The model version to run, in the format `owner/name:version`
            kwargs: The input to the model, as a dictionary
        Returns:
            The output of the model
        """
        # Split model_version into owner, name, version in format owner/name:version
        m = re.match(r"^(?P<model>[^/]+/[^:]+):(?P<version>.+)$", model_version)
        if not m:
            raise ReplicateError(
                f"Invalid model_version: {model_version}. Expected format: owner/name:version"
            )
        model = self.models.get(m.group("model"))
        version = model.versions.get(m.group("version"))
        prediction = self.predictions.create(version=version, **kwargs)
        # Return an iterator of the output
        schema = version.get_transformed_schema()
        output = schema["components"]["schemas"]["Output"]
        if (
            output.get("type") == "array"
            and output.get("x-cog-array-type") == "iterator"
        ):
            return prediction.output_iterator()

        prediction.wait()
        if prediction.status == "failed":
            raise ModelError(prediction.error)
        return prediction.output
