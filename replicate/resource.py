from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from replicate.client import Client
    from replicate.collection import Collection

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore


class Resource(pydantic.BaseModel):
    """
    A base class for representing a single object on the server.
    """

    id: str

    _client: "Client" = pydantic.PrivateAttr()
    _collection: "Collection" = pydantic.PrivateAttr()