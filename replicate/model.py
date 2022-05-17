from typing import List

from replicate.base_model import BaseModel
from replicate.collection import Collection
from replicate.exceptions import ReplicateException
from replicate.version import VersionCollection


class Model(BaseModel):
    username: str
    name: str

    def predict(self, *args, **kwargs):
        versions = self.versions.list()
        if not versions:
            raise ReplicateException(
                "No versions found for model %s/%s" % (self.username, self.name)
            )
        latest_version = versions[0]
        return latest_version.predict(*args, **kwargs)

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
