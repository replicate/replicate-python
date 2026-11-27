import datetime
from typing import TYPE_CHECKING, Any, Dict, Tuple, Union
from urllib.parse import urlsplit

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
        self, client: "Client", model: Union[str, Tuple[str, str], "Model"]
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

    def _list_url(self, cursor: Union[str, "ellipsis", None]) -> str:  # noqa: F821
        path = f"/v1/models/{self.model[0]}/{self.model[1]}/versions"
        if cursor is None:
            raise ValueError("cursor cannot be None")
        if cursor is ...:
            return path
        return f"{path}?{urlsplit(cursor).query}"

    def list(self, cursor: Union[str, "ellipsis", None] = ...) -> Page[Version]:  # noqa: F821
        """
        List a page of model versions, optionally using a previous page's next or previous URL.
        """
        resp = self._client._request("GET", self._list_url(cursor))
        obj = resp.json()
        obj["results"] = [_json_to_version(result) for result in obj["results"]]

        return Page[Version](**obj)

    async def async_list(
        self,
        cursor: Union[str, "ellipsis", None] = ...,  # noqa: F821
    ) -> Page[Version]:
        """
        List a page of model versions, optionally using a previous page's next or previous URL.
        """
        resp = await self._client._async_request("GET", self._list_url(cursor))
        obj = resp.json()
        obj["results"] = [_json_to_version(result) for result in obj["results"]]

        return Page[Version](**obj)

    def delete(self, id: str) -> bool:
        """
        Delete a model version and all associated predictions, including all output files.

        Model version deletion has some restrictions:

        * You can only delete versions from models you own.
        * You can only delete versions from private models.
        * You cannot delete a version if someone other than you
          has run predictions with it.

        Args:
            id: The version ID.
        """

        resp = self._client._request(
            "DELETE", f"/v1/models/{self.model[0]}/{self.model[1]}/versions/{id}"
        )
        return resp.status_code == 204

    async def async_delete(self, id: str) -> bool:
        """
        Delete a model version and all associated predictions, including all output files.

        Model version deletion has some restrictions:

        * You can only delete versions from models you own.
        * You can only delete versions from private models.
        * You cannot delete a version if someone other than you
          has run predictions with it.

        Args:
            id: The version ID.
        """

        resp = await self._client._async_request(
            "DELETE", f"/v1/models/{self.model[0]}/{self.model[1]}/versions/{id}"
        )
        return resp.status_code == 204


def _json_to_version(json: Dict[str, Any]) -> Version:
    return Version(**json)
