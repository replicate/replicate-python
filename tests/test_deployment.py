import httpx
import respx

from replicate.client import Client

router = respx.Router(base_url="https://api.replicate.com/v1")
router.route(
    method="POST",
    path="/deployments/test/model/predictions",
    name="deployments.predictions.create",
).mock(
    return_value=httpx.Response(
        201,
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
            "input": {"text": "world"},
            "output": None,
            "error": None,
            "logs": "",
        },
    )
)
router.route(host="api.replicate.com").pass_through()


def test_deployment_predictions_create():
    client = Client(
        api_token="test-token", transport=httpx.MockTransport(router.handler)
    )
    deployment = client.deployments.get("test/model")

    prediction = deployment.predictions.create(
        input={"text": "world"},
        webhook="https://example.com/webhook",
        webhook_events_filter=["completed"],
    )

    assert router["deployments.predictions.create"].called
    assert prediction.id == "p1"
    assert prediction.input == {"text": "world"}
