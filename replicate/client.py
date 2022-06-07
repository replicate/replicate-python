import os
from json import JSONDecodeError

import requests
from requests.adapters import HTTPAdapter, Retry

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

        # Gracefully retry requests
        # This is primarily for when iterating through predict(), where if an exception is thrown, the client
        # has no way of restarting the iterator.
        # We might just want to enable retry logic for iterators, but for now this is a blunt instrument to
        # make this reliable.
        retries = Retry(
            total=5,
            backoff_factor=2,
            # Only retry on GET so we don't unintionally mutute data
            method_whitelist=["GET"],
            # https://support.cloudflare.com/hc/en-us/articles/115003011431-Troubleshooting-Cloudflare-5XX-errors
            status_forcelist=[500, 502, 503, 504, 520, 521, 522, 523, 524, 526, 527],
        )
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

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
