import pytest

import replicate

@pytest.mark.asyncio
async def test_async_client():
    model = replicate.models.get("creatorrr/instructor-large")
    version = await model.versions.get_async("bd2701dac1aea9d598bda71e6ae56b204287c0a79e2cadf96b1393127d044495")

    inputs = {
        # Text to embed
        'text': "Hello world! How are you doing?",

        # Embedding instruction
        'instruction': "Represent the following text",
    }

    output = await version.predict_async(**inputs)

    assert output["result"]
