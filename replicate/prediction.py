import asyncio
import re
import time
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    overload,
)

import httpx
from typing_extensions import NotRequired, TypedDict, Unpack

from replicate.exceptions import ModelError, ReplicateError
from replicate.file import FileEncodingStrategy
from replicate.helpers import async_encode_json, encode_json
from replicate.pagination import Page
from replicate.resource import Namespace, Resource
from replicate.stream import EventSource
from replicate.version import Version

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore

if TYPE_CHECKING:
    from replicate.client import Client
    from replicate.deployment import Deployment
    from replicate.model import Model
    from replicate.stream import ServerSentEvent


class Prediction(Resource):
    """
    A prediction made by a model hosted on Replicate.
    """

    _client: "Client" = pydantic.PrivateAttr()

    id: str
    """The unique ID of the prediction."""

    model: str
    """An identifier for the model used to create the prediction, in the form `owner/name`."""

    version: str
    """An identifier for the version of the model used to create the prediction."""

    status: Literal["starting", "processing", "succeeded", "failed", "canceled"]
    """The status of the prediction."""

    input: Optional[Dict[str, Any]]
    """The input to the prediction."""

    output: Optional[Any]
    """The output of the prediction."""

    logs: Optional[str]
    """The logs of the prediction."""

    error: Optional[str]
    """The error encountered during the prediction, if any."""

    metrics: Optional[Dict[str, Any]]
    """Metrics for the prediction."""

    created_at: Optional[str]
    """When the prediction was created."""

    started_at: Optional[str]
    """When the prediction was started."""

    completed_at: Optional[str]
    """When the prediction was completed, if finished."""

    urls: Optional[Dict[str, str]]
    """
    URLs associated with the prediction.

    The following keys are available:
    - `get`: A URL to fetch the prediction.
    - `cancel`: A URL to cancel the prediction.
    """

    @dataclass
    class Progress:
        """
        The progress of a prediction.
        """

        percentage: float
        """The percentage of the prediction that has completed."""

        current: int
        """The number of items that have been processed."""

        total: int
        """The total number of items to process."""

        _pattern = re.compile(
            r"^\s*(?P<percentage>\d+)%\s*\|.+?\|\s*(?P<current>\d+)\/(?P<total>\d+)"
        )

        @classmethod
        def parse(cls, logs: str) -> Optional["Prediction.Progress"]:
            """Parse the progress from the logs of a prediction."""

            lines = logs.split("\n")
            for idx in reversed(range(len(lines))):
                line = lines[idx].strip()
                if cls._pattern.match(line):
                    matches = cls._pattern.findall(line)
                    if len(matches) == 1:
                        percentage, current, total = map(int, matches[0])
                        return cls(percentage / 100.0, current, total)

            return None

    @property
    def progress(self) -> Optional[Progress]:
        """
        The progress of the prediction, if available.
        """

        if self.logs is None or self.logs == "":
            return None

        return Prediction.Progress.parse(self.logs)

    def wait(self) -> None:
        """
        Wait for prediction to finish.
        """

        while self.status not in ["succeeded", "failed", "canceled"]:
            time.sleep(self._client.poll_interval)
            self.reload()

    async def async_wait(self) -> None:
        """
        Wait for prediction to finish asynchronously.
        """

        while self.status not in ["succeeded", "failed", "canceled"]:
            await asyncio.sleep(self._client.poll_interval)
            await self.async_reload()

    def stream(
        self,
        use_file_output: Optional[bool] = None,
    ) -> Iterator["ServerSentEvent"]:
        """
        Stream the prediction output.

        Raises:
            ReplicateError: If the model does not support streaming.
        """

        url = self.urls and self.urls.get("stream", None)
        if not url or not isinstance(url, str):
            raise ReplicateError("Model does not support streaming")

        headers = {}
        headers["Accept"] = "text/event-stream"
        headers["Cache-Control"] = "no-store"

        with self._client._client.stream("GET", url, headers=headers) as response:
            yield from EventSource(
                self._client, response, use_file_output=use_file_output
            )

    async def async_stream(
        self,
        use_file_output: Optional[bool] = None,
    ) -> AsyncIterator["ServerSentEvent"]:
        """
        Stream the prediction output asynchronously.

        Raises:
            ReplicateError: If the model does not support streaming.
        """

        # no-op to enforce the use of 'await' when calling this method
        await asyncio.sleep(0)

        url = self.urls and self.urls.get("stream", None)
        if not url or not isinstance(url, str):
            raise ReplicateError("Model does not support streaming")

        headers = {}
        headers["Accept"] = "text/event-stream"
        headers["Cache-Control"] = "no-store"

        async with self._client._async_client.stream(
            "GET", url, headers=headers
        ) as response:
            async for event in EventSource(
                self._client, response, use_file_output=use_file_output
            ):
                yield event

    def cancel(self) -> None:
        """
        Cancels a running prediction.
        """

        canceled = self._client.predictions.cancel(self.id)
        for name, value in canceled.dict().items():
            setattr(self, name, value)

    async def async_cancel(self) -> None:
        """
        Cancels a running prediction asynchronously.
        """

        canceled = await self._client.predictions.async_cancel(self.id)
        for name, value in canceled.dict().items():
            setattr(self, name, value)

    def reload(self) -> None:
        """
        Load this prediction from the server.
        """

        updated = self._client.predictions.get(self.id)
        for name, value in updated.dict().items():
            setattr(self, name, value)

    async def async_reload(self) -> None:
        """
        Load this prediction from the server asynchronously.
        """

        updated = await self._client.predictions.async_get(self.id)
        for name, value in updated.dict().items():
            setattr(self, name, value)

    def output_iterator(self) -> Iterator[Any]:
        """
        Return an iterator of the prediction output.
        """

        # TODO: check output is list
        previous_output = self.output or []
        while self.status not in ["succeeded", "failed", "canceled"]:
            output = self.output or []
            new_output = output[len(previous_output) :]
            yield from new_output
            previous_output = output
            time.sleep(self._client.poll_interval)  # pylint: disable=no-member
            self.reload()

        if self.status == "failed":
            raise ModelError(self)

        output = self.output or []
        new_output = output[len(previous_output) :]
        yield from new_output

    async def async_output_iterator(self) -> AsyncIterator[Any]:
        """
        Return an asynchronous iterator of the prediction output.
        """

        # TODO: check output is list
        previous_output = self.output or []
        while self.status not in ["succeeded", "failed", "canceled"]:
            output = self.output or []
            new_output = output[len(previous_output) :]
            for item in new_output:
                yield item
            previous_output = output
            await asyncio.sleep(self._client.poll_interval)  # pylint: disable=no-member
            await self.async_reload()

        if self.status == "failed":
            raise ModelError(self)

        output = self.output or []
        new_output = output[len(previous_output) :]
        for output in new_output:
            yield output


