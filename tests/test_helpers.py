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
