import responses
from responses import matchers

from .factories import create_client, create_version


@responses.activate
def test_create_works_with_webhooks():
    client = create_client()
    version = create_version(client)

    rsp = responses.post(
        "https://api.replicate.com/v1/models/owner/model/versions/v1/trainings",
        match=[
            matchers.json_params_matcher(
                {
                    "input": {"data": "..."},
                    "destination": "new_owner/new_model",
                    "webhook": "https://example.com/webhook",
                    "webhook_events_filter": ["completed"],
                }
            ),
        ],
        json={
            "id": "t1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/trainings/t1",
                "cancel": "https://api.replicate.com/v1/trainings/t1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "processing",
            "input": {"data": "..."},
            "output": None,
            "error": None,
            "logs": "",
        },
    )

    client.trainings.create(
        version=f"owner/model:{version.id}",
        input={"data": "..."},
        destination="new_owner/new_model",
        webhook="https://example.com/webhook",
        webhook_events_filter=["completed"],
    )

    assert rsp.call_count == 1


@responses.activate
def test_cancel():
    client = create_client()
    version = create_version(client)

    responses.post(
        "https://api.replicate.com/v1/models/owner/model/versions/v1/trainings",
        match=[
            matchers.json_params_matcher(
                {
                    "input": {"data": "..."},
                    "destination": "new_owner/new_model",
                    "webhook": "https://example.com/webhook",
                    "webhook_events_filter": ["completed"],
                }
            ),
        ],
        json={
            "id": "t1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/trainings/t1",
                "cancel": "https://api.replicate.com/v1/trainings/t1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "processing",
            "input": {"data": "..."},
            "output": None,
            "error": None,
            "logs": "",
        },
    )

    training = client.trainings.create(
        version=f"owner/model:{version.id}",
        input={"data": "..."},
        destination="new_owner/new_model",
        webhook="https://example.com/webhook",
        webhook_events_filter=["completed"],
    )

    rsp = responses.post("https://api.replicate.com/v1/trainings/t1/cancel", json={})
    training.cancel()
    assert rsp.call_count == 1


@responses.activate
def test_async_timings():
    client = create_client()
    version = create_version(client)

    responses.post(
        "https://api.replicate.com/v1/models/owner/model/versions/v1/trainings",
        match=[
            matchers.json_params_matcher(
                {
                    "input": {"data": "..."},
                    "destination": "new_owner/new_model",
                    "webhook": "https://example.com/webhook",
                    "webhook_events_filter": ["completed"],
                }
            ),
        ],
        json={
            "id": "t1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/trainings/t1",
                "cancel": "https://api.replicate.com/v1/trainings/t1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "source": "api",
            "status": "processing",
            "input": {"data": "..."},
            "output": None,
            "error": None,
            "logs": "",
        },
    )

    responses.get(
        "https://api.replicate.com/v1/trainings/t1",
        json={
            "id": "t1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/trainings/t1",
                "cancel": "https://api.replicate.com/v1/trainings/t1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "succeeded",
            "input": {"data": "..."},
            "output": {
                "weights": "https://delivery.replicate.com/weights.tgz",
                "version": "v2",
            },
            "error": None,
            "logs": "",
        },
    )

    training = client.trainings.create(
        version=f"owner/model:{version.id}",
        input={"data": "..."},
        destination="new_owner/new_model",
        webhook="https://example.com/webhook",
        webhook_events_filter=["completed"],
    )

    assert training.created_at == "2022-04-26T20:00:40.658234Z"
    assert training.completed_at is None
    assert training.output is None

    # trainings don't have a wait method, so simulate it by calling reload
    training.reload()
    assert training.created_at == "2022-04-26T20:00:40.658234Z"
    assert training.completed_at == "2022-04-26T20:02:27.648305Z"
    assert training.output["weights"] == "https://delivery.replicate.com/weights.tgz"
    assert training.output["version"] == "v2"
