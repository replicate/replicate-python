import responses
from responses import matchers

import replicate

from .factories import create_client, create_version


@responses.activate
def test_create_works_with_webhooks():
    client = create_client()
    version = create_version(client)

    rsp = responses.post(
        "https://api.replicate.com/v1/predictions",
        match=[
            matchers.json_params_matcher(
                {
                    "version": "v1",
                    "input": {"text": "world"},
                    "webhook": "https://example.com/webhook",
                    "webhook_events_filter": ["completed"],
                }
            ),
        ],
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "processing",
            "input": {"text": "world"},
            "output": None,
            "error": None,
            "logs": "",
        },
    )

    prediction = client.predictions.create(
        version=version,
        input={"text": "world"},
        webhook="https://example.com/webhook",
        webhook_events_filter=["completed"],
    )

    assert rsp.call_count == 1


@responses.activate
def test_cancel():
    client = create_client()
    version = create_version(client)

    responses.post(
        "https://api.replicate.com/v1/predictions",
        match=[
            matchers.json_params_matcher(
                {
                    "version": "v1",
                    "input": {"text": "world"},
                    "webhook_completed": "https://example.com/webhook",
                }
            ),
        ],
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "processing",
            "input": {"text": "world"},
            "output": None,
            "error": None,
            "logs": "",
        },
    )

    prediction = client.predictions.create(
        version=version,
        input={"text": "world"},
        webhook_completed="https://example.com/webhook",
    )

    rsp = responses.post("https://api.replicate.com/v1/predictions/p1/cancel", json={})
    prediction.cancel()
    assert rsp.call_count == 1


@responses.activate
def test_async_timings():
    client = create_client()
    version = create_version(client)

    responses.post(
        "https://api.replicate.com/v1/predictions",
        match=[
            matchers.json_params_matcher(
                {
                    "version": "v1",
                    "input": {"text": "hello"},
                    "webhook_completed": "https://example.com/webhook",
                }
            ),
        ],
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "source": "api",
            "status": "processing",
            "input": {"text": "hello"},
            "output": None,
            "error": None,
            "logs": "",
        },
    )

    responses.get(
        "https://api.replicate.com/v1/predictions/p1",
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "succeeded",
            "input": {"text": "hello"},
            "output": "hello world",
            "error": None,
            "logs": "",
        },
    )

    prediction = client.predictions.create(
        version=version,
        input={"text": "hello"},
        webhook_completed="https://example.com/webhook",
    )

    assert prediction.created_at == "2022-04-26T20:00:40.658234Z"
    assert prediction.completed_at == None
    assert prediction.output == None
    prediction.wait()
    assert prediction.created_at == "2022-04-26T20:00:40.658234Z"
    assert prediction.completed_at == "2022-04-26T20:02:27.648305Z"
    assert prediction.output == "hello world"
