from typing import TYPE_CHECKING, Any, Dict

from typing_extensions import Unpack, deprecated

from replicate.prediction import (
    Prediction,
    _create_prediction_body,
    _json_to_prediction,
)
from replicate.resource import Namespace, Resource

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore


if TYPE_CHECKING:
    from replicate.client import Client
    from replicate.prediction import Predictions


class Deployment(Resource):
    """
    A deployment of a model hosted on Replicate.
    """

    _client: "Client" = pydantic.PrivateAttr()

    owner: str
    """
    The name of the user or organization that owns the deployment.
    """

    name: str
    """
    The name of the deployment.
    """

    @property
    @deprecated("Use `deployment.owner` instead.")
    def username(self) -> str:
        """
        The name of the user or organization that owns the deployment.
        This attribute is deprecated and will be removed in future versions.
        """
        return self.owner

    @property
    def id(self) -> str:
        """
        Return the qualified deployment name, in the format `owner/name`.
        """
        return f"{self.owner}/{self.name}"

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

    _client: "Client"

    def get(self, name: str) -> Deployment:
        """
        Get a deployment by name.

        Args:
            name: The name of the deployment, in the format `owner/model-name`.
        Returns:
            The model.
        """

        owner, name = name.split("/", 1)

        deployment = Deployment(owner=owner, name=name)
        deployment._client = self._client

        return deployment

    async def async_get(self, name: str) -> Deployment:
        """
        Get a deployment by name.

        Args:
            name: The name of the deployment, in the format `owner/model-name`.
        Returns:
            The model.
        """

        owner, name = name.split("/", 1)

        deployment = Deployment(owner=owner, name=name)
        deployment._client = self._client

        return deployment


class DeploymentPredictions(Namespace):
    """
    Namespace for operations related to predictions in a deployment.
    """

    _deployment: Deployment

    def __init__(self, client: "Client", deployment: Deployment) -> None:
        super().__init__(client=client)
        self._deployment = deployment

    def create(
        self,
        input: Dict[str, Any],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction:
        """
        Create a new prediction with the deployment.
        """

        body = _create_prediction_body(version=None, input=input, **params)

        resp = self._client._request(
            "POST",
            f"/v1/deployments/{self._deployment.owner}/{self._deployment.name}/predictions",
            json=body,
        )

        return _json_to_prediction(self._client, resp.json())

    async def async_create(
        self,
        input: Dict[str, Any],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction:
        """
        Create a new prediction with the deployment.
        """

        body = _create_prediction_body(version=None, input=input, **params)

        resp = await self._client._async_request(
            "POST",
            f"/v1/deployments/{self._deployment.owner}/{self._deployment.name}/predictions",
            json=body,
        )

        return _json_to_prediction(self._client, resp.json())
