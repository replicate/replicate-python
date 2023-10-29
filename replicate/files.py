import base64
import io
import mimetypes
import os
from typing import Optional

import httpx


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
