import abc
from typing import TYPE_CHECKING, Dict, Generic, TypeVar, Union, cast

from replicate.exceptions import ReplicateException

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

    id: str

    _client: "Client" = pydantic.PrivateAttr()
    _namespace: "Namespace" = pydantic.PrivateAttr()


Model = TypeVar("Model", bound=Resource)


class Namespace(abc.ABC, Generic[Model]):
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
        if isinstance(attrs, Resource):
            attrs._client = self._client
            attrs._namespace = self
            return cast(Model, attrs)

        if isinstance(attrs, dict) and self.model is not None and callable(self.model):
            model = self.model(**attrs)
            model._client = self._client
            model._namespace = self
            return model

        name = self.model.__name__ if hasattr(self.model, "__name__") else "model"
        raise ReplicateException(f"Can't create {name} from {attrs}")
