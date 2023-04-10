import abc
from typing import TYPE_CHECKING, Any, Generic, List, Optional, TypeVar

if TYPE_CHECKING:
    from replicate.client import Client

from replicate.base_model import BaseModel

Model = TypeVar("Model", BaseModel, Any)


class Collection(abc.ABC, Generic[Model]):
    """
    A base class for representing all objects of a particular type on the
    server.
    """

    def __init__(self, client: "Client") -> None:
        self._client = client

    @abc.abstractproperty
    def model(self) -> Model:
        pass

    @abc.abstractmethod
    def list(self) -> List[Model]:
        pass

    @abc.abstractmethod
    def get(self, key: str) -> Model:
        pass

    @abc.abstractmethod
    def create(self, **kwargs) -> Model:
        pass

    def prepare_model(self, attrs: Model | dict) -> Model:
        """
        Create a model from a set of attributes.
        """
        if isinstance(attrs, BaseModel):
            attrs._client = self._client
            attrs._collection = self
            return attrs
        elif isinstance(attrs, dict):
            model = self.model(**attrs)
            model._client = self._client
            model._collection = self
            return model
        else:
            raise Exception(f"Can't create {self.model.__name__} from {attrs}")
