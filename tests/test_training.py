import pytest

import replicate
from replicate.exceptions import APIError

input_images_url = "https://replicate.delivery/pbxt/JMV5OrEWpBAC5gO8rre0tPOyJIOkaXvG0TWfVJ9b4zhLeEUY/data.zip"


@pytest.mark.vcr("trainings-create.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_trainings_create(async_flag):
    id = "a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5"

    if async_flag:
        training = await replicate.async_trainings.create(
            "stability-ai",
            "sdxl",
            id,
            destination="replicate/dreambooth-sdxl",
            input={
                "input_images": input_images_url,
                "use_face_detection_instead": True,
            },
        )
    else:
        training = replicate.trainings.create(
            "stability-ai",
            "sdxl",
            id,
            destination="replicate/dreambooth-sdxl",
            input={
                "input_images": input_images_url,
                "use_face_detection_instead": True,
            },
        )

    assert training.id is not None
    assert training.status == "starting"


@pytest.mark.vcr("trainings-create__invalid-destination.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_trainings_create_with_invalid_destination(async_flag):
    id = "a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5"

    with pytest.raises(APIError) as excinfo:
        if async_flag:
            await replicate.async_trainings.create(
                "stability-ai",
                "sdxl",
                id,
                destination="<invalid>",
                input={
                    "input_images": input_images_url,
                },
            )
        else:
            replicate.trainings.create(
                "stability-ai",
                "sdxl",
                id,
                destination="<invalid>",
                input={
                    "input_images": input_images_url,
                },
            )

    error: APIError = excinfo.value
    assert error.status == 404
    assert error.detail == "The specified training destination does not exist"


@pytest.mark.vcr("trainings-get.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_trainings_get(async_flag):
    id = "medrnz3bm5dd6ultvad2tejrte"

    if async_flag:
        training = await replicate.async_trainings.get(id)
    else:
        training = replicate.trainings.get(id)

    assert training.id == id
    assert training.status == "running"


@pytest.mark.vcr("trainings-cancel.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_trainings_cancel(async_flag):
    id = "a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5"

    input = {
        "input_images": input_images_url,
        "use_face_detection_instead": True,
    }

    destination = "replicate/dreambooth-sdxl"

    if async_flag:
        training = await replicate.async_trainings.create(
            "stability-ai", "sdxl", id, destination=destination, input=input
        )
    else:
        training = replicate.trainings.create(
            "stability-ai",
            "sdxl",
            id,
            destination=destination,
            input=input,
        )

    id = training.id
    assert training.status == "starting"

    if async_flag:
        training = await replicate.async_trainings.cancel(training)
    else:
        training = replicate.trainings.cancel(training)

    assert training.id == id
    assert training.status == "canceled"
