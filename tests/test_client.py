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
        headers={"Authorization": "Bearer test-set-after-import"},
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


@pytest.mark.asyncio
async def test_client_error_handling():
    import replicate
    from replicate.exceptions import ReplicateError

    router = respx.Router()
    router.route(
        method="GET",
        url="https://api.replicate.com/",
        headers={"Authorization": "Bearer test-client-error"},
    ).mock(
        return_value=httpx.Response(
            400,
            json={"detail": "Client error occurred"},
        )
    )

    token = "test-client-error"  # noqa: S105

    with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": token}):
        client = replicate.Client(transport=httpx.MockTransport(router.handler))
        with pytest.raises(ReplicateError) as exc_info:
            client._request("GET", "/")
        assert "status: 400" in str(exc_info.value)
        assert "detail: Client error occurred" in str(exc_info.value)


@pytest.mark.asyncio
async def test_server_error_handling():
    import replicate
    from replicate.exceptions import ReplicateError

    router = respx.Router()
    router.route(
        method="GET",
        url="https://api.replicate.com/",
        headers={"Authorization": "Bearer test-server-error"},
    ).mock(
        return_value=httpx.Response(
            500,
            json={"detail": "Server error occurred"},
        )
    )

    token = "test-server-error"  # noqa: S105

    with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": token}):
        client = replicate.Client(transport=httpx.MockTransport(router.handler))
        with pytest.raises(ReplicateError) as exc_info:
            client._request("GET", "/")
        assert "status: 500" in str(exc_info.value)
        assert "detail: Server error occurred" in str(exc_info.value)


def test_custom_headers_are_applied():
    import replicate
    from replicate.exceptions import ReplicateError

    custom_headers = {"User-Agent": "my-custom-user-agent/1.0"}

    def mock_send(request):
        assert "User-Agent" in request.headers, "Custom header not found in request"
        assert (
            request.headers["User-Agent"] == "my-custom-user-agent/1.0"
        ), "Custom header value is incorrect"
        return httpx.Response(401, json={})

    mock_send_wrapper = mock.Mock(side_effect=mock_send)

    client = replicate.Client(
        api_token="dummy_token",
        headers=custom_headers,
        transport=httpx.MockTransport(mock_send_wrapper),
    )

    try:
        client.accounts.current()
    except ReplicateError:
        pass

    mock_send_wrapper.assert_called_once()
