import io

import pytest

from replicate.helpers import base64_encode_file


@pytest.mark.parametrize(
    "content, filename, expected",
    [
        (b"Hello, World!", "test.txt", "data:text/plain;base64,SGVsbG8sIFdvcmxkIQ=="),
        (b"\x89PNG\r\n\x1a\n", "image.png", "data:image/png;base64,iVBORw0KGgo="),
        (
            "{'key': 'value'}",
            "data.json",
            "data:application/json;base64,eydrZXknOiAndmFsdWUnfQ==",
        ),
        (
            b"Random bytes",
            None,
            "data:application/octet-stream;base64,UmFuZG9tIGJ5dGVz",
        ),
    ],
)
def test_base64_encode_file(content, filename, expected):
    # Create a file-like object with the given content
    file = io.BytesIO(content if isinstance(content, bytes) else content.encode())

    # Set the filename if provided
    if filename:
        file.name = filename

    # Call the function and check the result
    result = base64_encode_file(file)
    assert result == expected


def test_file_output_equality_and_repr():
    from replicate.client import Client
    from replicate.helpers import FileOutput

    client = Client(api_token="test")
    fo1 = FileOutput("https://replicate.delivery/test.png", client)
    fo2 = FileOutput("https://replicate.delivery/test.png", client)
    fo3 = FileOutput("https://replicate.delivery/other.png", client)

    assert fo1 == fo2
    assert fo1 != fo3
    assert fo1 == "https://replicate.delivery/test.png"
    assert "https://replicate.delivery/test.png" == fo1
    assert fo1 != "https://replicate.delivery/other.png"
    assert repr(fo1) == "FileOutput('https://replicate.delivery/test.png')"
    assert hash(fo1) == hash("https://replicate.delivery/test.png")
    assert {fo1, fo2} == {fo1}


def test_encode_json_with_file_output():
    import json

    from replicate.client import Client
    from replicate.helpers import FileOutput, encode_json

    client = Client(api_token="test")
    url = "https://replicate.delivery/test.png"
    fo = FileOutput(url, client)

    # Direct FileOutput encoding
    encoded = encode_json(fo, client)
    assert encoded == url
    assert json.dumps({"image": encoded}) == f'{{"image": "{url}"}}'

    # Nested FileOutput in dict and list
    nested = {"image": fo, "images": [fo]}
    encoded_nested = encode_json(nested, client)
    assert encoded_nested == {"image": url, "images": [url]}
    assert json.dumps(encoded_nested) == f'{{"image": "{url}", "images": ["{url}"]}}'

    # Data URI FileOutput with base64 strategy
    data_uri = "data:image/png;base64,iVBORw0KGgo="
    fo_data = FileOutput(data_uri, client)
    assert encode_json(fo_data, client, file_encoding_strategy="base64") == data_uri


@pytest.mark.asyncio
async def test_async_encode_json_with_file_output():
    import json

    from replicate.client import Client
    from replicate.helpers import FileOutput, async_encode_json

    client = Client(api_token="test")
    url = "https://replicate.delivery/test.png"
    fo = FileOutput(url, client)

    encoded = await async_encode_json(fo, client)
    assert encoded == url
    assert json.dumps({"image": encoded}) == f'{{"image": "{url}"}}'

    nested = {"image": fo, "images": [fo]}
    encoded_nested = await async_encode_json(nested, client)
    assert encoded_nested == {"image": url, "images": [url]}
    assert json.dumps(encoded_nested) == f'{{"image": "{url}", "images": ["{url}"]}}'

    data_uri = "data:image/png;base64,iVBORw0KGgo="
    fo_data = FileOutput(data_uri, client)
    assert (
        await async_encode_json(fo_data, client, file_encoding_strategy="base64")
        == data_uri
    )
