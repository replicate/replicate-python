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
    key: str


class Webhooks(Namespace):
    @property
    def default(self) -> "Webhooks.Default":
        """
        Namespace for operations related to the default webhook.
        """

        return self.Default(self._client)

    class Default(Namespace):
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
    def validate(request: "httpx.Request", secret: WebhookSigningSecret) -> bool: ...

    @overload
    @staticmethod
    def validate(
        headers: Dict[str, str], body: str, secret: WebhookSigningSecret
    ) -> bool: ...

    @staticmethod
    def validate(  # type: ignore
        request: Optional["httpx.Request"] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        secret: Optional[WebhookSigningSecret] = None,
    ) -> bool:
        """
        Validate the signature from an incoming webhook request using the provided secret.

        Args:
            request (httpx.Request): The request object.
            headers (Dict[str, str]): The request headers.
            body (str): The request body.
            secret (WebhookSigningSecret): The webhook signing secret.

        Returns:
            bool: True if the request is valid, False otherwise.

        Raises:
            ValueError: If there are missing headers, invalid secret key format, or missing body.
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
                raise ValueError("Missing webhook headers")

            # Convert headers to case-insensitive dictionary
            headers = {k.lower(): v for k, v in headers.items()}

            webhook_id = headers.get("webhook-id")
            timestamp = headers.get("webhook-timestamp")
            signature = headers.get("webhook-signature")

        if not webhook_id:
            raise ValueError("Missing webhook id")
        if not timestamp:
            raise ValueError("Missing webhook timestamp")
        if not signature:
            raise ValueError("Missing webhook signature")
        if not body:
            raise ValueError("Missing webhook body")

        signed_content = f"{webhook_id}.{timestamp}.{body}"

        key_parts = secret.key.split("_")
        if len(key_parts) != 2:
            raise ValueError(f"Invalid secret key format: {secret.key}")

        secret_bytes = base64.b64decode(key_parts[1])

        h = hmac.new(secret_bytes, signed_content.encode(), sha256)
        computed_signature = h.digest()

        for sig in signature.split():
            sig_parts = sig.split(",")
            if len(sig_parts) < 2:
                raise ValueError(f"Invalid signature format: {sig}")

            sig_bytes = base64.b64decode(sig_parts[1])

            if hmac.compare_digest(sig_bytes, computed_signature):
                return True

        return False
