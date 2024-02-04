import json

import httpx
import pytest
import respx

from replicate.client import Client

router = respx.Router(base_url="https://api.replicate.com/v1")

router.route(
    method="GET",
    path="/deployments/replicate/my-app-image-generator",
    name="deployments.get",
).mock(
    return_value=httpx.Response(
        201,
        json={
            "owner": "replicate",
            "name": "my-app-image-generator",
            "current_release": {
                "number": 1,
                "model": "stability-ai/sdxl",
                "version": "da77bc59ee60423279fd632efb4795ab731d9e3ca9705ef3341091fb989b7eaf",
                "created_at": "2024-02-15T16:32:57.018467Z",
                "created_by": {
                    "type": "organization",
                    "username": "acme",
                    "name": "Acme Corp, Inc.",
                    "github_url": "https://github.com/acme",
                },
                "configuration": {
                    "hardware": "gpu-t4",
                    "scaling": {"min_instances": 1, "max_instances": 5},
                },
            },
        },
    )
)
router.route(
    method="POST",
    path="/deployments/replicate/my-app-image-generator/predictions",
    name="deployments.predictions.create",
).mock(
    return_value=httpx.Response(
        201,
        json={
            "id": "p1",
            "model": "replicate/my-app-image-generator",
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


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_deployment_get(async_flag):
    client = Client(
        api_token="test-token", transport=httpx.MockTransport(router.handler)
    )

    if async_flag:
        deployment = await client.deployments.async_get(
            "replicate/my-app-image-generator"
        )
    else:
        deployment = client.deployments.get("replicate/my-app-image-generator")

    assert router["deployments.get"].called

    assert deployment.owner == "replicate"
    assert deployment.name == "my-app-image-generator"
    assert deployment.current_release is not None
    assert deployment.current_release.number == 1
    assert deployment.current_release.model == "stability-ai/sdxl"
    assert (
        deployment.current_release.version
        == "da77bc59ee60423279fd632efb4795ab731d9e3ca9705ef3341091fb989b7eaf"
    )
    assert deployment.current_release.created_by.type == "organization"
    assert deployment.current_release.created_by.username == "acme"
    assert deployment.current_release.created_by.name == "Acme Corp, Inc."
    assert deployment.current_release.created_by.github_url == "https://github.com/acme"


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_deployment_predictions_create(async_flag):
    client = Client(
        api_token="test-token", transport=httpx.MockTransport(router.handler)
    )

    if async_flag:
        deployment = await client.deployments.async_get(
            "replicate/my-app-image-generator"
        )

        prediction = await deployment.predictions.async_create(
            input={"text": "world"},
            webhook="https://example.com/webhook",
            webhook_events_filter=["completed"],
            stream=True,
        )
    else:
        deployment = client.deployments.get("replicate/my-app-image-generator")

        prediction = deployment.predictions.create(
            input={"text": "world"},
            webhook="https://example.com/webhook",
            webhook_events_filter=["completed"],
            stream=True,
        )

    assert router["deployments.predictions.create"].called
    request = router["deployments.predictions.create"].calls[0].request
    request_body = json.loads(request.content)
    assert request_body["input"] == {"text": "world"}
    assert request_body["webhook"] == "https://example.com/webhook"
    assert request_body["webhook_events_filter"] == ["completed"]
    assert request_body["stream"] is True

    assert prediction.id == "p1"
    assert prediction.input == {"text": "world"}


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_deploymentspredictions_create(async_flag):
    client = Client(
        api_token="test-token", transport=httpx.MockTransport(router.handler)
    )

    if async_flag:
        prediction = await client.deployments.predictions.async_create(
            deployment="replicate/my-app-image-generator",
            input={"text": "world"},
            webhook="https://example.com/webhook",
            webhook_events_filter=["completed"],
            stream=True,
        )
    else:
        prediction = await client.deployments.predictions.async_create(
            deployment="replicate/my-app-image-generator",
            input={"text": "world"},
            webhook="https://example.com/webhook",
            webhook_events_filter=["completed"],
            stream=True,
        )

    assert router["deployments.predictions.create"].called
    request = router["deployments.predictions.create"].calls[0].request
    request_body = json.loads(request.content)
    assert request_body["input"] == {"text": "world"}
    assert request_body["webhook"] == "https://example.com/webhook"
    assert request_body["webhook_events_filter"] == ["completed"]
    assert request_body["stream"] is True

    assert prediction.id == "p1"
    assert prediction.input == {"text": "world"}
