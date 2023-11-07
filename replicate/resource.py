import abc
from typing import TYPE_CHECKING, Generic, TypeVar

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore

if TYPE_CHECKING:
    from replicate.client import Client


class Resource(pydantic.BaseModel):
    """
    A base class for representing a single object on the server.
    """


Model = TypeVar("Model", bound=Resource)


class Namespace(abc.ABC, Generic[Model]):
    """
    A base class for representing objects of a particular type on the server.
    """

    _client: "Client"
    model: Model

    def __init__(self, client: "Client") -> None:
        self._client = client
