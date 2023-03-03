import base64
import io
import mimetypes
import os

import httpx
import requests


def to_data_url(fh: io.IOBase) -> str:
    """
    Lifted straight from cog.files
    """
    fh.seek(0)

    b = fh.read()
    # The file handle is strings, not bytes
    if isinstance(b, str):
        b = b.encode("utf-8")
    encoded_body = base64.b64encode(b)
    if getattr(fh, "name", None):
        # despite doing a getattr check here, mypy complains that io.IOBase has no attribute name
        mime_type = mimetypes.guess_type(fh.name)[0]  # type: ignore
    else:
        mime_type = "application/octet-stream"
    s = encoded_body.decode("utf-8")
    return f"data:{mime_type};base64,{s}"


def upload_file_to_server(fh: io.IOBase, output_file_prefix: str) -> str:
    """
    Lifted straight from cog.files
    """
    fh.seek(0)

    name = getattr(fh, "name", "output")
    url = output_file_prefix + os.path.basename(name)
    resp = requests.put(url, files={"file": fh})
    resp.raise_for_status()
    return url


def upload_file(fh: io.IOBase, output_file_prefix: str = None) -> str:
    """
    Lifted straight from cog.files
    """
    fh.seek(0)

    if output_file_prefix is not None:
        url = upload_file_to_server(fh, output_file_prefix)
        return url

    data_url: str = to_data_url(fh)
    return data_url


async def upload_file_to_server_async(fh: io.IOBase, output_file_prefix: str) -> str:
    """
    Lifted straight from cog.files
    """
    fh.seek(0)

    name = getattr(fh, "name", "output")
    url = output_file_prefix + os.path.basename(name)

    # httpx does not follow redirects by default
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.put(url, files={"file": fh})

    return url


async def upload_file_async(fh: io.IOBase, output_file_prefix: str = None) -> str:
    """
    Lifted straight from cog.files
    """
    fh.seek(0)

    if output_file_prefix is not None:
        url = await upload_file_to_server_async(fh, output_file_prefix)
        return url

    data_url: str = to_data_url(fh)
    return data_url
