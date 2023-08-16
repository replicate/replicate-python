import pytest

import replicate


@pytest.mark.vcr("models-get.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_models_get(async_flag):
    if async_flag:
        model = await replicate.async_models.get("stability-ai", "sdxl")
    else:
        model = replicate.models.get("stability-ai", "sdxl")

    assert model is not None
    assert model.owner == "stability-ai"
    assert model.name == "sdxl"
    assert model.visibility == "public"
    assert model.latest_version is not None
