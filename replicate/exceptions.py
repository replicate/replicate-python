from typing import TYPE_CHECKING, Optional

import httpx

if TYPE_CHECKING:
    from replicate.prediction import Prediction


class ReplicateException(Exception):
    """A base class for all Replicate exceptions."""


class ModelError(ReplicateException):
    """An error from user's code in a model."""

    prediction: "Prediction"

    def __init__(self, prediction: "Prediction") -> None:
        self.prediction = prediction
        super().__init__(prediction.error)


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

    def __init__(  # pylint: disable=too-many-arguments
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
        """Create a ReplicateError from an HTTP response."""

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
        """Get a dictionary representation of the error."""

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
        return "ReplicateError Details:\n" + "\n".join(
            [f"{key}: {value}" for key, value in self.to_dict().items()]
        )

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        params = ", ".join(
            [
                f"type={repr(self.type)}",
                f"title={repr(self.title)}",
                f"status={repr(self.status)}",
                f"detail={repr(self.detail)}",
                f"instance={repr(self.instance)}",
            ]
        )
        return f"{class_name}({params})"
