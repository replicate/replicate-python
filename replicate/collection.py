from typing import Optional

from replicate.resource import Namespace, Resource

from .model import Model
from .pagination import Page


class Collection(Resource):
    """"""

    slug: str

    name: str

    description: str

    models: Optional[list[Model]] = None


class Collections(Namespace):
    model = Collection

    def list(self) -> Page[Collection]:
        """List all models."""

        resp = self._client.request("GET", "/collections")

        return Page[Collection](**resp.json())

    def get(self, slug: str) -> Model:
        """Get a model by name.

        Args:
            name: The name of the model, in the format `owner/model-name`.
        Returns:
            The model.
        """

        resp = self._client.request("GET", f"/collections/{slug}")

        return Collection(**resp.json())


class AsyncCollections(Collections):
    async def list(self) -> Page[Collection]:
        resp = await self._client.request("GET", "/collections")

        return Page[Collection](**resp.json())

    async def get(self, slug: str) -> Collection:
        resp = await self._client.request("GET", f"/collections/{slug}")

        return Collection(**resp.json())
