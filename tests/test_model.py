import pytest

import replicate


@pytest.mark.vcr("models-get.yaml")
@pytest.mark.asyncio
async def test_models_get(mock_replicate_api_token):
    model = replicate.models.get("stability-ai/sdxl")

    assert model is not None
    assert model.owner == "stability-ai"
    assert model.name == "sdxl"
    assert model.visibility == "public"


@pytest.mark.vcr("models-list.yaml")
@pytest.mark.asyncio
async def test_models_list(mock_replicate_api_token):
    models = replicate.models.list()

    assert len(models) > 0
    assert models[0].owner is not None
    assert models[0].name is not None
    assert models[0].visibility == "public"
