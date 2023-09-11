import responses
from responses import matchers

from replicate.client import Client


@responses.activate
def test_deployment_predictions_create():
    client = Client(api_token="abc123")

    deployment = client.deployments.get("test/model")

    rsp = responses.post(
        "https://api.replicate.com/v1/deployments/test/model/predictions",
        match=[
            matchers.json_params_matcher(
                {
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
            "source": "api",
            "status": "processing",
            "input": {"text": "hello"},
            "output": None,
            "error": None,
            "logs": "",
        },
    )

    deployment.predictions.create(
        input={"text": "world"},
        webhook="https://example.com/webhook",
        webhook_events_filter=["completed"],
    )

    assert rsp.call_count == 1
