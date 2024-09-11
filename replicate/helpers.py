import base64
import io
import mimetypes
from pathlib import Path
from types import GeneratorType
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from replicate.client import Client
    from replicate.file import FileEncodingStrategy


try:
    import numpy as np  # type: ignore

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# pylint: disable=too-many-return-statements
def encode_json(
    obj: Any,  # noqa: ANN401
    client: "Client",
    file_encoding_strategy: Optional["FileEncodingStrategy"] = None,
) -> Any:  # noqa: ANN401
    """
    Return a JSON-compatible version of the object.
    """

    if isinstance(obj, dict):
        return {
            key: encode_json(value, client, file_encoding_strategy)
            for key, value in obj.items()
        }
    if isinstance(obj, (list, set, frozenset, GeneratorType, tuple)):
        return [encode_json(value, client, file_encoding_strategy) for value in obj]
    if isinstance(obj, Path):
        with obj.open("rb") as file:
            return encode_json(file, client, file_encoding_strategy)
    if isinstance(obj, io.IOBase):
        if file_encoding_strategy == "base64":
            return base64.b64encode(obj.read()).decode("utf-8")
        else:
            return client.files.create(obj).urls["get"]
    if HAS_NUMPY:
        if isinstance(obj, np.integer):  # type: ignore
            return int(obj)
        if isinstance(obj, np.floating):  # type: ignore
            return float(obj)
        if isinstance(obj, np.ndarray):  # type: ignore
            return obj.tolist()
    return obj


async def async_encode_json(
    obj: Any,  # noqa: ANN401
    client: "Client",
    file_encoding_strategy: Optional["FileEncodingStrategy"] = None,
) -> Any:  # noqa: ANN401
    """
    Asynchronously return a JSON-compatible version of the object.
    """

    if isinstance(obj, dict):
        return {
            key: (await async_encode_json(value, client, file_encoding_strategy))
            for key, value in obj.items()
        }
    if isinstance(obj, (list, set, frozenset, GeneratorType, tuple)):
        return [
            (await async_encode_json(value, client, file_encoding_strategy))
            for value in obj
        ]
    if isinstance(obj, Path):
        with obj.open("rb") as file:
            return encode_json(file, client, file_encoding_strategy)
    if isinstance(obj, io.IOBase):
        return (await client.files.async_create(obj)).urls["get"]
    if HAS_NUMPY:
        if isinstance(obj, np.integer):  # type: ignore
            return int(obj)
        if isinstance(obj, np.floating):  # type: ignore
            return float(obj)
        if isinstance(obj, np.ndarray):  # type: ignore
            return obj.tolist()
    return obj


def base64_encode_file(file: io.IOBase) -> str:
    """
    Base64 encode a file.

    Args:
        file: A file handle to upload.
    Returns:
        str: A base64-encoded data URI.
    """

    file.seek(0)
    body = file.read()

    # Ensure the file handle is in bytes
    body = body.encode("utf-8") if isinstance(body, str) else body
    encoded_body = base64.b64encode(body).decode("utf-8")

    mime_type = (
        mimetypes.guess_type(getattr(file, "name", ""))[0] or "application/octet-stream"
    )
    return f"data:{mime_type};base64,{encoded_body}"
