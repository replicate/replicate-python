import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Union

from replicate.exceptions import ModelError
from replicate.files import upload_file
from replicate.json import encode_json
from replicate.pagination import Page
from replicate.resource import Namespace, Resource
from replicate.version import Version


class Prediction(Resource):
    """
    A prediction made by a model hosted on Replicate.
    """

    _namespace: "Predictions"

    id: str
    """The unique ID of the prediction."""

    version: Optional[Version]
    """The version of the model used to create the prediction."""

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
            for i in reversed(range(len(lines))):
                line = lines[i].strip()
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
            time.sleep(self._client.poll_interval)  # pylint: disable=no-member
            self.reload()

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

    def cancel(self) -> None:
        """
        Cancels a running prediction.
        """
        self._client._request("POST", f"/v1/predictions/{self.id}/cancel")  # pylint: disable=no-member

    def reload(self) -> None:
        """
        Load this prediction from the server.
        """

        obj = self._namespace.get(self.id)  # pylint: disable=no-member
        for name, value in obj.dict().items():
            setattr(self, name, value)


class Predictions(Namespace):
    """
    Namespace for operations related to predictions.
    """

    model = Prediction

    def list(self, cursor: Union[str, "ellipsis"] = ...) -> Page[Prediction]:  # noqa: F821
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
        return Page[Prediction](self._client, self, **resp.json())

    def get(self, id: str) -> Prediction:  # pylint: disable=invalid-name
        """
        Get a prediction by ID.

        Args:
            id: The ID of the prediction.
        Returns:
            Prediction: The prediction object.
        """

        resp = self._client._request("GET", f"/v1/predictions/{id}")
        obj = resp.json()
        # HACK: resolve this? make it lazy somehow?
        del obj["version"]
        return self._prepare_model(obj)

    def create(
        self,
        version: Union[Version, str],
        input: Dict[str, Any],
        *,
        webhook: Optional[str] = None,
        webhook_completed: Optional[str] = None,
        webhook_events_filter: Optional[List[str]] = None,
        stream: Optional[bool] = None,
    ) -> Prediction:
        """
        Create a new prediction for the specified model version.

        Args:
            version: The model version to use for the prediction.
            input: The input data for the prediction.
            webhook: The URL to receive a POST request with prediction updates.
            webhook_completed: The URL to receive a POST request when the prediction is completed.
            webhook_events_filter: List of events to trigger webhooks.
            stream: Set to True to enable streaming of prediction output.

        Returns:
            Prediction: The created prediction object.
        """

        body = {
            "version": version if isinstance(version, str) else version.id,
            "input": encode_json(input, upload_file=upload_file),
        }

        if webhook is not None:
            body["webhook"] = webhook

        if webhook_completed is not None:
            body["webhook_completed"] = webhook_completed

        if webhook_events_filter is not None:
            body["webhook_events_filter"] = webhook_events_filter

        if stream is not None:
            body["stream"] = stream

        resp = self._client._request(
            "POST",
            "/v1/predictions",
            json=body,
        )
        obj = resp.json()
        if isinstance(version, Version):
            obj["version"] = version
        else:
            del obj["version"]

        return self._prepare_model(obj)
