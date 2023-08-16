from abc import ABC
from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from replicate.client import Client


Resource = BaseModel


T = TypeVar("T", bound=Resource)


class Namespace(ABC, Generic[T]):
    """
    A base class for representing objects of a particular type on the server.
    """

    _client: "Client"
    model: T

    def __init__(self, client: "Client") -> None:
        self._client = client
