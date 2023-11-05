import abc
from typing import TYPE_CHECKING, Dict, Generic, TypeVar, Union, cast

if TYPE_CHECKING:
    from replicate.client import Client

from replicate.base_model import BaseModel
from replicate.exceptions import ReplicateException

Model = TypeVar("Model", bound=BaseModel)


class Collection(abc.ABC, Generic[Model]):
    """
    A base class for representing objects of a particular type on the server.
    """

    _client: "Client"
    model: Model

    def __init__(self, client: "Client") -> None:
        self._client = client

    def _prepare_model(self, attrs: Union[Model, Dict]) -> Model:
        """
        Create a model from a set of attributes.
        """
        if isinstance(attrs, BaseModel):
            attrs._client = self._client
            attrs._collection = self
            return cast(Model, attrs)

        if isinstance(attrs, dict) and self.model is not None and callable(self.model):
            model = self.model(**attrs)
            model._client = self._client
            model._collection = self
            return model

        name = self.model.__name__ if hasattr(self.model, "__name__") else "model"
        raise ReplicateException(f"Can't create {name} from {attrs}")
