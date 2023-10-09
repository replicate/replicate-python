import pytest

import replicate


@pytest.mark.vcr("models-get.yaml")
@pytest.mark.asyncio
async def test_models_get(mock_replicate_api_token):
    sdxl = replicate.models.get("stability-ai/sdxl")

    assert sdxl is not None
    assert sdxl.owner == "stability-ai"
    assert sdxl.name == "sdxl"
    assert sdxl.visibility == "public"

    empty = replicate.models.get("mattt/empty")

    assert empty.default_example is None


@pytest.mark.vcr("models-list.yaml")
@pytest.mark.asyncio
async def test_models_list(mock_replicate_api_token):
    models = replicate.models.list()

    assert len(models) > 0
    assert models[0].owner is not None
    assert models[0].name is not None
    assert models[0].visibility == "public"
