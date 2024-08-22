import os
from unittest import mock

import pytest

skip_if_no_token = pytest.mark.skipif(
    os.environ.get("REPLICATE_API_TOKEN") is None, reason="REPLICATE_API_TOKEN not set"
)


@pytest.fixture(scope="session")
def mock_replicate_api_token(scope="class"):
    if os.environ.get("REPLICATE_API_TOKEN", "") != "":
        yield
    else:
        with mock.patch.dict(
            os.environ,
            {"REPLICATE_API_TOKEN": "test-token", "REPLICATE_POLL_INTERVAL": "0.0"},
        ):
            yield


@pytest.fixture(scope="module")
def vcr_config():
    return {"allowed_hosts": ["api.replicate.com"], "filter_headers": ["authorization"]}


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    module = request.node.fspath
    return os.path.join(module.dirname, "cassettes")
