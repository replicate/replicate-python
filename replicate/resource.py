import abc
from typing import TYPE_CHECKING

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore

if TYPE_CHECKING:
    from replicate.client import Client


class Resource(pydantic.BaseModel):  # type: ignore
    """
    A base class for representing a single object on the server.
    """


class Namespace(abc.ABC):
    """
    A base class for representing objects of a particular type on the server.
    """

    _client: "Client"

    def __init__(self, client: "Client") -> None:
        self._client = client
