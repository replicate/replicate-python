from json import JSONDecodeError

import httpx


class ReplicateException(Exception):
    pass


class ModelError(ReplicateException):
    """An error from user's code in a model."""


class ReplicateError(ReplicateException):
    """An error from Replicate."""


class APIError(ReplicateError):
    """An error from the Replicate API."""

    status: int

    detail: str

    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        self.detail = detail

        super().__init__(f"HTTP {status}: {detail}")

    @classmethod
    def from_response(cls, resp: httpx.Response) -> "APIError":
        try:
            return APIError(**resp.json())
        except (JSONDecodeError, KeyError):
            pass
        return APIError(status=resp.status_code, detail=resp.text)
