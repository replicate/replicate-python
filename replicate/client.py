import asyncio
import os
import random
import time
from datetime import datetime
from typing import Iterable, Mapping, Optional, Union

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
        return httpx.Client(transport=RetryTransport(httpx.HTTPTransport()), **kwargs)

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
        return httpx.AsyncClient(
            transport=RetryTransport(httpx.HTTPTransport()), **kwargs
        )

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


# Adapted from https://github.com/encode/httpx/issues/108#issuecomment-1132753155
class RetryTransport(httpx.AsyncBaseTransport, httpx.BaseTransport):
    """A custom HTTP transport that automatically retries requests using an exponential backoff strategy
    for specific HTTP status codes and request methods.
    """

    RETRYABLE_METHODS = frozenset(["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"])
    RETRYABLE_STATUS_CODES = frozenset([413, 429, 503, 504])
    MAX_BACKOFF_WAIT = 60

    def __init__(
        self,
        wrapped_transport: Union[httpx.BaseTransport, httpx.AsyncBaseTransport],
        max_attempts: int = 10,
        max_backoff_wait: float = MAX_BACKOFF_WAIT,
        backoff_factor: float = 0.1,
        jitter_ratio: float = 0.1,
        retryable_methods: Iterable[str] = None,
        retry_status_codes: Iterable[int] = None,
    ) -> None:
        self.wrapped_transport = wrapped_transport
        if jitter_ratio < 0 or jitter_ratio > 0.5:
            raise ValueError(
                f"jitter ratio should be between 0 and 0.5, actual {jitter_ratio}"
            )

        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.retryable_methods = (
            frozenset(retryable_methods)
            if retryable_methods
            else self.RETRYABLE_METHODS
        )
        self.retry_status_codes = (
            frozenset(retry_status_codes)
            if retry_status_codes
            else self.RETRYABLE_STATUS_CODES
        )
        self.jitter_ratio = jitter_ratio
        self.max_backoff_wait = max_backoff_wait

    def _calculate_sleep(
        self, attempts_made: int, headers: Union[httpx.Headers, Mapping[str, str]]
    ) -> float:
        retry_after_header = (headers.get("Retry-After") or "").strip()
        if retry_after_header:
            if retry_after_header.isdigit():
                return float(retry_after_header)

            try:
                parsed_date = datetime.fromisoformat(retry_after_header).astimezone()
                diff = (parsed_date - datetime.now().astimezone()).total_seconds()
                if diff > 0:
                    return min(diff, self.max_backoff_wait)
            except ValueError:
                pass

        backoff = self.backoff_factor * (2 ** (attempts_made - 1))
        jitter = (backoff * self.jitter_ratio) * random.choice([1, -1])
        total_backoff = backoff + jitter
        return min(total_backoff, self.max_backoff_wait)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        response = self.wrapped_transport.handle_request(request)

        if request.method not in self.retryable_methods:
            return response

        remaining_attempts = self.max_attempts - 1
        attempts_made = 1

        while True:
            if (
                remaining_attempts < 1
                or response.status_code not in self.retry_status_codes
            ):
                return response

            response.close()

            sleep_for = self._calculate_sleep(attempts_made, response.headers)
            time.sleep(sleep_for)

            response = self.wrapped_transport.handle_request(request)

            attempts_made += 1
            remaining_attempts -= 1

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        response = await self.wrapped_transport.handle_async_request(request)

        if request.method not in self.retryable_methods:
            return response

        remaining_attempts = self.max_attempts - 1
        attempts_made = 1

        while True:
            if (
                remaining_attempts < 1
                or response.status_code not in self.retry_status_codes
            ):
                return response

            response.close()

            sleep_for = self._calculate_sleep(attempts_made, response.headers)
            time.sleep(sleep_for)

            response = await self.wrapped_transport.handle_async_request(request)

            attempts_made += 1
            remaining_attempts -= 1

    async def aclose(self) -> None:
        transport: httpx.AsyncBaseTransport = self._wrapped_transport
        await transport.aclose()

    def close(self) -> None:
        transport: httpx.BaseTransport = self._wrapped_transport
        transport.close()
