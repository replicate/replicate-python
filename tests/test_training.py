import pytest

import replicate
from replicate.exceptions import ReplicateException

input_images_url = "https://replicate.delivery/pbxt/JMV5OrEWpBAC5gO8rre0tPOyJIOkaXvG0TWfVJ9b4zhLeEUY/data.zip"


@pytest.mark.vcr("trainings-create.yaml")
@pytest.mark.asyncio
async def test_trainings_create(mock_replicate_api_token):
    training = replicate.trainings.create(
        "stability-ai/sdxl:a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5",
        input={
            "input_images": input_images_url,
            "use_face_detection_instead": True,
        },
        destination="replicate/dreambooth-sdxl",
    )

    assert training.id is not None
    assert training.status == "starting"


@pytest.mark.vcr("trainings-create__invalid-destination.yaml")
@pytest.mark.asyncio
async def test_trainings_create_with_invalid_destination(mock_replicate_api_token):
    with pytest.raises(ReplicateException):
        replicate.trainings.create(
            "stability-ai/sdxl:a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5",
            input={
                "input_images": input_images_url,
            },
            destination="<invalid>",
        )


@pytest.mark.vcr("trainings-get.yaml")
@pytest.mark.asyncio
async def test_trainings_get(mock_replicate_api_token):
    id = "ckcbvmtbvg6di3b3uhvccytnfm"

    training = replicate.trainings.get(id)

    assert training.id == id
    assert training.status == "processing"


@pytest.mark.vcr("trainings-cancel.yaml")
@pytest.mark.asyncio
async def test_trainings_cancel(mock_replicate_api_token):
    input = {
        "input_images": input_images_url,
        "use_face_detection_instead": True,
    }

    destination = "replicate/dreambooth-sdxl"

    training = replicate.trainings.create(
        "stability-ai/sdxl:a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5",
        destination=destination,
        input=input,
    )

    id = training.id
    assert training.status == "starting"

    # training = replicate.trainings.cancel(training)
    training.cancel()
    training.reload()

    assert training.id == id
    assert training.status == "canceled"
