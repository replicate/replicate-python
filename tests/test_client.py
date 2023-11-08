import os
from unittest import mock

import httpx
import pytest
import respx


@pytest.mark.asyncio
async def test_authorization_when_setting_environ_after_import():
    import replicate

    router = respx.Router()
    router.route(
        method="GET",
        url="https://api.replicate.com/",
        headers={"Authorization": "Token test-set-after-import"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={},
        )
    )

    token = "test-set-after-import"  # noqa: S105

    with mock.patch.dict(
        os.environ,
        {"REPLICATE_API_TOKEN": token},
    ):
        client = replicate.Client(transport=httpx.MockTransport(router.handler))
        resp = client._request("GET", "/")
        assert resp.status_code == 200
