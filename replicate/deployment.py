from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from replicate.base_model import BaseModel
from replicate.collection import Collection
from replicate.files import upload_file
from replicate.json import encode_json
from replicate.prediction import Prediction

if TYPE_CHECKING:
    from replicate.client import Client


class Deployment(BaseModel):
    """
    A deployment of a model hosted on Replicate.
    """

    username: str
    """
    The name of the user or organization that owns the deployment.
    """

    name: str
    """
    The name of the deployment.
    """

    @property
    def predictions(self) -> "DeploymentPredictionCollection":
        """
        Get the predictions for this deployment.
        """

        return DeploymentPredictionCollection(client=self._client, deployment=self)


class DeploymentCollection(Collection):
    model = Deployment

    def list(self) -> List[Deployment]:
        raise NotImplementedError()

    def get(self, name: str) -> Deployment:
        """
        Get a deployment by name.

        Args:
            name: The name of the deployment, in the format `owner/model-name`.
        Returns:
            The model.
        """

        # TODO: fetch model from server
        # TODO: support permanent IDs
        username, name = name.split("/")
        return self.prepare_model({"username": username, "name": name})

    def create(self, **kwargs) -> Deployment:
        raise NotImplementedError()

    def prepare_model(self, attrs: Union[Deployment, Dict]) -> Deployment:
        if isinstance(attrs, BaseModel):
            attrs.id = f"{attrs.username}/{attrs.name}"
        elif isinstance(attrs, dict):
            attrs["id"] = f"{attrs['username']}/{attrs['name']}"
        return super().prepare_model(attrs)


class DeploymentPredictionCollection(Collection):
    model = Prediction

    def __init__(self, client: "Client", deployment: Deployment) -> None:
        super().__init__(client=client)
        self._deployment = deployment

    def list(self) -> List[Prediction]:
        raise NotImplementedError()

    def get(self, id: str) -> Prediction:
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
        return self.prepare_model(obj)

    def create(  # type: ignore
        self,
        input: Dict[str, Any],
        webhook: Optional[str] = None,
        webhook_completed: Optional[str] = None,
        webhook_events_filter: Optional[List[str]] = None,
        *,
        stream: Optional[bool] = None,
        **kwargs,
    ) -> Prediction:
        """
        Create a new prediction with the deployment.

        Args:
            input: The input data for the prediction.
            webhook: The URL to receive a POST request with prediction updates.
            webhook_completed: The URL to receive a POST request when the prediction is completed.
            webhook_events_filter: List of events to trigger webhooks.
            stream: Set to True to enable streaming of prediction output.

        Returns:
            Prediction: The created prediction object.
        """

        input = encode_json(input, upload_file=upload_file)
        body: Dict[str, Any] = {
            "input": input,
        }
        if webhook is not None:
            body["webhook"] = webhook
        if webhook_completed is not None:
            body["webhook_completed"] = webhook_completed
        if webhook_events_filter is not None:
            body["webhook_events_filter"] = webhook_events_filter
        if stream is True:
            body["stream"] = "true"

        resp = self._client._request(
            "POST",
            f"/v1/deployments/{self._deployment.username}/{self._deployment.name}/predictions",
            json=body,
        )
        obj = resp.json()
        obj["deployment"] = self._deployment
        del obj["version"]
        return self.prepare_model(obj)
