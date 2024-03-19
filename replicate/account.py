from typing import Any, Dict, Literal, Optional

from replicate.resource import Namespace, Resource


class Account(Resource):
    """
    A user or organization account on Replicate.
    """

    type: Literal["user", "organization"]
    """The type of account."""

    username: str
    """The username of the account."""

    name: str
    """The name of the account."""

    github_url: Optional[str]
    """The GitHub URL of the account."""


class Accounts(Namespace):
    """
    Namespace for operations related to accounts.
    """

    def current(self) -> Account:
        """
        Get the current account.

        Returns:
            Account: The current account.
        """

        resp = self._client._request("GET", "/v1/account")
        obj = resp.json()

        return _json_to_account(obj)

    async def async_current(self) -> Account:
        """
        Get the current account.

        Returns:
            Account: The current account.
        """

        resp = await self._client._async_request("GET", "/v1/account")
        obj = resp.json()

        return _json_to_account(obj)


def _json_to_account(json: Dict[str, Any]) -> Account:
    return Account(**json)
