import base64
import io
import json
import mimetypes
import os
import pathlib
from typing import Any, BinaryIO, Dict, List, Optional, TypedDict, Union

import httpx
from typing_extensions import NotRequired, Unpack

from replicate.resource import Namespace, Resource


class File(Resource):
    """
    A file uploaded to Replicate that can be used as an input to a model.
    """

    id: str
    """The ID of the file."""

    name: str
    """The name of the file."""

    content_type: str
    """The content type of the file."""

    size: int
    """The size of the file in bytes."""

    etag: str
    """The ETag of the file."""

    checksums: Dict[str, str]
    """The checksums of the file."""

    metadata: Dict[str, Any]
    """The metadata of the file."""

    created_at: str
    """The time the file was created."""

    expires_at: Optional[str]
    """The time the file will expire."""

    urls: Dict[str, str]
    """The URLs of the file."""


class Files(Namespace):
    class CreateFileParams(TypedDict):
        """Parameters for creating a file."""

        filename: NotRequired[str]
        """The name of the file."""

        content_type: NotRequired[str]
        """The content type of the file."""

        metadata: NotRequired[Dict[str, Any]]
        """The file metadata."""

    def create(
        self,
        file: Union[str, pathlib.Path, BinaryIO, io.IOBase],
        **params: Unpack["Files.CreateFileParams"],
    ) -> File:
        """
        Upload a file that can be passed as an input when running a model.
        """

        if isinstance(file, (str, pathlib.Path)):
            with open(file, "rb") as f:
                return self.create(f, **params)
        elif not isinstance(file, (io.IOBase, BinaryIO)):
            raise ValueError(
                "Unsupported file type. Must be a file path or file-like object."
            )

        resp = self._client._request(
            "POST", "/v1/files", timeout=None, **_create_file_params(file, **params)
        )

        return _json_to_file(resp.json())

    async def async_create(
        self,
        file: Union[str, pathlib.Path, BinaryIO, io.IOBase],
        **params: Unpack["Files.CreateFileParams"],
    ) -> File:
        """Upload a file asynchronously that can be passed as an input when running a model."""

        if isinstance(file, (str, pathlib.Path)):
            with open(file, "rb") as f:
                return self.create(f, **params)
        elif not isinstance(file, (io.IOBase, BinaryIO)):
            raise ValueError(
                "Unsupported file type. Must be a file path or file-like object."
            )

        resp = await self._client._async_request(
            "POST", "/v1/files", timeout=None, **_create_file_params(file, **params)
        )

        return _json_to_file(resp.json())

    def get(self, file_id: str) -> File:
        """Get an uploaded file by its ID."""

        resp = self._client._request("GET", f"/v1/files/{file_id}")
        return _json_to_file(resp.json())

    async def async_get(self, file_id: str) -> File:
        """Get an uploaded file by its ID asynchronously."""

        resp = await self._client._async_request("GET", f"/v1/files/{file_id}")
        return _json_to_file(resp.json())

    def list(self) -> List[File]:
        """List all uploaded files."""

        resp = self._client._request("GET", "/v1/files")
        return [_json_to_file(obj) for obj in resp.json().get("results", [])]

    async def async_list(self) -> List[File]:
        """List all uploaded files asynchronously."""

        resp = await self._client._async_request("GET", "/v1/files")
        return [_json_to_file(obj) for obj in resp.json().get("results", [])]

    def delete(self, file_id: str) -> None:
        """Delete an uploaded file by its ID."""

        _ = self._client._request("DELETE", f"/v1/files/{file_id}")

    async def async_delete(self, file_id: str) -> None:
        """Delete an uploaded file by its ID asynchronously."""

        _ = await self._client._async_request("DELETE", f"/v1/files/{file_id}")


def _create_file_params(
    file: Union[BinaryIO, io.IOBase],
    **params: Unpack["Files.CreateFileParams"],
) -> Dict[str, Any]:
    file.seek(0)

    if params is None:
        params = {}

    filename = params.get("filename", os.path.basename(getattr(file, "name", "file")))
    content_type = (
        params.get("content_type")
        or mimetypes.guess_type(filename)[0]
        or "application/octet-stream"
    )
    metadata = params.get("metadata")

    data = {}
    if metadata:
        data["metadata"] = json.dumps(metadata)

    return {
        "files": {"content": (filename, file, content_type)},
        "data": data,
    }


def _json_to_file(json: Dict[str, Any]) -> File:  # pylint: disable=redefined-outer-name
    return File(**json)


def upload_file(file: io.IOBase, output_file_prefix: Optional[str] = None) -> str:
    """
    Upload a file to the server.

    Args:
        file: A file handle to upload.
        output_file_prefix: A string to prepend to the output file name.
    Returns:
        str: A URL to the uploaded file.
    """
    # Lifted straight from cog.files

    file.seek(0)

    if output_file_prefix is not None:
        name = getattr(file, "name", "output")
        url = output_file_prefix + os.path.basename(name)
        resp = httpx.put(url, files={"file": file}, timeout=None)  # type: ignore
        resp.raise_for_status()

        return url

    body = file.read()
    # Ensure the file handle is in bytes
    body = body.encode("utf-8") if isinstance(body, str) else body
    encoded_body = base64.b64encode(body).decode("utf-8")
    # Use getattr to avoid mypy complaints about io.IOBase having no attribute name
    mime_type = (
        mimetypes.guess_type(getattr(file, "name", ""))[0] or "application/octet-stream"
    )
    return f"data:{mime_type};base64,{encoded_body}"
