import io
import json

import pytest

from replicate.client import Client
from replicate.helpers import async_encode_json, base64_encode_file, encode_json


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


@pytest.mark.parametrize("value", [True, False])
async def test_numpy_boolean_prediction_inputs(value):
    np = pytest.importorskip("numpy")
    inputs = {"enabled": np.bool_(value), "flags": [np.bool_(value)]}
    client = Client()
    for payload in (
        encode_json(inputs, client),
        await async_encode_json(inputs, client),
    ):
        decoded = json.loads(json.dumps(payload))
        assert decoded["enabled"] is value
        assert decoded["flags"][0] is value
