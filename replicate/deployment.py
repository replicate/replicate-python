from typing import TYPE_CHECKING, Any, Dict, List, Union

from typing_extensions import TypedDict, Unpack

from replicate.base_model import BaseModel
from replicate.collection import Collection
from replicate.files import upload_file
from replicate.json import encode_json
from replicate.prediction import Prediction, PredictionCollection

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
    """
    Namespace for operations related to deployments.
    """

    model = Deployment

    def list(self) -> List[Deployment]:
        """
        List deployments.

        Raises:
            NotImplementedError: This method is not implemented.
        """
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

    def create(
        self,
        *args,
        **kwargs: Unpack[TypedDict],  # type: ignore[misc]
    ) -> Deployment:
        """
        Create a deployment.

        Raises:
            NotImplementedError: This method is not implemented.
        """
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
        """
        List predictions in a deployment.

        Raises:
            NotImplementedError: This method is not implemented.
        """
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

    def create(
        self,
        *args,
        **kwargs: Unpack[PredictionCollection.CreateParams],  # type: ignore[misc]
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

        webhook = kwargs.get("webhook")
        webhook_events_filter = kwargs.get("webhook_events_filter")
        stream = kwargs.get("stream")

        input = encode_json(kwargs.get("input"), upload_file=upload_file)
        body: Dict[str, Any] = {
            "input": input,
        }
        if webhook is not None:
            body["webhook"] = webhook
        if webhook_events_filter is not None:
            body["webhook_events_filter"] = webhook_events_filter
        if stream is True:
            body["stream"] = True

        resp = self._client._request(
            "POST",
            f"/v1/deployments/{self._deployment.username}/{self._deployment.name}/predictions",
            json=body,
        )
        obj = resp.json()
        obj["deployment"] = self._deployment
        del obj["version"]
        return self.prepare_model(obj)
