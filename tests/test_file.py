import os
import tempfile

import httpx
import pytest

import replicate

from .conftest import skip_if_no_token


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
