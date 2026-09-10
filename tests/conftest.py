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


@pytest.fixture(autouse=True)
def _vcr_httpx2(vcr):
    """Patch httpx2 clients with VCR send-stubs while a cassette is active.

    pytest-recording/vcrpy only patch httpx (0.x); after the migration the
    SDK uses httpx2, so mirror the same patching for httpx2 clients.
    """
    if vcr is None:
        yield
        return

    import httpx2

    from tests._vcr_httpx2_stubs import async_vcr_send, sync_vcr_send

    sync_send = httpx2.Client._send_single_request
    async_send = httpx2.AsyncClient._send_single_request
    httpx2.Client._send_single_request = sync_vcr_send(vcr, sync_send)
    httpx2.AsyncClient._send_single_request = async_vcr_send(vcr, async_send)
    try:
        yield
    finally:
        httpx2.Client._send_single_request = sync_send
        httpx2.AsyncClient._send_single_request = async_send
