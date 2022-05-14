import os
import requests

from replicate.model import ModelCollection
from replicate.prediction import PredictionCollection
from replicate.version import VersionCollection


class Client:
    def __init__(self, api_token=None) -> None:
        super().__init__()
        self.api_token = api_token
        if self.api_token is None:
            self.api_token = os.environ.get("REPLICATE_API_TOKEN")

        self.base_url = "https://api.replicate.com"

        # TODO: make thread safe
        self.session = requests.Session()

    def _get(self, path: str, **kwargs):
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"].update(self._headers())
        return self.session.get(self.base_url + path, **kwargs)

    def _post(self, path: str, **kwargs):
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"].update(self._headers())
        return self.session.post(self.base_url + path, **kwargs)

    def _headers(self):
        return {"Authorization": f"Token {self.api_token}"}

    @property
    def models(self) -> ModelCollection:
        return ModelCollection(client=self)

    @property
    def predictions(self) -> PredictionCollection:
        return PredictionCollection(client=self)

    @property
    def versions(self) -> VersionCollection:
        return VersionCollection(client=self)
