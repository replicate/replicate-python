import os
import re
from json import JSONDecodeError
from typing import Any, Dict, Iterator, Optional, Union

import requests
from requests.adapters import HTTPAdapter, Retry
from requests.cookies import RequestsCookieJar

from replicate.__about__ import __version__
from replicate.exceptions import ModelError, ReplicateError
from replicate.model import ModelCollection
from replicate.prediction import PredictionCollection
from replicate.training import TrainingCollection


class Client:
    def __init__(self, api_token: Optional[str] = None) -> None:
        super().__init__()
        # Client is instantiated at import time, so do as little as possible.
        # This includes resolving environment variables -- they might be set programmatically.
        self.api_token = api_token
        self.base_url = os.environ.get(
            "REPLICATE_API_BASE_URL", "https://api.replicate.com"
        )
        self.poll_interval = float(os.environ.get("REPLICATE_POLL_INTERVAL", "0.5"))

        # TODO: make thread safe
        self.read_session = _create_session()
        read_retries = Retry(
            total=5,
            backoff_factor=2,
            # Only retry 500s on GET so we don't unintionally mutute data
            allowed_methods=["GET"],
            # https://support.cloudflare.com/hc/en-us/articles/115003011431-Troubleshooting-Cloudflare-5XX-errors
            status_forcelist=[
                429,
                500,
                502,
                503,
                504,
                520,
                521,
                522,
                523,
                524,
                526,
                527,
            ],
        )
        self.read_session.mount("http://", HTTPAdapter(max_retries=read_retries))
        self.read_session.mount("https://", HTTPAdapter(max_retries=read_retries))

        self.write_session = _create_session()
        write_retries = Retry(
            total=5,
            backoff_factor=2,
            allowed_methods=["POST", "PUT"],
            # Only retry POST/PUT requests on rate limits, so we don't unintionally mutute data
            status_forcelist=[429],
        )
        self.write_session.mount("http://", HTTPAdapter(max_retries=write_retries))
        self.write_session.mount("https://", HTTPAdapter(max_retries=write_retries))

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        # from requests.Session
        if method in ["GET", "OPTIONS"]:
            kwargs.setdefault("allow_redirects", True)
        if method in ["HEAD"]:
            kwargs.setdefault("allow_redirects", False)
        kwargs.setdefault("headers", {})
        kwargs["headers"].update(self._headers())
        session = self.read_session
        if method in ["POST", "PUT", "DELETE", "PATCH"]:
            session = self.write_session
        resp = session.request(method, self.base_url + path, **kwargs)
        if 400 <= resp.status_code < 600:
            try:
                raise ReplicateError(resp.json()["detail"])
            except (JSONDecodeError, KeyError):
                pass
            raise ReplicateError(f"HTTP error: {resp.status_code, resp.reason}")
        return resp

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Token {self._api_token()}",
            "User-Agent": f"replicate-python/{__version__}",
        }

    def _api_token(self) -> str:
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

    @property
    def trainings(self) -> TrainingCollection:
        return TrainingCollection(client=self)

    def run(self, model_version: str, **kwargs) -> Union[Any, Iterator[Any]]:
        """
        Run a model in the format owner/name:version.
        """
        # Split model_version into owner, name, version in format owner/name:version
        m = re.match(r"^(?P<model>[^/]+/[^:]+):(?P<version>.+)$", model_version)
        if not m:
            raise ReplicateError(
                f"Invalid model_version: {model_version}. Expected format: owner/name:version"
            )
        model = self.models.get(m.group("model"))
        version = model.versions.get(m.group("version"))
        prediction = self.predictions.create(version=version, **kwargs)
        # Return an iterator of the output
        schema = version.get_transformed_schema()
        output = schema["components"]["schemas"]["Output"]
        if (
            output.get("type") == "array"
            and output.get("x-cog-array-type") == "iterator"
        ):
            return prediction.output_iterator()

        prediction.wait()
        if prediction.status == "failed":
            raise ModelError(prediction.error)
        return prediction.output


class _NonpersistentCookieJar(RequestsCookieJar):
    """
    A cookie jar that doesn't persist cookies between requests.
    """

    def set(self, name, value, **kwargs) -> None:
        return

    def set_cookie(self, cookie, *args, **kwargs) -> None:
        return


def _create_session() -> requests.Session:
    s = requests.Session()
    s.cookies = _NonpersistentCookieJar()
    return s
