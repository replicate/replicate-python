import os
import tempfile

import httpx
import pytest
import respx

import replicate
from replicate.client import Client

from .conftest import skip_if_no_token

router = respx.Router(base_url="https://api.replicate.com/v1")

router.route(
    method="POST",
    path="/files",
    name="files.create",
).mock(
    return_value=httpx.Response(
        201,
        json={
            "id": "0ZjcyLWFhZjkNGZiNmY2YzQtMThhZi0tODg4NTY0NWNlMDEy",
            "name": "hello.txt",
            "size": 14,
            "content_type": "text/plain",
            "etag": "746308829575e17c3331bbcb00c0898b",
            "checksums": {
                "md5": "746308829575e17c3331bbcb00c0898b",
                "sha256": "d9014c4624844aa5bac314773d6b689ad467fa4e1d1a50a1b8a99d5a95f72ff5",
            },
            "metadata": {
                "foo": "bar",
            },
            "urls": {
                "get": "https://api.replicate.com/v1/files/0ZjcyLWFhZjkNGZiNmY2YzQtMThhZi0tODg4NTY0NWNlMDEy",
            },
            "created_at": "2024-08-22T12:26:51.079Z",
            "expires_at": "2024-08-22T13:26:51.079Z",
        },
    )
)


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
@pytest.mark.parametrize("use_path", [True, False])
async def test_file_create(async_flag, use_path):
    client = Client(
        api_token="test-token", transport=httpx.MockTransport(router.handler)
    )

    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, "hello.txt")

    try:
        with open(temp_file_path, "w", encoding="utf-8") as temp_file:
            temp_file.write("Hello, world!")

        metadata = {"foo": "bar"}

        if use_path:
            file_arg = temp_file_path
            if async_flag:
                created_file = await client.files.async_create(
                    file_arg, metadata=metadata
                )
            else:
                created_file = client.files.create(file_arg, metadata=metadata)
        else:
            with open(temp_file_path, "rb") as file_arg:
                if async_flag:
                    created_file = await client.files.async_create(
                        file_arg, metadata=metadata
                    )
                else:
                    created_file = client.files.create(file_arg, metadata=metadata)

        assert router["files.create"].called
        request = router["files.create"].calls[0].request

        # Check that the request is multipart/form-data
        assert request.headers["Content-Type"].startswith("multipart/form-data")

        # Check that the filename is included and matches the fixed file name
        assert b'filename="hello.txt"' in request.content
        assert b"Hello, world!" in request.content

        # Check the response
        assert created_file.id == "0ZjcyLWFhZjkNGZiNmY2YzQtMThhZi0tODg4NTY0NWNlMDEy"
        assert created_file.name == "hello.txt"
        assert created_file.size == 14
        assert created_file.content_type == "text/plain"
        assert created_file.etag == "746308829575e17c3331bbcb00c0898b"
        assert created_file.checksums == {
            "md5": "746308829575e17c3331bbcb00c0898b",
            "sha256": "d9014c4624844aa5bac314773d6b689ad467fa4e1d1a50a1b8a99d5a95f72ff5",
        }
        assert created_file.metadata == metadata
        assert created_file.urls == {
            "get": "https://api.replicate.com/v1/files/0ZjcyLWFhZjkNGZiNmY2YzQtMThhZi0tODg4NTY0NWNlMDEy",
        }

    finally:
        os.unlink(temp_file_path)
        os.rmdir(temp_dir)


@skip_if_no_token
@pytest.mark.skipif(os.environ.get("CI") is not None, reason="Do not run on CI")
# @pytest.mark.vcr("file-prediction.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_file_prediction(async_flag):
    # Normally, we'd pass a URL as an input to the model,
    # but we're testing the file operations here, so we're
    # downloading the image to a temp file instead.
    image_url = "https://replicate.delivery/pbxt/LUSNInCegT0XwStCCJjXOojSBhPjpk2Pzj5VNjksiP9cER8A/ComfyUI_02172_.png"

    if async_flag:
        client = httpx.AsyncClient()
        response = await client.get(image_url)
    else:
        client = httpx.Client()
        response = httpx.get(image_url)

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(response.content)

        model = "fofr/flux-dev-controlnet:56ac7b66bd9a1b5eb7d15da5ac5625e4c8c9c5bc26da892caf6249cf38a611ed"
        input = {
            "steps": 28,
            "prompt": "a cyberpunk with natural greys and whites and browns",
            "control_type": "depth",
            "control_image": open(temp_file.name, "rb"),
            "output_format": "webp",
            "guidance_scale": 2.5,
            "output_quality": 100,
            "negative_prompt": "low quality, ugly, distorted, artefacts",
            "control_strength": 0.45,
            "depth_preprocessor": "DepthAnything",
            "soft_edge_preprocessor": "HED",
            "image_to_image_strength": 0,
            "return_preprocessed_image": False,
        }

        if async_flag:
            output = await replicate.async_run(model, input=input)
        else:
            output = replicate.run(model, input=input)

        assert output is not None


@pytest.mark.vcr("file-operations.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_file_operations(async_flag):
    # Create a sample file
    with tempfile.NamedTemporaryFile(
        mode="wb", delete=False, prefix="test_file", suffix=".txt"
    ) as temp_file:
        temp_file.write(b"Hello, Replicate!")

        # Test create
        if async_flag:
            created_file = await replicate.files.async_create(temp_file.name)
        else:
            created_file = replicate.files.create(temp_file.name)

    assert created_file.name.startswith("test_file")
    assert created_file.name.endswith(".txt")
    file_id = created_file.id

    # Test get
    if async_flag:
        retrieved_file = await replicate.files.async_get(file_id)
    else:
        retrieved_file = replicate.files.get(file_id)

    assert retrieved_file.id == file_id

    # Test list
    if async_flag:
        file_list = await replicate.files.async_list()
    else:
        file_list = replicate.files.list()

    assert file_list is not None
    assert len(file_list) > 0
    assert any(f.id == file_id for f in file_list)

    # Test delete
    if async_flag:
        await replicate.files.async_delete(file_id)
    else:
        replicate.files.delete(file_id)

    # Verify file is deleted
    if async_flag:
        file_list = await replicate.files.async_list()
    else:
        file_list = replicate.files.list()

    assert all(f.id != file_id for f in file_list)
