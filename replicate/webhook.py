import base64
import hmac
from hashlib import sha256
from typing import (
    TYPE_CHECKING,
    Dict,
    Optional,
    overload,
)

from replicate.resource import Namespace, Resource

if TYPE_CHECKING:
    import httpx


class WebhookSigningSecret(Resource):
    """
    A webhook signing secret.
    """

    key: str


class WebhookValidationError(ValueError):
    """Base exception for webhook validation errors."""


class MissingWebhookHeaderError(WebhookValidationError):
    """Exception raised when a required webhook header is missing."""


class InvalidSecretKeyError(WebhookValidationError):
    """Exception raised when the secret key format is invalid."""


class MissingWebhookBodyError(WebhookValidationError):
    """Exception raised when the webhook body is missing."""


class InvalidTimestampError(WebhookValidationError):
    """Exception raised when the webhook timestamp is invalid or outside the tolerance."""


class InvalidSignatureError(WebhookValidationError):
    """Exception raised when the webhook signature is invalid."""


class Webhooks(Namespace):
    """
    Namespace for operations related to webhooks.
    """

    @property
    def default(self) -> "Webhooks.Default":
        """
        Namespace for operations related to the default webhook.
        """

        return self.Default(self._client)

    class Default(Namespace):
        """
        Namespace for operations related to the default webhook.
        """

        def secret(self) -> WebhookSigningSecret:
            """
            Get the default webhook signing secret.

            Returns:
                WebhookSigningSecret: The default webhook signing secret.
            """

            resp = self._client._request("GET", "/v1/webhooks/default/secret")
            return WebhookSigningSecret(**resp.json())

        async def async_secret(self) -> WebhookSigningSecret:
            """
            Get the default webhook signing secret.

            Returns:
                WebhookSigningSecret: The default webhook signing secret.
            """

            resp = await self._client._async_request(
                "GET", "/v1/webhooks/default/secret"
            )
            return WebhookSigningSecret(**resp.json())

    @overload
    @staticmethod
    def validate(
        request: "httpx.Request",
        secret: WebhookSigningSecret,
        tolerance: Optional[int] = None,
    ) -> bool: ...

    @overload
    @staticmethod
    def validate(
        headers: Dict[str, str],
        body: str,
        secret: WebhookSigningSecret,
        tolerance: Optional[int] = None,
    ) -> bool: ...

    @staticmethod
    def validate(  # type: ignore # pylint: disable=too-many-branches,too-many-locals
        request: Optional["httpx.Request"] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        secret: Optional[WebhookSigningSecret] = None,
        tolerance: Optional[int] = None,
    ) -> None:
        """
        Validate the signature from an incoming webhook request using the provided secret.

        Args:
            request (httpx.Request): The request object.
            headers (Dict[str, str]): The request headers.
            body (str): The request body.
            secret (WebhookSigningSecret): The webhook signing secret.
            tolerance (Optional[int]): Maximum allowed time difference (in seconds) between the current time and the webhook timestamp.

        Returns:
            None: If the request is valid.

        Raises:
            MissingWebhookHeaderError: If required webhook headers are missing.
            InvalidSecretKeyError: If the secret key format is invalid.
            MissingWebhookBodyError: If the webhook body is missing.
            InvalidTimestampError: If the webhook timestamp is invalid or outside the tolerance.
            InvalidSignatureError: If the webhook signature is invalid.
        """

        if not secret:
            raise ValueError("Missing webhook signing secret")

        if request and any([headers, body]):
            raise ValueError("Only one of request or headers/body can be provided")

        if request and request.headers:
            webhook_id = request.headers.get("webhook-id")
            timestamp = request.headers.get("webhook-timestamp")
            signature = request.headers.get("webhook-signature")
            body = request.content.decode("utf-8")
        else:
            if not headers:
                raise MissingWebhookHeaderError("Missing webhook headers")

            # Convert headers to case-insensitive dictionary
            headers = {k.lower(): v for k, v in headers.items()}

            webhook_id = headers.get("webhook-id")
            timestamp = headers.get("webhook-timestamp")
            signature = headers.get("webhook-signature")

        if not webhook_id:
            raise MissingWebhookHeaderError("Missing webhook id")
        if not timestamp:
            raise MissingWebhookHeaderError("Missing webhook timestamp")
        if not signature:
            raise MissingWebhookHeaderError("Missing webhook signature")
        if not body:
            raise MissingWebhookBodyError("Missing webhook body")

        if tolerance is not None:
            import time  # pylint: disable=import-outside-toplevel

            current_time = int(time.time())
            webhook_time = int(timestamp)
            time_difference = abs(current_time - webhook_time)
            if time_difference > tolerance:
                raise InvalidTimestampError(
                    f"Webhook timestamp is outside the allowed tolerance of {tolerance} seconds"
                )

        signed_content = f"{webhook_id}.{timestamp}.{body}"

        key_parts = secret.key.split("_")
        if len(key_parts) != 2:
            raise InvalidSecretKeyError(f"Invalid secret key format: {secret.key}")

        secret_bytes = base64.b64decode(key_parts[1])

        h = hmac.new(secret_bytes, signed_content.encode(), sha256)
        computed_signature = h.digest()

        valid = False
        for sig in signature.split():
            sig_parts = sig.split(",")
            if len(sig_parts) < 2:
                raise InvalidSignatureError(f"Invalid signature format: {sig}")

            sig_bytes = base64.b64decode(sig_parts[1])

            if hmac.compare_digest(sig_bytes, computed_signature):
                valid = True
                break

        if not valid:
            raise InvalidSignatureError("Webhook signature is invalid")
