import os
from unittest import mock

import httpx
import pytest


@pytest.mark.asyncio
async def test_authorization_when_setting_environ_after_import():
    import replicate

    token = "test-set-after-import"  # noqa: S105

    with mock.patch.dict(
        os.environ,
        {"REPLICATE_API_TOKEN": token},
    ):
        client: httpx.Client = replicate.default_client._client
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == f"Token {token}"
