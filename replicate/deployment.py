from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, TypedDict, Union

from typing_extensions import Unpack, deprecated

from replicate.account import Account
from replicate.helpers import async_encode_json, encode_json
from replicate.pagination import Page
from replicate.prediction import (
    Prediction,
    _create_prediction_body,
    _create_prediction_request_params,
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

    class Release(Resource):
        """
        A release of a deployment.
        """

        number: int
        """
        The release number.
        """

        model: str
        """
        The model identifier string in the format of `{model_owner}/{model_name}`.
        """

        version: str
        """
        The ID of the model version used in the release.
        """

        created_at: str
        """
        The time the release was created.
        """

        created_by: Optional[Account]
        """
        The account that created the release.
        """

        class Configuration(Resource):
            """
            A configuration for a deployment.
            """

            hardware: str
            """
            The SKU for the hardware used to run the model.
            """

            min_instances: int
            """
            The minimum number of instances for scaling.
            """

            max_instances: int
            """
            The maximum number of instances for scaling.
            """

        configuration: Configuration
        """
        The deployment configuration.
        """

    current_release: Optional[Release]
    """
    The current release of the deployment.
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

    def list(
        self,
        cursor: Union[str, "ellipsis", None] = ...,  # noqa: F821
    ) -> Page[Deployment]:
        """
        List all deployments.

        Returns:
            A page of Deployments.
        """

        if cursor is None:
            raise ValueError("cursor cannot be None")

        resp = self._client._request(
            "GET", "/v1/deployments" if cursor is ... else cursor
        )

        obj = resp.json()
        obj["results"] = [
            _json_to_deployment(self._client, result) for result in obj["results"]
        ]

        return Page[Deployment](**obj)

    async def async_list(
        self,
        cursor: Union[str, "ellipsis", None] = ...,  # noqa: F821
    ) -> Page[Deployment]:
        """
        List all deployments.

        Returns:
            A page of Deployments.
        """
        if cursor is None:
            raise ValueError("cursor cannot be None")

        resp = await self._client._async_request(
            "GET", "/v1/deployments" if cursor is ... else cursor
        )

        obj = resp.json()
        obj["results"] = [
            _json_to_deployment(self._client, result) for result in obj["results"]
        ]

        return Page[Deployment](**obj)

    def get(self, name: str) -> Deployment:
        """
        Get a deployment by name.

        Args:
            name: The name of the deployment, in the format `owner/model-name`.
        Returns:
            The model.
        """

        owner, name = name.split("/", 1)

        resp = self._client._request(
            "GET",
            f"/v1/deployments/{owner}/{name}",
        )

        return _json_to_deployment(self._client, resp.json())

    async def async_get(self, name: str) -> Deployment:
        """
        Get a deployment by name.

        Args:
            name: The name of the deployment, in the format `owner/model-name`.
        Returns:
            The model.
        """

        owner, name = name.split("/", 1)

        resp = await self._client._async_request(
            "GET",
            f"/v1/deployments/{owner}/{name}",
        )

        return _json_to_deployment(self._client, resp.json())

    class CreateDeploymentParams(TypedDict):
        """
        Parameters for creating a new deployment.
        """

        name: str
        """The name of the deployment."""

        model: str
        """The model identifier string in the format of `{model_owner}/{model_name}`."""

        version: str
        """The version of the model to deploy."""

        hardware: str
        """The SKU for the hardware used to run the model."""

        min_instances: int
        """The minimum number of instances for scaling."""

        max_instances: int
        """The maximum number of instances for scaling."""

    def create(self, **params: Unpack[CreateDeploymentParams]) -> Deployment:
        """
        Create a new deployment.

        Args:
            params: Configuration for the new deployment.
        Returns:
            The newly created Deployment.
        """

        if name := params.get("name", None):
            if "/" in name:
                _, name = name.split("/", 1)
            params["name"] = name

        resp = self._client._request(
            "POST",
            "/v1/deployments",
            json=params,
        )

        return _json_to_deployment(self._client, resp.json())

    async def async_create(
        self, **params: Unpack[CreateDeploymentParams]
    ) -> Deployment:
        """
        Create a new deployment.

        Args:
            params: Configuration for the new deployment.
        Returns:
            The newly created Deployment.
        """

        if name := params.get("name", None):
            if "/" in name:
                _, name = name.split("/", 1)
            params["name"] = name

        resp = await self._client._async_request(
            "POST",
            "/v1/deployments",
            json=params,
        )

        return _json_to_deployment(self._client, resp.json())

    class UpdateDeploymentParams(TypedDict, total=False):
        """
        Parameters for updating an existing deployment.
        """

        version: str
        """The version of the model to deploy."""

        hardware: str
        """The SKU for the hardware used to run the model."""

        min_instances: int
        """The minimum number of instances for scaling."""

        max_instances: int
        """The maximum number of instances for scaling."""

    def update(
        self,
        deployment_owner: str,
        deployment_name: str,
        **params: Unpack[UpdateDeploymentParams],
    ) -> Deployment:
        """
        Update an existing deployment.

        Args:
            deployment_owner: The owner of the deployment.
            deployment_name: The name of the deployment.
            params: Configuration updates for the deployment.
        Returns:
            The updated Deployment.
        """

        resp = self._client._request(
            "PATCH",
            f"/v1/deployments/{deployment_owner}/{deployment_name}",
            json=params,
        )

        return _json_to_deployment(self._client, resp.json())

    async def async_update(
        self,
        deployment_owner: str,
        deployment_name: str,
        **params: Unpack[UpdateDeploymentParams],
    ) -> Deployment:
        """
        Update an existing deployment.

        Args:
            deployment_owner: The owner of the deployment.
            deployment_name: The name of the deployment.
            params: Configuration updates for the deployment.
        Returns:
            The updated Deployment.
        """

        resp = await self._client._async_request(
            "PATCH",
            f"/v1/deployments/{deployment_owner}/{deployment_name}",
            json=params,
        )

        return _json_to_deployment(self._client, resp.json())

    def delete(self, deployment_owner: str, deployment_name: str) -> bool:
        """
        Delete an existing deployment.

        Args:
            deployment_owner: The owner of the deployment.
            deployment_name: The name of the deployment.
        """
        resp = self._client._request(
            "DELETE",
            f"/v1/deployments/{deployment_owner}/{deployment_name}",
        )
        return resp.status_code == 204

    async def async_delete(self, deployment_owner: str, deployment_name: str) -> bool:
        """
        Delete an existing deployment asynchronously.

        Args:
            deployment_owner: The owner of the deployment.
            deployment_name: The name of the deployment.
        """
        resp = await self._client._async_request(
            "DELETE",
            f"/v1/deployments/{deployment_owner}/{deployment_name}",
        )
        return resp.status_code == 204

    @property
    def predictions(self) -> "DeploymentsPredictions":
        """
        Get predictions for deployments.
        """

        return DeploymentsPredictions(client=self._client)


def _json_to_deployment(client: "Client", json: Dict[str, Any]) -> Deployment:
    deployment = Deployment(**json)
    deployment._client = client
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

        wait = params.pop("wait", None)
        file_encoding_strategy = params.pop("file_encoding_strategy", None)

        if input is not None:
            input = encode_json(
                input,
                client=self._client,
                file_encoding_strategy=file_encoding_strategy,
            )

        body = _create_prediction_body(version=None, input=input, **params)
        extras = _create_prediction_request_params(
            wait=wait,
        )
        resp = self._client._request(
            "POST",
            f"/v1/deployments/{self._deployment.owner}/{self._deployment.name}/predictions",
            json=body,
            **extras,
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

        wait = params.pop("wait", None)
        file_encoding_strategy = params.pop("file_encoding_strategy", None)
        if input is not None:
            input = await async_encode_json(
                input,
                client=self._client,
                file_encoding_strategy=file_encoding_strategy,
            )

        body = _create_prediction_body(version=None, input=input, **params)
        extras = _create_prediction_request_params(
            wait=wait,
        )
        resp = await self._client._async_request(
            "POST",
            f"/v1/deployments/{self._deployment.owner}/{self._deployment.name}/predictions",
            json=body,
            **extras,
        )

        return _json_to_prediction(self._client, resp.json())


class DeploymentsPredictions(Namespace):
    """
    Namespace for operations related to predictions in deployments.
    """

    def create(
        self,
        deployment: Union[str, Tuple[str, str], Deployment],
        input: Dict[str, Any],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction:
        """
        Create a new prediction with the deployment.
        """

        wait = params.pop("wait", None)
        file_encoding_strategy = params.pop("file_encoding_strategy", None)

        url = _create_prediction_url_from_deployment(deployment)
        if input is not None:
            input = encode_json(
                input,
                client=self._client,
                file_encoding_strategy=file_encoding_strategy,
            )

        body = _create_prediction_body(version=None, input=input, **params)
        extras = _create_prediction_request_params(wait=wait)
        resp = self._client._request("POST", url, json=body, **extras)

        return _json_to_prediction(self._client, resp.json())

    async def async_create(
        self,
        deployment: Union[str, Tuple[str, str], Deployment],
        input: Dict[str, Any],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction:
        """
        Create a new prediction with the deployment.
        """

        wait = params.pop("wait", None)
        file_encoding_strategy = params.pop("file_encoding_strategy", None)

        url = _create_prediction_url_from_deployment(deployment)
        if input is not None:
            input = await async_encode_json(
                input,
                client=self._client,
                file_encoding_strategy=file_encoding_strategy,
            )

        body = _create_prediction_body(version=None, input=input, **params)
        extras = _create_prediction_request_params(wait=wait)
        resp = await self._client._async_request("POST", url, json=body, **extras)

        return _json_to_prediction(self._client, resp.json())


def _create_prediction_url_from_deployment(
    deployment: Union[str, Tuple[str, str], Deployment],
) -> str:
    owner, name = None, None
    if isinstance(deployment, Deployment):
        owner, name = deployment.owner, deployment.name
    elif isinstance(deployment, tuple):
        owner, name = deployment[0], deployment[1]
    elif isinstance(deployment, str):
        owner, name = deployment.split("/", 1)

    if owner is None or name is None:
        raise ValueError(
            "deployment must be a Deployment, a tuple of (owner, name), or a string in the format 'owner/name'"
        )

    return f"/v1/deployments/{owner}/{name}/predictions"
