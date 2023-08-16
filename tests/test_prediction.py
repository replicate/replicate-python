import pytest

import replicate


@pytest.mark.vcr("predictions-create.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_predictions_create(async_flag):
    input = {
        "prompt": "a studio photo of a rainbow colored corgi",
        "width": 512,
        "height": 512,
        "seed": 42069,
    }

    if async_flag:
        model = await replicate.async_models.get("stability-ai", "sdxl")
        version = model.latest_version
        prediction = await replicate.async_predictions.create(
            version=version,
            input=input,
        )
    else:
        model = replicate.models.get("stability-ai", "sdxl")
        version = model.latest_version
        prediction = replicate.predictions.create(
            version=version,
            input=input,
        )

    assert prediction.id is not None
    assert prediction.version == version.id
    assert prediction.status == "starting"


@pytest.mark.vcr("predictions-get.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_predictions_get(async_flag):
    id = "vgcm4plb7tgzlyznry5d5jkgvu"

    if async_flag:
        prediction = await replicate.async_predictions.get(id)
    else:
        prediction = replicate.predictions.get(id)

    assert prediction.id == id


@pytest.mark.vcr("predictions-cancel.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_predictions_cancel(async_flag):
    input = {
        "prompt": "a studio photo of a rainbow colored corgi",
        "width": 512,
        "height": 512,
        "seed": 42069,
    }

    if async_flag:
        model = await replicate.async_models.get("stability-ai", "sdxl")
        version = model.latest_version
        prediction = await replicate.async_predictions.create(
            version=version,
            input=input,
        )
    else:
        model = replicate.models.get("stability-ai", "sdxl")
        version = model.latest_version
        prediction = replicate.predictions.create(
            version=version,
            input=input,
        )

    id = prediction.id
    assert prediction.status == "starting"

    prediction = replicate.predictions.cancel(prediction)

    assert prediction.id == id
    assert prediction.status == "canceled"
