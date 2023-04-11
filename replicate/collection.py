import abc
from typing import TYPE_CHECKING, Dict, Generic, List, TypeVar, Union, cast

if TYPE_CHECKING:
    from replicate.client import Client

from replicate.base_model import BaseModel

Model = TypeVar("Model", bound=BaseModel)


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

    def prepare_model(self, attrs: Union[Model, Dict]) -> Model:
        """
        Create a model from a set of attributes.
        """
        if isinstance(attrs, BaseModel):
            attrs._client = self._client
            attrs._collection = self
            return cast(Model, attrs)
        elif (
            isinstance(attrs, dict) and self.model is not None and callable(self.model)
        ):
            model = self.model(**attrs)
            model._client = self._client
            model._collection = self
            return model
        else:
            name = self.model.__name__ if hasattr(self.model, "__name__") else "model"
            raise Exception(f"Can't create {name} from {attrs}")
