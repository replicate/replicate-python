import datetime
from typing import TYPE_CHECKING, Any, Dict, Tuple, Union

if TYPE_CHECKING:
    from replicate.client import Client
    from replicate.model import Model

from replicate.pagination import Page
from replicate.resource import Namespace, Resource


class Version(Resource):
    """
    A version of a model.
    """

    id: str
    """The unique ID of the version."""

    created_at: datetime.datetime
    """When the version was created."""

    cog_version: str
    """The version of the Cog used to create the version."""

    openapi_schema: dict
    """An OpenAPI description of the model inputs and outputs."""


class Versions(Namespace):
    """
    Namespace for operations related to model versions.
    """

    model: Tuple[str, str]

    def __init__(
        self, client: "Client", model: Union["Model", str, Tuple[str, str]]
    ) -> None:
        super().__init__(client=client)

        from replicate.model import Model  # pylint: disable=import-outside-toplevel

        if isinstance(model, Model):
            self.model = (model.owner, model.name)
        elif isinstance(model, str):
            owner, name = model.split("/", 1)
            self.model = (owner, name)
        else:
            self.model = model

    def get(self, id: str) -> Version:
        """
        Get a specific model version.

        Args:
            id: The version ID.
        Returns:
            The model version.
        """

        resp = self._client._request(
            "GET", f"/v1/models/{self.model[0]}/{self.model[1]}/versions/{id}"
        )

        return _json_to_version(resp.json())

    async def async_get(self, id: str) -> Version:
        """
        Get a specific model version.

        Args:
            id: The version ID.
        Returns:
            The model version.
        """

        resp = await self._client._async_request(
            "GET", f"/v1/models/{self.model[0]}/{self.model[1]}/versions/{id}"
        )

        return _json_to_version(resp.json())

    def list(self) -> Page[Version]:
        """
        Return a list of all versions for a model.

        Returns:
            List[Version]: A list of version objects.
        """

        resp = self._client._request(
            "GET", f"/v1/models/{self.model[0]}/{self.model[1]}/versions"
        )
        obj = resp.json()
        obj["results"] = [_json_to_version(result) for result in obj["results"]]

        return Page[Version](**obj)

    async def async_list(self) -> Page[Version]:
        """
        Return a list of all versions for a model.

        Returns:
            List[Version]: A list of version objects.
        """

        resp = await self._client._async_request(
            "GET", f"/v1/models/{self.model[0]}/{self.model[1]}/versions"
        )
        obj = resp.json()
        obj["results"] = [_json_to_version(result) for result in obj["results"]]

        return Page[Version](**obj)


def _json_to_version(json: Dict[str, Any]) -> Version:
    return Version(**json)
