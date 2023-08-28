import pytest

import replicate


@pytest.mark.vcr("predictions-create.yaml")
@pytest.mark.asyncio
async def test_predictions_create(mock_replicate_api_token):
    input = {
        "prompt": "a studio photo of a rainbow colored corgi",
        "width": 512,
        "height": 512,
        "seed": 42069,
    }

    model = replicate.models.get("stability-ai/sdxl")
    version = model.versions.get(
        "a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5"
    )
    prediction = replicate.predictions.create(
        version=version,
        input=input,
    )

    assert prediction.id is not None
    assert prediction.version == version
    assert prediction.status == "starting"


@pytest.mark.vcr("predictions-get.yaml")
@pytest.mark.asyncio
async def test_predictions_get(mock_replicate_api_token):
    id = "vgcm4plb7tgzlyznry5d5jkgvu"

    prediction = replicate.predictions.get(id)

    assert prediction.id == id


@pytest.mark.vcr("predictions-cancel.yaml")
@pytest.mark.asyncio
async def test_predictions_cancel(mock_replicate_api_token):
    input = {
        "prompt": "a studio photo of a rainbow colored corgi",
        "width": 512,
        "height": 512,
        "seed": 42069,
    }

    model = replicate.models.get("stability-ai/sdxl")
    version = model.versions.get(
        "a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5"
    )
    prediction = replicate.predictions.create(
        version=version,
        input=input,
    )

    # id = prediction.id
    assert prediction.status == "starting"

    # prediction = replicate.predictions.cancel(prediction)
    prediction.cancel()

    # assert prediction.id == id
    # assert prediction.status == "canceled"
