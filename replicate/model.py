from typing import Dict, List, Union

from replicate.base_model import BaseModel
from replicate.collection import Collection
from replicate.exceptions import ReplicateException
from replicate.version import VersionCollection


class Model(BaseModel):
    """
    A machine learning model hosted on Replicate.
    """

    username: str
    """
    The name of the user or organization that owns the model.
    """

    name: str
    """
    The name of the model.
    """

    def predict(self, *args, **kwargs) -> None:
        """
        DEPRECATED: Use `replicate.run()` instead.
        """

        raise ReplicateException(
            "The `model.predict()` method has been removed, because it's unstable: if a new version of the model you're using is pushed and its API has changed, your code may break. Use `replicate.run()` instead. See https://github.com/replicate/replicate-python#readme"
        )

    @property
    def versions(self) -> VersionCollection:
        """
        Get the versions of this model.
        """

        return VersionCollection(client=self._client, model=self)


class ModelCollection(Collection):
    model = Model

    def list(self) -> List[Model]:
        raise NotImplementedError()

    def get(self, name: str) -> Model:
        """
        Get a model by name.

        Args:
            name: The name of the model, in the format `owner/model-name`.
        Returns:
            The model.
        """

        # TODO: fetch model from server
        # TODO: support permanent IDs
        username, name = name.split("/")
        return self.prepare_model({"username": username, "name": name})

    def create(self, **kwargs) -> Model:
        raise NotImplementedError()

    def prepare_model(self, attrs: Union[Model, Dict]) -> Model:
        if isinstance(attrs, BaseModel):
            attrs.id = f"{attrs.username}/{attrs.name}"
        elif isinstance(attrs, dict):
            attrs["id"] = f"{attrs['username']}/{attrs['name']}"
        return super().prepare_model(attrs)
