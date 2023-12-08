import pytest

import replicate


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_stream(async_flag, record_mode):
    if record_mode == "none":
        return

    version = "02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3"

    input = {
        "prompt": "Please write a haiku about llamas.",
    }

    events = []

    if async_flag:
        async for event in await replicate.async_stream(
            f"meta/llama-2-70b-chat:{version}",
            input=input,
        ):
            events.append(event)
    else:
        for event in replicate.stream(
            f"meta/llama-2-70b-chat:{version}",
            input=input,
        ):
            events.append(event)

    assert len(events) > 0
    assert events[0].event == "output"


@pytest.mark.asyncio
async def test_stream_prediction(record_mode):
    if record_mode == "none":
        return

    version = "02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3"

    input = {
        "prompt": "Please write a haiku about llamas.",
    }

    prediction = replicate.predictions.create(version=version, input=input)

    events = []
    for event in prediction.stream():
        events.append(event)

    assert len(events) > 0
    assert events[0].event == "output"
