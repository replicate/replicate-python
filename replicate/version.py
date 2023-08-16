import re
from datetime import datetime
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    pass


from .exceptions import ReplicateError
from .pagination import Page
from .resource import Namespace, Resource


class Version(Resource):
    """A version of a model."""

    id: str
    """The unique ID of the version."""

    created_at: datetime
    """When the version was created."""

    cog_version: str
    """The version of the Cog used to create the version."""

    openapi_schema: dict
    """An OpenAPI description of the model inputs and outputs."""


class VersionIdentifier(NamedTuple):
    """An identifier for a Replicate model at a given version in the form
    `owner/name:version`.
    """

    owner: str
    """The owner of the model"""

    name: str
    """The name of the model"""

    version: str
    """The version of the model"""

    @classmethod
    def from_string(cls, identifier: str) -> "VersionIdentifier":
        """Parse a model identifier in the format into its components.

        Args:
            identifier: The version identifier in the format `owner/name:version`.
        Returns:
            A version identifier object.
        Throws:
            InvalidVersionIdentifierError: If the model identifier is invalid.
        """
        m = re.match(r"^(?P<owner>[^/]+)/(?P<name>[^:]+):(?P<version>.+)$", identifier)
        if not m:
            raise InvalidVersionIdentifierError(
                f"Invalid model identifier: {identifier}. Expected format: owner/name:version"
            )
        return cls(**m.groupdict())


class InvalidVersionIdentifierError(ReplicateError):
    """Raised when an invalid model identifier is provided"""

    pass


class Versions(Namespace):
    model = Version

    def get(self, model_owner: str, model_name: str, version_id: str) -> Version:
        """Get a specific model version.

        Args:
            model_owner: The name of the user or organization that owns the model.
            model_name: The name of the model.
            version_id: The ID of the version.
        Returns:
            The model version.
        """

        resp = self._client.request(
            "GET", f"/models/{model_owner}/{model_name}/versions/{version_id}"
        )

        return Version(**resp.json())

    def list(self, model_owner: str, model_name: str) -> Page[Version]:
        """Return a list of all versions for a model.

        Args:
            model_owner: The name of the user or organization that owns the model.
            model_name: The name of the model.
        Returns:
            A page of model versions.
        """

        resp = self._client.request(
            "GET", f"/models/{model_owner}/{model_name}/versions"
        )

        return Page[Version](**resp.json())


class AsyncVersions(Versions):
    async def get(self, model_owner: str, model_name: str, version_id: str) -> Version:
        resp = await self._client.request(
            "GET", f"/models/{model_owner}/{model_name}/versions/{version_id}"
        )

        return Version(**resp.json())

    async def list(self, model_owner: str, model_name: str) -> Page[Version]:
        resp = await self._client.request(
            "GET", f"/models/{model_owner}/{model_name}/versions"
        )

        return Page[Version](**resp.json())
