import os

import requests

from replicate.__about__ import __version__
from replicate.model import ModelCollection
from replicate.prediction import PredictionCollection
from replicate.version import VersionCollection


class Client:
    def __init__(self, api_token=None) -> None:
        super().__init__()
        # Client is instantiated at import time, so do as little as possible.
        # This includes resolving environment variables -- they might be set programmatically.
        self.api_token = api_token
        self.base_url = os.environ.get(
            "REPLICATE_API_BASE_URL", "https://api.replicate.com"
        )

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
        return {
            "Authorization": f"Token {self._api_token()}",
            "User-Agent": f"replicate-python@{__version__}",
        }

    def _api_token(self):
        # Evaluate lazily in case environment variable is set with dotenv, or something
        if self.api_token is None:
            return os.environ.get("REPLICATE_API_TOKEN")
        return self.api_token

    @property
    def models(self) -> ModelCollection:
        return ModelCollection(client=self)

    @property
    def predictions(self) -> PredictionCollection:
        return PredictionCollection(client=self)
