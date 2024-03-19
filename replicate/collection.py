from typing import Any, Dict, Iterator, List, Optional, Union, overload

from typing_extensions import deprecated

from replicate.model import Model
from replicate.pagination import Page
from replicate.resource import Namespace, Resource


class Collection(Resource):
    """
    A collection of models on Replicate.
    """

    slug: str
    """The slug used to identify the collection."""

    name: str
    """The name of the collection."""

    description: str
    """A description of the collection."""

    models: Optional[List[Model]] = None
    """The models in the collection."""

    @property
    @deprecated("Use `slug` instead of `id`")
    def id(self) -> str:
        """
        DEPRECATED: Use `slug` instead.
        """
        return self.slug

    def __iter__(self) -> Iterator[Model]:
        if self.models is not None:
            return iter(self.models)
        return iter([])

    @overload
    def __getitem__(self, index: int) -> Optional[Model]: ...

    @overload
    def __getitem__(self, index: slice) -> Optional[List[Model]]: ...

    def __getitem__(
        self, index: Union[int, slice]
    ) -> Union[Optional[Model], Optional[List[Model]]]:
        if self.models is not None:
            return self.models[index]
        return None

    def __len__(self) -> int:
        if self.models is not None:
            return len(self.models)

        return 0


class Collections(Namespace):
    """
    A namespace for operations related to collections of models.
    """

    def list(
        self,
        cursor: Union[str, "ellipsis", None] = ...,  # noqa: F821
    ) -> Page[Collection]:
        """
        List collections of models.

        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Collection]: A page of of model collections.
        Raises:
            ValueError: If `cursor` is `None`.
        """

        if cursor is None:
            raise ValueError("cursor cannot be None")

        resp = self._client._request(
            "GET", "/v1/collections" if cursor is ... else cursor
        )

        obj = resp.json()
        obj["results"] = [_json_to_collection(result) for result in obj["results"]]

        return Page[Collection](**obj)

    async def async_list(
        self,
        cursor: Union[str, "ellipsis", None] = ...,  # noqa: F821
    ) -> Page[Collection]:
        """
        List collections of models.

        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Collection]: A page of of model collections.
        Raises:
            ValueError: If `cursor` is `None`.
        """

        if cursor is None:
            raise ValueError("cursor cannot be None")

        resp = await self._client._async_request(
            "GET", "/v1/collections" if cursor is ... else cursor
        )

        obj = resp.json()
        obj["results"] = [_json_to_collection(result) for result in obj["results"]]

        return Page[Collection](**obj)

    def get(self, slug: str) -> Collection:
        """Get a model by name.

        Args:
            name: The name of the model, in the format `owner/model-name`.
        Returns:
            The model.
        """

        resp = self._client._request("GET", f"/v1/collections/{slug}")

        return _json_to_collection(resp.json())

    async def async_get(self, slug: str) -> Collection:
        """Get a model by name.

        Args:
            name: The name of the model, in the format `owner/model-name`.
        Returns:
            The model.
        """

        resp = await self._client._async_request("GET", f"/v1/collections/{slug}")

        return _json_to_collection(resp.json())


def _json_to_collection(json: Dict[str, Any]) -> Collection:
    return Collection(**json)
