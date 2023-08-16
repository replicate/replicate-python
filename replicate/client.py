import asyncio
import os
import time
from typing import Optional

import httpx

from .__about__ import __version__
from .collection import AsyncCollections, Collections
from .exceptions import APIError, ModelError
from .model import AsyncModels, Models
from .prediction import AsyncPredictions, Prediction, Predictions
from .training import AsyncTrainings, Trainings
from .version import VersionIdentifier


class Client:
    """A Replicate API client library"""

    def __init__(
        self,
        api_token: str,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[httpx.Timeout] = None,
        **kwargs,
    ) -> None:
        super().__init__()

        base_url = base_url or os.environ.get(
            "REPLICATE_API_BASE_URL", "https://api.replicate.com/v1"
        )

        timeout = timeout or httpx.Timeout(
            5.0, read=30.0, write=30.0, connect=5.0, pool=10.0
        )

        headers = {
            "Authorization": f"Token {api_token}",
            "User-Agent": f"replicate-python/{__version__}",
        }

        self._client = self._build_client(
            **kwargs,
            base_url=base_url,
            headers=headers,
            timeout=timeout,
        )

    def _build_client(self, **kwargs) -> httpx.Client:
        return httpx.Client(**kwargs)

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        resp = self._client.request(method, path, **kwargs)

        if 400 <= resp.status_code < 600:
            raise APIError.from_response(resp)

        return resp

    @property
    def collections(self) -> Collections:
        return Collections(client=self)

    @property
    def models(self) -> Models:
        return Models(client=self)

    @property
    def predictions(self) -> Predictions:
        return Predictions(client=self)

    @property
    def trainings(self) -> Trainings:
        return Trainings(client=self)

    def run(
        self,
        identifier: VersionIdentifier | str,
        input: dict,
        webhook: Optional[str] = None,
        webhook_completed: Optional[str] = None,
        webhook_events_filter: Optional[list[str]] = None,
        *,
        poll_interval: float = 1.0,
        **kwargs,
    ) -> any:
        """
        Run a model and wait for its output.

        Args:
            identifier: The model version to run, in the form `owner/name:version`
            kwargs: The input to the model, as a dictionary
        Returns:
            The output of the model
        Throws:
            Identifier.InvalidError: If the model identifier is invalid
            ModelError: If the prediction fails
        """

        if not isinstance(identifier, VersionIdentifier):
            identifier = VersionIdentifier.from_string(identifier)

        prediction = self.predictions.create(
            identifier.version,
            input,
            webhook,
            webhook_completed,
            webhook_events_filter,
            **kwargs,
        )

        prediction = self.wait(prediction, poll_interval=poll_interval)

        if prediction.status == "failed":
            raise ModelError(prediction.error)

        return prediction.output

    def wait(self, prediction: Prediction, *, poll_interval: float = 1.0) -> Prediction:
        """
        Wait for a prediction to complete.

        Args:
            prediction: The prediction to wait for.
        """

        while prediction.status not in ["succeeded", "failed", "canceled"]:
            if poll_interval > 0:
                time.sleep(poll_interval)
            prediction = self.predictions.get(prediction.id)

        return prediction


class AsyncClient(Client):
    """An asynchronous Replicate API client library"""

    def _build_client(self, **kwargs) -> httpx.AsyncClient:
        return httpx.AsyncClient(**kwargs)

    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        resp = await self._client.request(method, path, **kwargs)

        if 400 <= resp.status_code < 600:
            raise APIError.from_response(resp)

        return resp

    @property
    def collections(self) -> AsyncCollections:
        return AsyncCollections(client=self)

    @property
    def models(self) -> AsyncModels:
        return AsyncModels(client=self)

    @property
    def predictions(self) -> AsyncPredictions:
        return AsyncPredictions(client=self)

    @property
    def trainings(self) -> AsyncTrainings:
        return AsyncTrainings(client=self)

    async def run(
        self,
        identifier: VersionIdentifier | str,
        input: dict,
        webhook: Optional[str] = None,
        webhook_completed: Optional[str] = None,
        webhook_events_filter: Optional[list[str]] = None,
        *,
        poll_interval: float = 1.0,
        **kwargs,
    ) -> any:
        if not isinstance(identifier, VersionIdentifier):
            identifier = VersionIdentifier.from_string(identifier)

        prediction = await self.predictions.create(
            identifier.version,
            input,
            webhook,
            webhook_completed,
            webhook_events_filter,
            **kwargs,
        )

        prediction = await self.wait(prediction, poll_interval=poll_interval)

        if prediction.status == "failed":
            raise ModelError(prediction.error)

        return prediction.output

    async def wait(
        self, prediction: Prediction, *, poll_interval: float = 1.0
    ) -> Prediction:
        while prediction.status not in ["succeeded", "failed", "canceled"]:
            await asyncio.sleep(poll_interval)
            prediction = await self.predictions.get(prediction.id)

        return prediction