class Predictions(Namespace):
    """
    Namespace for operations related to predictions.
    """

    def list(self, cursor: Union[str, "ellipsis", None] = ...) -> Page[Prediction]:  # noqa: F821
        """
        List your predictions.

        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Prediction]: A page of of predictions.
        Raises:
            ValueError: If `cursor` is `None`.
        """

        if cursor is None:
            raise ValueError("cursor cannot be None")

        resp = self._client._request(
            "GET", "/v1/predictions" if cursor is ... else cursor
        )

        obj = resp.json()
        obj["results"] = [
            _json_to_prediction(self._client, result) for result in obj["results"]
        ]

        return Page[Prediction](**obj)

    async def async_list(
        self,
        cursor: Union[str, "ellipsis", None] = ...,  # noqa: F821
    ) -> Page[Prediction]:
        """
        List your predictions.

        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Prediction]: A page of of predictions.
        Raises:
            ValueError: If `cursor` is `None`.
        """

        if cursor is None:
            raise ValueError("cursor cannot be None")

        resp = await self._client._async_request(
            "GET", "/v1/predictions" if cursor is ... else cursor
        )

        obj = resp.json()
        obj["results"] = [
            _json_to_prediction(self._client, result) for result in obj["results"]
        ]

        return Page[Prediction](**obj)

    def get(self, id: str) -> Prediction:
        """
        Get a prediction by ID.

        Args:
            id: The ID of the prediction.
        Returns:
            Prediction: The prediction object.
        """

        resp = self._client._request("GET", f"/v1/predictions/{id}")

        return _json_to_prediction(self._client, resp.json())

    async def async_get(self, id: str) -> Prediction:
        """
        Get a prediction by ID.

        Args:
            id: The ID of the prediction.
        Returns:
            Prediction: The prediction object.
        """

        resp = await self._client._async_request("GET", f"/v1/predictions/{id}")

        return _json_to_prediction(self._client, resp.json())

    class CreatePredictionParams(TypedDict):
        """Parameters for creating a prediction."""

        webhook: NotRequired[str]
        """The URL to receive a POST request with prediction updates."""

        webhook_completed: NotRequired[str]
        """The URL to receive a POST request when the prediction is completed."""

        webhook_events_filter: NotRequired[List[str]]
        """List of events to trigger webhooks."""

        stream: NotRequired[bool]
        """Enable streaming of prediction output."""

        wait: NotRequired[Union[int, bool]]
        """
        Block until the prediction is completed before returning.

        If `True`, keep the request open for up to 60 seconds, falling back to
        polling until the prediction is completed.
        If an `int`, same as True but hold the request for a specified number of
        seconds (between 1 and 60).
        If `False`, poll for the prediction status until completed.
        """

        file_encoding_strategy: NotRequired[FileEncodingStrategy]
        """The strategy to use for encoding files in the prediction input."""

    @overload
    def create(
        self,
        version: Union[Version, str],
        input: Optional[Dict[str, Any]],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction: ...

    @overload
    def create(
        self,
        *,
        model: Union[str, Tuple[str, str], "Model"],
        input: Optional[Dict[str, Any]],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction: ...

    @overload
    def create(
        self,
        *,
        deployment: Union[str, Tuple[str, str], "Deployment"],
        input: Optional[Dict[str, Any]],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction: ...

    def create(  # type: ignore
        self,
        *args,
        model: Optional[Union[str, Tuple[str, str], "Model"]] = None,
        version: Optional[Union[Version, str, "Version"]] = None,
        deployment: Optional[Union[str, Tuple[str, str], "Deployment"]] = None,
        input: Optional[Dict[str, Any]] = None,
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction:
        """
        Create a new prediction for the specified model, version, or deployment.
        """

        wait = params.pop("wait", None)
        file_encoding_strategy = params.pop("file_encoding_strategy", None)

        if args:
            version = args[0] if len(args) > 0 else None
            input = args[1] if len(args) > 1 else input

        if sum(bool(x) for x in [model, version, deployment]) != 1:
            raise ValueError(
                "Exactly one of 'model', 'version', or 'deployment' must be specified."
            )

        if model is not None:
            from replicate.model import (  # pylint: disable=import-outside-toplevel
                Models,
            )

            return Models(self._client).predictions.create(
                model=model,
                input=input or {},
                **params,
            )

        if deployment is not None:
            from replicate.deployment import (  # pylint: disable=import-outside-toplevel
                Deployments,
            )

            return Deployments(self._client).predictions.create(
                deployment=deployment,
                input=input or {},
                **params,
            )

        if input is not None:
            input = encode_json(
                input,
                client=self._client,
                file_encoding_strategy=file_encoding_strategy,
            )

        body = _create_prediction_body(
            version,
            input,
            **params,
        )
        extras = _create_prediction_request_params(wait=wait)
        resp = self._client._request("POST", "/v1/predictions", json=body, **extras)

        return _json_to_prediction(self._client, resp.json())

    @overload
    async def async_create(
        self,
        version: Union[Version, str],
        input: Optional[Dict[str, Any]],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction: ...

    @overload
    async def async_create(
        self,
        *,
        model: Union[str, Tuple[str, str], "Model"],
        input: Optional[Dict[str, Any]],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction: ...

    @overload
    async def async_create(
        self,
        *,
        deployment: Union[str, Tuple[str, str], "Deployment"],
        input: Optional[Dict[str, Any]],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction: ...

    async def async_create(  # type: ignore
        self,
        *args,
        model: Optional[Union[str, Tuple[str, str], "Model"]] = None,
        version: Optional[Union[Version, str, "Version"]] = None,
        deployment: Optional[Union[str, Tuple[str, str], "Deployment"]] = None,
        input: Optional[Dict[str, Any]] = None,
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction:
        """
        Create a new prediction for the specified model, version, or deployment.
        """
        wait = params.pop("wait", None)
        file_encoding_strategy = params.pop("file_encoding_strategy", None)

        if args:
            version = args[0] if len(args) > 0 else None
            input = args[1] if len(args) > 1 else input

        if sum(bool(x) for x in [model, version, deployment]) != 1:
            raise ValueError(
                "Exactly one of 'model', 'version', or 'deployment' must be specified."
            )

        if model is not None:
            from replicate.model import (  # pylint: disable=import-outside-toplevel
                Models,
            )

            return await Models(self._client).predictions.async_create(
                model=model,
                input=input or {},
                **params,
            )

        if deployment is not None:
            from replicate.deployment import (  # pylint: disable=import-outside-toplevel
                Deployments,
            )

            return await Deployments(self._client).predictions.async_create(
                deployment=deployment,
                input=input or {},
                **params,
            )

        if input is not None:
            input = await async_encode_json(
                input,
                client=self._client,
                file_encoding_strategy=file_encoding_strategy,
            )

        body = _create_prediction_body(
            version,
            input,
            **params,
        )
        extras = _create_prediction_request_params(wait=wait)
        resp = await self._client._async_request(
            "POST", "/v1/predictions", json=body, **extras
        )

        return _json_to_prediction(self._client, resp.json())

    def cancel(self, id: str) -> Prediction:
        """
        Cancel a prediction.

        Args:
            id: The ID of the prediction to cancel.
        Returns:
            Prediction: The canceled prediction object.
        """

        resp = self._client._request(
            "POST",
            f"/v1/predictions/{id}/cancel",
        )

        return _json_to_prediction(self._client, resp.json())

    async def async_cancel(self, id: str) -> Prediction:
        """
        Cancel a prediction.

        Args:
            id: The ID of the prediction to cancel.
        Returns:
            Prediction: The canceled prediction object.
        """

        resp = await self._client._async_request(
            "POST",
            f"/v1/predictions/{id}/cancel",
        )

        return _json_to_prediction(self._client, resp.json())


class CreatePredictionRequestParams(TypedDict):
    headers: NotRequired[Optional[dict]]
    timeout: NotRequired[Optional[httpx.Timeout]]


def _create_prediction_request_params(
    wait: Optional[Union[int, bool]],
) -> CreatePredictionRequestParams:
    timeout = _create_prediction_timeout(wait=wait)
    headers = _create_prediction_headers(wait=wait)

    return {
        "headers": headers,
        "timeout": timeout,
    }


def _create_prediction_timeout(
    *, wait: Optional[Union[int, bool]] = None
) -> Union[httpx.Timeout, None]:
    """
    Returns an `httpx.Timeout` instances appropriate for the optional
    `Prefer: wait=x` header that can be provided with the request. This
    will ensure that we give the server enough time to respond with
    a partial prediction in the event that the request times out.
    """

    if not wait:
        return None

    read_timeout = 60.0 if isinstance(wait, bool) else wait
    return httpx.Timeout(5.0, read=read_timeout + 0.5)


def _create_prediction_headers(
    *,
    wait: Optional[Union[int, bool]] = None,
) -> Dict[str, Any]:
    headers = {}

    if wait:
        if isinstance(wait, bool):
            headers["Prefer"] = "wait"
        elif isinstance(wait, int):
            headers["Prefer"] = f"wait={wait}"
    return headers


def _create_prediction_body(  # pylint: disable=too-many-arguments
    version: Optional[Union[Version, str]],
    input: Optional[Dict[str, Any]],
    webhook: Optional[str] = None,
    webhook_completed: Optional[str] = None,
    webhook_events_filter: Optional[List[str]] = None,
    stream: Optional[bool] = None,
    **_kwargs,
) -> Dict[str, Any]:
    body = {}

    if input is not None:
        body["input"] = input

    if version is not None:
        body["version"] = version.id if isinstance(version, Version) else version

    if webhook is not None:
        body["webhook"] = webhook

    if webhook_completed is not None:
        body["webhook_completed"] = webhook_completed

    if webhook_events_filter is not None:
        body["webhook_events_filter"] = webhook_events_filter

    if stream is not None:
        body["stream"] = stream

    return body


def _json_to_prediction(client: "Client", json: Dict[str, Any]) -> Prediction:
    prediction = Prediction(**json)
    prediction._client = client
    return prediction
