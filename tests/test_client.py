import os
import sys
from unittest import mock

import httpx
import pytest
import respx

from replicate.client import _get_api_token_from_environment


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
        assert request.headers["User-Agent"] == "my-custom-user-agent/1.0", (
            "Custom header value is incorrect"
        )
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


class ExperimentalFeatureWarning(Warning): ...


class TestGetApiToken:
    """Test cases for _get_api_token_from_environment function covering all import paths."""

    def test_cog_not_available_falls_back_to_env(self):
        """Test fallback to environment when cog package is not available."""
        with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": "env-token"}):
            with mock.patch.dict(sys.modules, {"cog": None}):
                token = _get_api_token_from_environment()
                assert token == "env-token"  # noqa: S105

    def test_cog_import_error_falls_back_to_env(self):
        """Test fallback to environment when cog import raises exception."""
        with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": "env-token"}):
            with mock.patch(
                "builtins.__import__",
                side_effect=ModuleNotFoundError("No module named 'cog'"),
            ):
                token = _get_api_token_from_environment()
                assert token == "env-token"  # noqa: S105

    def test_cog_no_current_scope_method_falls_back_to_env(self):
        """Test fallback when cog exists but has no current_scope method."""
        mock_cog = mock.MagicMock()
        mock_cog.ExperimentalFeatureWarning = ExperimentalFeatureWarning
        del mock_cog.current_scope  # Remove the method

        with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": "env-token"}):
            with mock.patch.dict(sys.modules, {"cog": mock_cog}):
                token = _get_api_token_from_environment()
                assert token == "env-token"  # noqa: S105

    def test_cog_current_scope_returns_none_falls_back_to_env(self):
        """Test fallback when current_scope() returns None."""
        mock_cog = mock.MagicMock()
        mock_cog.ExperimentalFeatureWarning = ExperimentalFeatureWarning
        mock_cog.current_scope.return_value = None

        with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": "env-token"}):
            with mock.patch.dict(sys.modules, {"cog": mock_cog}):
                token = _get_api_token_from_environment()
                assert token == "env-token"  # noqa: S105

    def test_cog_scope_no_context_attr_falls_back_to_env(self):
        """Test fallback when scope has no context attribute."""
        mock_scope = mock.MagicMock()
        del mock_scope.context  # Remove the context attribute

        mock_cog = mock.MagicMock()
        mock_cog.ExperimentalFeatureWarning = ExperimentalFeatureWarning
        mock_cog.current_scope.return_value = mock_scope

        with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": "env-token"}):
            with mock.patch.dict(sys.modules, {"cog": mock_cog}):
                token = _get_api_token_from_environment()
                assert token == "env-token"  # noqa: S105

    def test_cog_scope_context_not_dict_falls_back_to_env(self):
        """Test fallback when scope.context is not a dictionary."""
        mock_scope = mock.MagicMock()
        mock_scope.context = "not a dict"

        mock_cog = mock.MagicMock()
        mock_cog.ExperimentalFeatureWarning = ExperimentalFeatureWarning
        mock_cog.current_scope.return_value = mock_scope

        with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": "env-token"}):
            with mock.patch.dict(sys.modules, {"cog": mock_cog}):
                token = _get_api_token_from_environment()
                assert token == "env-token"  # noqa: S105

    def test_cog_scope_no_replicate_api_token_key_falls_back_to_env(self):
        """Test fallback when replicate_api_token key is missing from context."""
        mock_scope = mock.MagicMock()
        mock_scope.context = {"other_key": "other_value"}  # Missing replicate_api_token

        mock_cog = mock.MagicMock()
        mock_cog.ExperimentalFeatureWarning = ExperimentalFeatureWarning
        mock_cog.current_scope.return_value = mock_scope

        with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": "env-token"}):
            with mock.patch.dict(sys.modules, {"cog": mock_cog}):
                token = _get_api_token_from_environment()
                assert token == "env-token"  # noqa: S105

    def test_cog_scope_replicate_api_token_valid_string(self):
        """Test successful retrieval of non-empty token from cog."""
        mock_scope = mock.MagicMock()
        mock_scope.context = {"REPLICATE_API_TOKEN": "cog-token"}

        mock_cog = mock.MagicMock()
        mock_cog.ExperimentalFeatureWarning = ExperimentalFeatureWarning
        mock_cog.current_scope.return_value = mock_scope

        with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": "env-token"}):
            with mock.patch.dict(sys.modules, {"cog": mock_cog}):
                token = _get_api_token_from_environment()
                assert token == "cog-token"  # noqa: S105

    def test_cog_scope_replicate_api_token_case_insensitive(self):
        """Test successful retrieval of non-empty token from cog ignoring case."""
        mock_scope = mock.MagicMock()
        mock_scope.context = {"replicate_api_token": "cog-token"}

        mock_cog = mock.MagicMock()
        mock_cog.ExperimentalFeatureWarning = ExperimentalFeatureWarning
        mock_cog.current_scope.return_value = mock_scope

        with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": "env-token"}):
            with mock.patch.dict(sys.modules, {"cog": mock_cog}):
                token = _get_api_token_from_environment()
                assert token == "cog-token"  # noqa: S105

    def test_cog_scope_replicate_api_token_empty_string(self):
        """Test that empty string from cog is returned (not falling back to env)."""
        mock_scope = mock.MagicMock()
        mock_scope.context = {"replicate_api_token": ""}  # Empty string

        mock_cog = mock.MagicMock()
        mock_cog.ExperimentalFeatureWarning = ExperimentalFeatureWarning
        mock_cog.current_scope.return_value = mock_scope

        with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": "env-token"}):
            with mock.patch.dict(sys.modules, {"cog": mock_cog}):
                token = _get_api_token_from_environment()
                assert token == ""  # Should return empty string, not env token

    def test_cog_scope_replicate_api_token_none(self):
        """Test that None from cog is returned (not falling back to env)."""
        mock_scope = mock.MagicMock()
        mock_scope.context = {"replicate_api_token": None}

        mock_cog = mock.MagicMock()
        mock_cog.ExperimentalFeatureWarning = ExperimentalFeatureWarning
        mock_cog.current_scope.return_value = mock_scope

        with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": "env-token"}):
            with mock.patch.dict(sys.modules, {"cog": mock_cog}):
                token = _get_api_token_from_environment()
                assert token is None  # Should return None, not env token

    def test_cog_current_scope_raises_exception_falls_back_to_env(self):
        """Test fallback when current_scope() raises an exception."""
        mock_cog = mock.MagicMock()
        mock_cog.ExperimentalFeatureWarning = ExperimentalFeatureWarning
        mock_cog.current_scope.side_effect = RuntimeError("Scope error")

        with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": "env-token"}):
            with mock.patch.dict(sys.modules, {"cog": mock_cog}):
                token = _get_api_token_from_environment()
                assert token == "env-token"  # noqa: S105

    def test_no_env_token_returns_none(self):
        """Test that None is returned when no environment token is set and cog unavailable."""
        with mock.patch.dict(os.environ, {}, clear=True):  # Clear all env vars
            with mock.patch.dict(sys.modules, {"cog": None}):
                token = _get_api_token_from_environment()
                assert token is None

    def test_env_token_empty_string(self):
        """Test that empty string from environment is returned."""
        with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": ""}):
            with mock.patch.dict(sys.modules, {"cog": None}):
                token = _get_api_token_from_environment()
                assert token == ""
