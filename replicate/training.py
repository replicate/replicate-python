from typing import Any, Dict, Optional

from .files import upload_file
from .json import encode_json
from .pagination import Page
from .resource import Namespace, Resource
from .version import Version


class Training(Resource):
    """A training made for a model hosted on Replicate."""

    id: str
    """The unique ID of the training."""

    version: Optional[str]
    """The version of the model used to create the training."""

    status: str
    """The status of the training."""

    input: Optional[Dict[str, Any]]
    """The input to the training."""

    output: Optional[Any] = None
    """The output of the training."""

    logs: Optional[str] = None
    """The logs of the training."""

    error: Optional[Any] = None
    """The error encountered during the training, if any."""

    metrics: Optional[dict[str, Any]] = None
    """Metrics for the training."""

    created_at: Optional[str]
    """When the training was created."""

    started_at: Optional[str] = None
    """When the training was started."""

    completed_at: Optional[str] = None
    """When the training was completed, if finished."""

    urls: Optional[Dict[str, str]]
    """URLs associated with the training.

    The following keys are available:
    - `get`: A URL to fetch the training.
    - `cancel`: A URL to cancel the training.
    """


class Trainings(Namespace):
    model = Training

    def get(self, id: str) -> Training:
        """Get a training by ID.

        Args:
            id: The ID of the training.
        Returns:
            Training: The training object.
        """

        resp = self._client.request(
            "GET",
            f"/trainings/{id}",
        )

        return Training(**resp.json())

    def list(self) -> Page[Training]:
        """List your trainings.

        Returns:
            List[Training]: A list of training objects.
        """

        resp = self._client.request("GET", "/v1/trainings")

        return Page[Training](**resp.json())

    def create(  # type: ignore
        self,
        model_owner: str,
        model_name: str,
        version: Version | str,
        destination: str,
        input: dict[str, any],
        webhook: Optional[str] = None,
        webhook_events_filter: Optional[list] = None,
        **kwargs,
    ) -> Training:
        """Create a new training using the specified model version as a base.

        Args:
            version: The ID of the base model version that you're using to train a new model version.
            input: The input to the training.
            destination: The desired model to push to in the format `{owner}/{model_name}`. This should be an existing model owned by the user or organization making the API request.
            webhook: The URL to send a POST request to when the training is completed. Defaults to None.
            webhook_events_filter: The events to send to the webhook. Defaults to None.
        Returns:
            The training object.
        """

        body = {}

        body["input"] = encode_json(input, upload_file=upload_file)

        body["destination"] = destination

        if webhook is not None:
            body["webhook"] = webhook
        if webhook_events_filter is not None:
            body["webhook_events_filter"] = webhook_events_filter

        version_id = version.id if isinstance(version, Version) else version
        resp = self._client.request(
            "POST",
            f"/models/{model_owner}/{model_name}/versions/{version_id}/trainings",
            json=body,
        )

        return Training(**resp.json())

    def cancel(self, training: Training | str) -> Training:
        """Cancel a running training"""

        training_id = training.id if isinstance(training, Training) else training
        resp = self._client.request("POST", f"/trainings/{training_id}/cancel")

        return Training(**resp.json())


class AsyncTrainings(Trainings):
    async def get(self, id: str) -> Training:
        resp = await self._client.request(
            "GET",
            f"/trainings/{id}",
        )

        return Training(**resp.json())

    async def list(self) -> Page[Training]:
        resp = await self._client.request("GET", "/v1/trainings")

        return Page[Training](**resp.json())

    async def create(  # type: ignore
        self,
        model_owner: str,
        model_name: str,
        version: Version | str,
        destination: str,
        input: dict[str, any],
        webhook: Optional[str] = None,
        webhook_events_filter: Optional[list] = None,
        **kwargs,
    ) -> Training:
        body = {}

        body["input"] = encode_json(input, upload_file=upload_file)

        body["destination"] = destination

        if webhook is not None:
            body["webhook"] = webhook
        if webhook_events_filter is not None:
            body["webhook_events_filter"] = webhook_events_filter

        version_id = version.id if isinstance(version, Version) else version
        resp = await self._client.request(
            "POST",
            f"/models/{model_owner}/{model_name}/versions/{version_id}/trainings",
            json=body,
        )

        return Training(**resp.json())

    async def cancel(self, training: Training | str) -> Training:
        training_id = training.id if isinstance(training, Training) else training
        resp = await self._client.request("POST", f"/trainings/{training_id}/cancel")

        return Training(**resp.json())
