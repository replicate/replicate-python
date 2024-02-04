import pytest

import replicate
from replicate.exceptions import ReplicateException

input_images_url = "https://replicate.delivery/pbxt/JMV5OrEWpBAC5gO8rre0tPOyJIOkaXvG0TWfVJ9b4zhLeEUY/data.zip"


@pytest.mark.vcr("trainings-create.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_trainings_create(async_flag, mock_replicate_api_token):
    if async_flag:
        training = await replicate.trainings.async_create(
            model="stability-ai/sdxl",
            version="a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5",
            input={
                "input_images": input_images_url,
                "use_face_detection_instead": True,
            },
            destination="replicate/dreambooth-sdxl",
        )
    else:
        training = replicate.trainings.create(
            model="stability-ai/sdxl",
            version="a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5",
            input={
                "input_images": input_images_url,
                "use_face_detection_instead": True,
            },
            destination="replicate/dreambooth-sdxl",
        )

    assert training.id is not None
    assert training.status == "starting"


@pytest.mark.vcr("trainings-create.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_trainings_create_with_named_version_argument(
    async_flag, mock_replicate_api_token
):
    if async_flag:
        # The overload with a model version identifier is soft-deprecated
        # and not supported in the async version.
        return
    else:
        training = replicate.trainings.create(
            version="stability-ai/sdxl:a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5",
            input={
                "input_images": input_images_url,
                "use_face_detection_instead": True,
            },
            destination="replicate/dreambooth-sdxl",
        )

    assert training.id is not None
    assert training.status == "starting"


@pytest.mark.vcr("trainings-create.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_trainings_create_with_positional_argument(
    async_flag, mock_replicate_api_token
):
    if async_flag:
        # The overload with positional arguments is soft-deprecated
        # and not supported in the async version.
        return
    else:
        training = replicate.trainings.create(
            "stability-ai/sdxl:a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5",
            {
                "input_images": input_images_url,
                "use_face_detection_instead": True,
            },
            "replicate/dreambooth-sdxl",
        )

        assert training.id is not None
        assert training.status == "starting"


@pytest.mark.vcr("trainings-create__invalid-destination.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_trainings_create_with_invalid_destination(
    async_flag, mock_replicate_api_token
):
    with pytest.raises(ReplicateException):
        if async_flag:
            await replicate.trainings.async_create(
                model="stability-ai/sdxl",
                version="a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5",
                input={
                    "input_images": input_images_url,
                    "use_face_detection_instead": True,
                },
                destination="<invalid>",
            )
        else:
            replicate.trainings.create(
                model="stability-ai/sdxl",
                version="a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5",
                input={
                    "input_images": input_images_url,
                },
                destination="<invalid>",
            )


@pytest.mark.vcr("trainings-get.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_trainings_get(async_flag, mock_replicate_api_token):
    id = "medrnz3bm5dd6ultvad2tejrte"

    if async_flag:
        training = await replicate.trainings.async_get(id)
    else:
        training = replicate.trainings.get(id)

    assert training.id == id
    assert training.status == "processing"


@pytest.mark.vcr("trainings-cancel.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_trainings_cancel(async_flag, mock_replicate_api_token):
    input = {
        "input_images": input_images_url,
        "use_face_detection_instead": True,
    }

    destination = "replicate/dreambooth-sdxl"

    if async_flag:
        training = await replicate.trainings.async_create(
            model="stability-ai/sdxl",
            version="a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5",
            input=input,
            destination=destination,
        )

        assert training.status == "starting"

        training = replicate.trainings.cancel(training.id)
        assert training.status == "canceled"
    else:
        training = replicate.trainings.create(
            version="stability-ai/sdxl:a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5",
            destination=destination,
            input=input,
        )

        assert training.status == "starting"

        training = replicate.trainings.cancel(training.id)
        assert training.status == "canceled"


@pytest.mark.vcr("trainings-cancel.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_trainings_cancel_instance_method(async_flag, mock_replicate_api_token):
    input = {
        "input_images": input_images_url,
        "use_face_detection_instead": True,
    }

    destination = "replicate/dreambooth-sdxl"

    if async_flag:
        # The cancel instance method is soft-deprecated,
        # and not supported in the async version.
        return
    else:
        training = replicate.trainings.create(
            version="stability-ai/sdxl:a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5",
            destination=destination,
            input=input,
        )

        assert training.status == "starting"

        training.cancel()
        assert training.status == "canceled"
