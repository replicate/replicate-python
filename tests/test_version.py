import pytest

import replicate


@pytest.mark.vcr("models-versions-get.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_models_versions_get(async_flag):
    id = "a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5"

    if async_flag:
        version = await replicate.async_models.versions.get("stability-ai", "sdxl", id)
    else:
        version = replicate.models.versions.get("stability-ai", "sdxl", id)

    assert version.id == id


@pytest.mark.vcr("models-versions-list.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_models_versions_list(async_flag):
    if async_flag:
        page = await replicate.async_models.versions.list("stability-ai", "sdxl")
    else:
        page = replicate.models.versions.list("stability-ai", "sdxl")

    assert page.previous is None
    assert len(page.results) > 0

    version = page.results[0]
    assert version.id is not None
