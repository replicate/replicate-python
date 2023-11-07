from typing import TYPE_CHECKING, Any, Dict, List, Optional

from replicate.files import upload_file
from replicate.json import encode_json
from replicate.prediction import Prediction
from replicate.resource import Namespace, Resource

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    pass  # type: ignore


if TYPE_CHECKING:
    from replicate.client import Client


class Deployment(Resource):
    """
    A deployment of a model hosted on Replicate.
    """

    _client: "Client" = pydantic.PrivateAttr()

    username: str
    """
    The name of the user or organization that owns the deployment.
    """

    name: str
    """
    The name of the deployment.
    """

    @property
    def id(self) -> str:
        return f"{self.username}/{self.name}"

    @property
    def predictions(self) -> "DeploymentPredictions":
        """
        Get the predictions for this deployment.
        """

        return DeploymentPredictions(client=self._client, deployment=self)


class Deployments(Namespace):
    """
    Namespace for operations related to deployments.
    """

    model = Deployment

    def get(self, name: str) -> Deployment:
        """
        Get a deployment by name.

        Args:
            name: The name of the deployment, in the format `owner/model-name`.
        Returns:
            The model.
        """

        username, name = name.split("/")

        deployment = Deployment(username=username, name=name)
        deployment._client = self._client

        return deployment


class DeploymentPredictions(Namespace):
    """
    Namespace for operations related to predictions in a deployment.
    """

    model = Prediction

    def __init__(self, client: "Client", deployment: Deployment) -> None:
        super().__init__(client=client)
        self._deployment = deployment

    def create(
        self,
        input: Dict[str, Any],
        *,
        webhook: Optional[str] = None,
        webhook_completed: Optional[str] = None,
        webhook_events_filter: Optional[List[str]] = None,
        stream: Optional[bool] = None,
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

        body = {
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
            f"/v1/deployments/{self._deployment.username}/{self._deployment.name}/predictions",
            json=body,
        )

        prediction = Prediction(**resp.json())
        prediction._client = self._client

        return prediction
