from typing import Optional

import httpx


class ReplicateException(Exception):
    """A base class for all Replicate exceptions."""


class ModelError(ReplicateException):
    """An error from user's code in a model."""


class ReplicateError(ReplicateException):
    """
    An error from Replicate's API.

    This class represents a problem details response as defined in RFC 7807.
    """

    type: Optional[str]
    """A URI that identifies the error type."""

    title: Optional[str]
    """A short, human-readable summary of the error."""

    status: Optional[int]
    """The HTTP status code."""

    detail: Optional[str]
    """A human-readable explanation specific to this occurrence of the error."""

    instance: Optional[str]
    """A URI that identifies the specific occurrence of the error."""

    def __init__(
        self,
        type: Optional[str] = None,
        title: Optional[str] = None,
        status: Optional[int] = None,
        detail: Optional[str] = None,
        instance: Optional[str] = None,
    ) -> None:
        self.type = type
        self.title = title
        self.status = status
        self.detail = detail
        self.instance = instance

    @classmethod
    def from_response(cls, response: httpx.Response) -> "ReplicateError":
        """Create a ReplicateError from a requests.Response."""
        try:
            data = response.json()
        except ValueError:
            data = {}

        return cls(
            type=data.get("type"),
            title=data.get("title"),
            detail=data.get("detail"),
            status=response.status_code,
            instance=data.get("instance"),
        )

    def to_dict(self) -> dict:
        return {
            key: value
            for key, value in {
                "type": self.type,
                "title": self.title,
                "status": self.status,
                "detail": self.detail,
                "instance": self.instance,
            }.items()
            if value is not None
        }

    def __str__(self) -> str:
        return f"ReplicateError: {self.to_dict()}"
