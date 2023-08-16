from typing import Any, Dict, List, Optional

from .files import upload_file
from .json import encode_json
from .pagination import Page
from .resource import Namespace, Resource
from .version import Version


class Prediction(Resource):
    """A prediction made by a model hosted on Replicate."""

    id: str
    """The unique ID of the prediction."""

    version: str
    """The version id of the model used to create the prediction."""

    status: str
    """The status of the prediction."""

    input: Optional[Dict[str, Any]]
    """The input to the prediction."""

    output: Optional[Any] = None
    """The output of the prediction."""

    logs: Optional[str] = None
    """The logs of the prediction."""

    error: Optional[Any] = None
    """The error encountered during the prediction, if any."""

    metrics: Optional[dict[str, Any]] = None
    """Metrics for the prediction."""

    created_at: Optional[str]
    """When the prediction was created."""

    started_at: Optional[str] = None
    """When the prediction was started."""

    completed_at: Optional[str] = None
    """When the prediction was completed, if finished."""

    urls: Optional[Dict[str, str]]
    """URLs associated with the prediction.

    The following keys are available:
    - `get`: A URL to fetch the prediction.
    - `cancel`: A URL to cancel the prediction.
    """


class Predictions(Namespace):
    model = Prediction

    def get(self, prediction: Prediction | str) -> Prediction:
        """
        Get a prediction by ID.

        Args:
            id: The ID of the prediction.
        Returns:
            Prediction: The prediction object.
        """

        id = prediction.id if isinstance(prediction, Prediction) else prediction
        resp = self._client.request("GET", f"/predictions/{id}")

        return Prediction(**resp.json())

    def list(self) -> Page[Prediction]:
        """
        List your predictions.

        Returns:
            A page of prediction objects.
        """

        resp = self._client.request("GET", "/v1/predictions")

        return Page[Prediction](**resp.json())

    def create(
        self,
        version: Version | str,
        input: dict,
        webhook: Optional[str] = None,
        webhook_completed: Optional[str] = None,
        webhook_events_filter: Optional[List[str]] = None,
        *,
        stream: Optional[bool] = None,
        **kwargs,
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

        body = {}

        body["version"] = version.id if isinstance(version, Version) else version
        body["input"] = encode_json(input, upload_file=upload_file)

        if webhook is not None:
            body["webhook"] = webhook
        if webhook_completed is not None:
            body["webhook_completed"] = webhook_completed
        if webhook_events_filter is not None:
            body["webhook_events_filter"] = webhook_events_filter
        if stream is True:
            body["stream"] = "true"

        resp = self._client.request(
            "POST",
            "/predictions",
            json=body,
        )

        return Prediction(**resp.json())

    def cancel(self, prediction: Prediction | str) -> Prediction:
        """
        Cancels a running prediction.
        """

        id = prediction.id if isinstance(prediction, Prediction) else prediction
        resp = self._client.request("POST", f"/predictions/{id}/cancel")

        return Prediction(**resp.json())


class AsyncPredictions(Predictions):
    async def get(self, prediction: Prediction | str) -> Prediction:
        id = prediction.id if isinstance(prediction, Prediction) else prediction
        resp = await self._client.request("GET", f"/predictions/{id}")

        return Prediction(**resp.json())

    async def list(self) -> Page[Prediction]:
        resp = await self._client.request("GET", "/v1/predictions")

        return Page[Prediction](**resp.json())

    async def create(
        self,
        version: Version | str,
        input: dict,
        webhook: Optional[str] = None,
        webhook_completed: Optional[str] = None,
        webhook_events_filter: Optional[List[str]] = None,
        *,
        stream: Optional[bool] = None,
        **kwargs,
    ) -> Prediction:
        body = {}

        body["version"] = version.id if isinstance(version, Version) else version
        body["input"] = encode_json(input, upload_file=upload_file)

        if webhook is not None:
            body["webhook"] = webhook
        if webhook_completed is not None:
            body["webhook_completed"] = webhook_completed
        if webhook_events_filter is not None:
            body["webhook_events_filter"] = webhook_events_filter
        if stream is True:
            body["stream"] = "true"

        resp = await self._client.request(
            "POST",
            "/predictions",
            json=body,
        )

        return Prediction(**resp.json())

    async def cancel(self, prediction: Prediction | str) -> Prediction:
        id = prediction.id if isinstance(prediction, Prediction) else prediction
        resp = await self._client.request("POST", f"/predictions/{id}/cancel")

        return Prediction(**resp.json())
