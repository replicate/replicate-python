import re
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union

from typing_extensions import NotRequired, TypedDict, Unpack

from replicate.exceptions import ModelError
from replicate.files import upload_file
from replicate.json import encode_json
from replicate.pagination import Page
from replicate.resource import Namespace, Resource
from replicate.version import Version

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore

if TYPE_CHECKING:
    from replicate.client import Client


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

    status: str
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

    def cancel(self) -> None:
        """
        Cancels a running prediction.
        """

        canceled = self._client.predictions.cancel(self.id)
        for name, value in canceled.dict().items():
            setattr(self, name, value)

    def reload(self) -> None:
        """
        Load this prediction from the server.
        """

        updated = self._client.predictions.get(self.id)
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
            raise ModelError(self.error)

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

    def create(
        self,
        version: Union[Version, str],
        input: Optional[Dict[str, Any]],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction:
        """
        Create a new prediction for the specified model version.
        """

        body = _create_prediction_body(
            version,
            input,
            **params,
        )
        resp = self._client._request(
            "POST",
            "/v1/predictions",
            json=body,
        )

        return _json_to_prediction(self._client, resp.json())

    async def async_create(
        self,
        version: Union[Version, str],
        input: Optional[Dict[str, Any]],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction:
        """
        Create a new prediction for the specified model version.
        """

        body = _create_prediction_body(
            version,
            input,
            **params,
        )
        resp = await self._client._async_request(
            "POST",
            "/v1/predictions",
            json=body,
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


def _create_prediction_body(  # pylint: disable=too-many-arguments
    version: Optional[Union[Version, str]],
    input: Optional[Dict[str, Any]],
    webhook: Optional[str] = None,
    webhook_completed: Optional[str] = None,
    webhook_events_filter: Optional[List[str]] = None,
    stream: Optional[bool] = None,
) -> Dict[str, Any]:
    body = {}

    if input is not None:
        body["input"] = encode_json(input, upload_file=upload_file)

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
