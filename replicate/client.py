import os
from json import JSONDecodeError

import requests

from replicate.__about__ import __version__
from replicate.exceptions import ReplicateError
from replicate.model import ModelCollection
from replicate.prediction import PredictionCollection


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

    def _request(self, method: str, path: str, **kwargs):
        # from requests.Session
        if method in ["GET", "OPTIONS"]:
            kwargs.setdefault("allow_redirects", True)
        if method in ["HEAD"]:
            kwargs.setdefault("allow_redirects", False)
        kwargs.setdefault("headers", {})
        kwargs["headers"].update(self._headers())
        resp = self.session.request(method, self.base_url + path, **kwargs)
        if 400 <= resp.status_code < 600:
            try:
                raise ReplicateError(resp.json()["detail"])
            except (JSONDecodeError, KeyError):
                pass
            raise ReplicateError(f"HTTP error: {resp.status_code, resp.reason}")
        return resp

    def _headers(self):
        return {
            "Authorization": f"Token {self._api_token()}",
            "User-Agent": f"replicate-python@{__version__}",
        }

    def _api_token(self):
        token = self.api_token
        # Evaluate lazily in case environment variable is set with dotenv, or something
        if token is None:
            token = os.environ.get("REPLICATE_API_TOKEN")
        if not token:
            raise ReplicateError(
                """No API token provided. You need to set the REPLICATE_API_TOKEN environment variable or create a client with `replicate.Client(api_token=...)`.

You can find your API key on https://replicate.com"""
            )
        return token

    @property
    def models(self) -> ModelCollection:
        return ModelCollection(client=self)

    @property
    def predictions(self) -> PredictionCollection:
        return PredictionCollection(client=self)
