from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, overload

from typing_extensions import Unpack

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
        **kwargs,
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

    @overload
    def create(  # pylint: disable=arguments-differ disable=too-many-arguments
        self,
        input: Dict[str, Any],
        *,
        webhook: Optional[str] = None,
        webhook_completed: Optional[str] = None,
        webhook_events_filter: Optional[List[str]] = None,
        stream: Optional[bool] = None,
    ) -> Prediction:
        ...

    @overload
    def create(  # pylint: disable=arguments-differ disable=too-many-arguments
        self,
        *,
        input: Dict[str, Any],
        webhook: Optional[str] = None,
        webhook_completed: Optional[str] = None,
        webhook_events_filter: Optional[List[str]] = None,
        stream: Optional[bool] = None,
    ) -> Prediction:
        ...

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

        input = args[0] if len(args) > 0 else kwargs.get("input")
        if input is None:
            raise ValueError(
                "An input must be provided as a positional or keyword argument."
            )

        body = {
            "input": encode_json(input, upload_file=upload_file),
        }

        for key in ["webhook", "webhook_completed", "webhook_events_filter", "stream"]:
            value = kwargs.get(key)
            if value is not None:
                body[key] = value

        resp = self._client._request(
            "POST",
            f"/v1/deployments/{self._deployment.username}/{self._deployment.name}/predictions",
            json=body,
        )
        obj = resp.json()
        obj["deployment"] = self._deployment
        del obj["version"]
        return self.prepare_model(obj)
