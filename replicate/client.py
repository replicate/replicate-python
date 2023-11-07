import os
import random
import re
import time
from datetime import datetime
from typing import (
    Any,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Union,
)

import httpx

from replicate.__about__ import __version__
from replicate.collection import Collections
from replicate.deployment import Deployments
from replicate.exceptions import ModelError, ReplicateError
from replicate.hardware import Hardwares
from replicate.model import Models
from replicate.prediction import Predictions
from replicate.schema import make_schema_backwards_compatible
from replicate.training import Trainings
from replicate.version import Version


class Client:
    """A Replicate API client library"""

    __client: Optional[httpx.Client] = None

    def __init__(
        self,
        api_token: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[httpx.Timeout] = None,
        **kwargs,
    ) -> None:
        super().__init__()

        self._api_token = api_token
        self._base_url = (
            base_url
            or os.environ.get("REPLICATE_API_BASE_URL")
            or "https://api.replicate.com"
        )
        self._timeout = timeout or httpx.Timeout(
            5.0, read=30.0, write=30.0, connect=5.0, pool=10.0
        )
        self._transport = kwargs.pop("transport", httpx.HTTPTransport())
        self._client_kwargs = kwargs

        self.poll_interval = float(os.environ.get("REPLICATE_POLL_INTERVAL", "0.5"))

    @property
    def _client(self) -> httpx.Client:
        if self.__client is None:
            headers = {
                "User-Agent": f"replicate-python/{__version__}",
            }

            api_token = self._api_token or os.environ.get("REPLICATE_API_TOKEN")

            if api_token is not None and api_token != "":
                headers["Authorization"] = f"Token {api_token}"

            self.__client = httpx.Client(
                **self._client_kwargs,
                base_url=self._base_url,
                headers=headers,
                timeout=self._timeout,
                transport=RetryTransport(wrapped_transport=self._transport),
            )

        return self.__client

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        resp = self._client.request(method, path, **kwargs)

        if 400 <= resp.status_code < 600:
            raise ReplicateError(resp.json()["detail"])

        return resp

    @property
    def collections(self) -> Collections:
        """
        Namespace for operations related to collections of models.
        """
        return Collections(client=self)

    @property
    def deployments(self) -> Deployments:
        """
        Namespace for operations related to deployments.
        """
        return Deployments(client=self)

    @property
    def hardware(self) -> Hardwares:
        """
        Namespace for operations related to hardware.
        """
        return Hardwares(client=self)

    @property
    def models(self) -> Models:
        """
        Namespace for operations related to models.
        """
        return Models(client=self)

    @property
    def predictions(self) -> Predictions:
        """
        Namespace for operations related to predictions.
        """
        return Predictions(client=self)

    @property
    def trainings(self) -> Trainings:
        """
        Namespace for operations related to trainings.
        """
        return Trainings(client=self)

    def run(self, model_version: str, **kwargs) -> Union[Any, Iterator[Any]]:  # noqa: ANN401
        """
        Run a model and wait for its output.

        Args:
            model_version: The model version to run, in the format `owner/name:version`
            kwargs: The input to the model, as a dictionary
        Returns:
            The output of the model
        """
        # Split model_version into owner, name, version in format owner/name:version
        match = re.match(
            r"^(?P<owner>[^/]+)/(?P<name>[^:]+):(?P<version>.+)$", model_version
        )
        if not match:
            raise ReplicateError(
                f"Invalid model_version: {model_version}. Expected format: owner/name:version"
            )

        owner = match.group("owner")
        name = match.group("name")
        version_id = match.group("version")

        prediction = self.predictions.create(version=version_id, **kwargs)

        if owner and name:
            # FIXME: There should be a method for fetching a version without first fetching its model
            resp = self._request(
                "GET", f"/v1/models/{owner}/{name}/versions/{version_id}"
            )
            version = Version(**resp.json())

            # Return an iterator of the output
            schema = make_schema_backwards_compatible(
                version.openapi_schema, version.cog_version
            )
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


# Adapted from https://github.com/encode/httpx/issues/108#issuecomment-1132753155
class RetryTransport(httpx.AsyncBaseTransport, httpx.BaseTransport):
    """A custom HTTP transport that automatically retries requests using an exponential backoff strategy
    for specific HTTP status codes and request methods.
    """

    RETRYABLE_METHODS = frozenset(["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"])
    RETRYABLE_STATUS_CODES = frozenset(
        [
            429,  # Too Many Requests
            503,  # Service Unavailable
            504,  # Gateway Timeout
        ]
    )
    MAX_BACKOFF_WAIT = 60

    def __init__(  # pylint: disable=too-many-arguments
        self,
        wrapped_transport: Union[httpx.BaseTransport, httpx.AsyncBaseTransport],
        *,
        max_attempts: int = 10,
        max_backoff_wait: float = MAX_BACKOFF_WAIT,
        backoff_factor: float = 0.1,
        jitter_ratio: float = 0.1,
        retryable_methods: Optional[Iterable[str]] = None,
        retry_status_codes: Optional[Iterable[int]] = None,
    ) -> None:
        self._wrapped_transport = wrapped_transport

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
        jitter = (backoff * self.jitter_ratio) * random.choice([1, -1])  # noqa: S311
        total_backoff = backoff + jitter
        return min(total_backoff, self.max_backoff_wait)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        response = self._wrapped_transport.handle_request(request)  # type: ignore

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

            response = self._wrapped_transport.handle_request(request)  # type: ignore

            attempts_made += 1
            remaining_attempts -= 1

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        response = await self._wrapped_transport.handle_async_request(request)  # type: ignore

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

            response = await self._wrapped_transport.handle_async_request(request)  # type: ignore

            attempts_made += 1
            remaining_attempts -= 1

    async def aclose(self) -> None:
        await self._wrapped_transport.aclose()  # type: ignore

    def close(self) -> None:
        self._wrapped_transport.close()  # type: ignore
