import base64
import io
import mimetypes
import os
from typing import Any, Dict, List, Optional, Tuple

import httpx

from replicate.resource import Namespace, Resource


class File(Resource):
    """A file on the server."""

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

    checksum: str
    """The checksum of the file."""

    metadata: Dict[str, Any]
    """The metadata of the file."""

    created_at: str
    """The time the file was created."""

    expires_at: Optional[str]
    """The time the file will expire."""

    urls: Dict[str, str]
    """The URLs of the file."""


class Files(Namespace):
    def create(
        self, file: io.IOBase, metadata: Optional[Dict[str, Any]] = None
    ) -> File:
        """Create a file on the server."""

        file.seek(0)

        resp = self._client._request(
            "POST",
            "/files",
            data={
                "content": _file_content(file),
                "metadata": metadata,
            },
            timeout=None,
        )

        return _json_to_file(resp.json())

    async def async_create(
        self, file: io.IOBase, metadata: Optional[Dict[str, Any]] = None
    ) -> File:
        """Create a file on the server."""

        file.seek(0)

        resp = await self._client._async_request(
            "POST",
            "/files",
            data={
                "content": _file_content(file),
                "metadata": metadata,
            },
            timeout=None,
        )

        return _json_to_file(resp.json())

    def get(self, file_id: str) -> File:
        """Get a file from the server by its ID."""

        resp = self._client._request("GET", f"/files/{file_id}")
        return _json_to_file(resp.json())

    async def async_get(self, file_id: str) -> File:
        """Get a file from the server by its ID."""

        resp = await self._client._async_request("GET", f"/files/{file_id}")
        return _json_to_file(resp.json())

    def list(self) -> List[File]:
        """List all files on the server."""

        resp = self._client._request("GET", "/files")
        return [_json_to_file(file_json) for file_json in resp.json()]

    async def async_list(self) -> List[File]:
        """List all files on the server."""

        resp = await self._client._async_request("GET", "/files")
        return [_json_to_file(file_json) for file_json in resp.json()]

    def delete(self, file_id: str) -> File:
        """Delete a file from the server by its ID."""

        resp = self._client._request("DELETE", f"/files/{file_id}")
        return _json_to_file(resp.json())

    async def async_delete(self, file_id: str) -> File:
        """Delete a file from the server by its ID."""

        resp = await self._client._async_request("DELETE", f"/files/{file_id}")
        return _json_to_file(resp.json())


def _file_content(file: io.IOBase) -> Tuple[str, io.IOBase, str]:
    """Get the file content details including name, file object and content type."""

    name = getattr(file, "name", "output")
    content_type = (
        mimetypes.guess_type(getattr(file, "name", ""))[0] or "application/octet-stream"
    )
    return (os.path.basename(name), file, content_type)


def _json_to_file(json: Dict[str, Any]) -> File:
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
