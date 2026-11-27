import httpx
import pytest

import replicate
from replicate.exceptions import ReplicateError
from replicate.stream import EventSource, ServerSentEvent

from .conftest import skip_if_no_token


@skip_if_no_token
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_stream(async_flag, record_mode):
    model = "replicate/canary:30e22229542eb3f79d4f945dacb58d32001b02cc313ae6f54eef27904edf3272"
    input = {
        "text": "Hello",
    }

    events = []

    try:
        if async_flag:
            async for event in await replicate.async_stream(
                model,
                input=input,
            ):
                events.append(event)
        else:
            for event in replicate.stream(
                model,
                input=input,
            ):
                events.append(event)

        assert len(events) > 0
        assert any(event.event == ServerSentEvent.EventType.OUTPUT for event in events)
        assert any(event.event == ServerSentEvent.EventType.DONE for event in events)
    except ReplicateError as e:
        if e.status == 401:
            pytest.skip("Skipping test due to authentication error")
        else:
            raise e


@skip_if_no_token
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_stream_prediction(async_flag, record_mode):
    version = "30e22229542eb3f79d4f945dacb58d32001b02cc313ae6f54eef27904edf3272"
    input = {
        "text": "Hello",
    }

    events = []

    try:
        if async_flag:
            async for event in replicate.predictions.create(
                version=version, input=input, stream=True
            ).async_stream():
                events.append(event)
        else:
            for event in replicate.predictions.create(
                version=version, input=input, stream=True
            ).stream():
                events.append(event)

        assert len(events) > 0
    except ReplicateError as e:
        if e.status == 401:
            pytest.skip("Skipping test due to authentication error")
        else:
            raise e


@pytest.mark.parametrize("async_flag", [True, False])
async def test_event_stream_media_type_is_case_insensitive(async_flag):
    response = httpx.Response(
        200,
        headers={"Content-Type": "Text/Event-Stream; charset=utf-8"},
        content=b"id: 1\nevent: output\ndata: hello\n\n",
    )
    source = EventSource(replicate.Client(), response)
    events = [event async for event in source] if async_flag else list(source)
    assert [str(event) for event in events] == ["hello"]


def test_event_stream_rejects_other_media_types():
    response = httpx.Response(200, headers={"Content-Type": "text/plain"})
    with pytest.raises(ValueError, match="text/plain"):
        EventSource(replicate.Client(), response)
