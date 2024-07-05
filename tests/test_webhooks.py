import httpx
import pytest
import respx
from httpx import Request

from replicate.client import Client
from replicate.webhook import Webhooks, WebhookSigningSecret


@pytest.fixture
def webhook_signing_secret():
    # This is a test secret and should not be used in production
    return WebhookSigningSecret(key="whsec_MfKQ9r8GKYqrTwjUPD8ILPZIo2LaLaSw")


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
@respx.mock
async def test_get_webhook_secret(async_flag, webhook_signing_secret):
    respx.get("https://api.replicate.com/v1/webhooks/default/secret").mock(
        return_value=httpx.Response(200, json={"key": webhook_signing_secret.key})
    )

    client = Client(api_token="test-token")

    if async_flag:
        secret = await client.webhooks.default.async_secret()
    else:
        secret = client.webhooks.default.secret()

    assert isinstance(secret, WebhookSigningSecret)
    assert secret.key == webhook_signing_secret.key

    body = '{"test": 2432232314}'
    headers = {
        "Content-Type": "application/json",
        "Webhook-ID": "msg_p5jXN8AQM9LWM0D4loKWxJek",
        "Webhook-Timestamp": "1614265330",
        "Webhook-Signature": "v1,g0hM9SsE+OTPJTGt/tmIKtSyZlE3uFJELVlNIOLJ1OE=",
    }

    request = Request(
        method="POST",
        url="http://test.host/webhook",
        headers=headers,
        content=body.encode(),
    )

    is_valid = client.webhooks.validate(request=request, secret=secret)
    assert is_valid


def test_validate_webhook_invalid_signature(webhook_signing_secret):
    headers = {
        "Content-Type": "application/json",
        "Webhook-ID": "msg_p5jXN8AQM9LWM0D4loKWxJek",
        "Webhook-Timestamp": "1614265330",
        "Webhook-Signature": "v1,invalid_signature",
    }
    body = '{"test": 2432232314}'

    is_valid = Webhooks.validate(
        headers=headers, body=body, secret=webhook_signing_secret
    )
    assert not is_valid


def test_validate_webhook_missing_webhook_id(webhook_signing_secret):
    headers = {
        "Content-Type": "application/json",
    }
    body = '{"test": 2432232314}'

    with pytest.raises(ValueError, match="Missing webhook id"):
        Webhooks.validate(headers=headers, body=body, secret=webhook_signing_secret)


def test_validate_webhook_invalid_secret():
    headers = {
        "Content-Type": "application/json",
        "Webhook-ID": "msg_p5jXN8AQM9LWM0D4loKWxJek",
        "Webhook-Timestamp": "1614265330",
        "Webhook-Signature": "v1,invalid_signature",
    }
    body = '{"test": 2432232314}'

    with pytest.raises(ValueError, match="Invalid secret key format"):
        Webhooks.validate(
            headers=headers,
            body=body,
            secret=WebhookSigningSecret(key="invalid_secret_format"),
        )


def test_validate_webhook_missing_headers(webhook_signing_secret):
    headers = None
    body = '{"test": 2432232314}'

    with pytest.raises(ValueError, match="Missing webhook headers"):
        Webhooks.validate(
            headers=headers,  # type: ignore
            body=body,
            secret=webhook_signing_secret,
        )


def test_validate_webhook_missing_body(webhook_signing_secret):
    headers = {
        "Content-Type": "application/json",
        "Webhook-ID": "msg_p5jXN8AQM9LWM0D4loKWxJek",
        "Webhook-Timestamp": "1614265330",
        "Webhook-Signature": "v1,g0hM9SsE+OTPJTGt/tmIKtSyZlE3uFJELVlNIOLJ1OE=",
    }
    body = None

    with pytest.raises(ValueError, match="Missing webhook body"):
        Webhooks.validate(
            headers=headers,
            body=body,  # type: ignore
            secret=webhook_signing_secret,
        )
