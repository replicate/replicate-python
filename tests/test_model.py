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


@pytest.mark.vcr("models-list.yaml")
@pytest.mark.asyncio
async def test_models_list_pagination(mock_replicate_api_token):
    page1 = replicate.models.list()
    assert len(page1) > 0
    assert page1.next is not None

    page2 = replicate.models.list(cursor=page1.next)
    assert len(page2) > 0
    assert page2.previous is not None


@pytest.mark.vcr("models-create.yaml")
@pytest.mark.asyncio
async def test_models_create(mock_replicate_api_token):
    model = replicate.models.create(
        owner="test",
        name="python-example",
        visibility="private",
        hardware="cpu",
        description="An example model",
    )

    assert model.owner == "test"
    assert model.name == "python-example"
    assert model.visibility == "private"


@pytest.mark.vcr("models-create.yaml")
@pytest.mark.asyncio
async def test_models_create_with_positional_arguments(mock_replicate_api_token):
    model = replicate.models.create(
        "test",
        "python-example",
        visibility="private",
        hardware="cpu",
    )

    assert model.owner == "test"
    assert model.name == "python-example"
    assert model.visibility == "private"
