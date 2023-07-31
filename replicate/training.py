import re
from typing import Any, Dict, List, Optional

from replicate.base_model import BaseModel
from replicate.collection import Collection
from replicate.exceptions import ReplicateException
from replicate.files import upload_file
from replicate.json import encode_json
from replicate.version import Version


class Training(BaseModel):
    """
    A training made for a model hosted on Replicate.
    """

    id: str
    """The unique ID of the training."""

    version: Optional[Version]
    """The version of the model used to create the training."""

    destination: Optional[str]
    """The model destination of the training."""

    status: str
    """The status of the training."""

    input: Optional[Dict[str, Any]]
    """The input to the training."""

    output: Optional[Any]
    """The output of the training."""

    logs: Optional[str]
    """The logs of the training."""

    error: Optional[str]
    """The error encountered during the training, if any."""

    created_at: Optional[str]
    """When the training was created."""

    started_at: Optional[str]
    """When the training was started."""

    completed_at: Optional[str]
    """When the training was completed, if finished."""

    urls: Optional[Dict[str, str]]
    """
    URLs associated with the training.

    The following keys are available:
    - `get`: A URL to fetch the training.
    - `cancel`: A URL to cancel the training.
    """

    def cancel(self) -> None:
        """Cancel a running training"""
        self._client._request("POST", f"/v1/trainings/{self.id}/cancel")


class TrainingCollection(Collection):
    model = Training

    def list(self) -> List[Training]:
        """
        List your trainings.

        Returns:
            List[Training]: A list of training objects.
        """

        resp = self._client._request("GET", "/v1/trainings")
        # TODO: paginate
        trainings = resp.json()["results"]
        for training in trainings:
            # HACK: resolve this? make it lazy somehow?
            del training["version"]
        return [self.prepare_model(obj) for obj in trainings]

    def get(self, id: str) -> Training:
        """
        Get a training by ID.

        Args:
            id: The ID of the training.
        Returns:
            Training: The training object.
        """

        resp = self._client._request(
            "GET",
            f"/v1/trainings/{id}",
        )
        obj = resp.json()
        # HACK: resolve this? make it lazy somehow?
        del obj["version"]
        return self.prepare_model(obj)

    def create(  # type: ignore
        self,
        version: str,
        input: Dict[str, Any],
        destination: str,
        webhook: Optional[str] = None,
        webhook_events_filter: Optional[List[str]] = None,
        **kwargs,
    ) -> Training:
        """
        Create a new training using the specified model version as a base.

        Args:
            version: The ID of the base model version that you're using to train a new model version.
            input: The input to the training.
            destination: The desired model to push to in the format `{owner}/{model_name}`. This should be an existing model owned by the user or organization making the API request.
            webhook: The URL to send a POST request to when the training is completed. Defaults to None.
            webhook_events_filter: The events to send to the webhook. Defaults to None.
        Returns:
            The training object.
        """

        input = encode_json(input, upload_file=upload_file)
        body = {
            "input": input,
            "destination": destination,
        }
        if webhook is not None:
            body["webhook"] = webhook
        if webhook_events_filter is not None:
            body["webhook_events_filter"] = webhook_events_filter

        # Split version in format "username/model_name:version_id"
        match = re.match(
            r"^(?P<username>[^/]+)/(?P<model_name>[^:]+):(?P<version_id>.+)$", version
        )
        if not match:
            raise ReplicateException(
                "version must be in format username/model_name:version_id"
            )
        username = match.group("username")
        model_name = match.group("model_name")
        version_id = match.group("version_id")

        resp = self._client._request(
            "POST",
            f"/v1/models/{username}/{model_name}/versions/{version_id}/trainings",
            json=body,
        )
        obj = resp.json()
        del obj["version"]
        return self.prepare_model(obj)
