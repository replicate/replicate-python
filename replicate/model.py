from typing import List

from replicate.base_model import BaseModel
from replicate.collection import Collection
from replicate.exceptions import ReplicateException
from replicate.version import VersionCollection


class Model(BaseModel):
    username: str
    name: str

    def predict(self, *args, **kwargs):
        raise ReplicateException(
            f"The `model.predict()` method has been removed, because it's unstable: if a new version of the model you're using is pushed and its API has changed, your code may break. Use `version.predict()` instead. See https://github.com/replicate/replicate-python#readme"
        )

    @property
    def versions(self):
        return VersionCollection(client=self._client, model=self)


class ModelCollection(Collection):
    model = Model

    def get(self, name: str) -> Model:
        # TODO: fetch model from server
        # TODO: support permanent IDs
        username, name = name.split("/")
        return self.prepare_model({"username": username, "name": name})
