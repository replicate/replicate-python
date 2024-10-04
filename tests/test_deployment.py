import json
from typing import cast

import httpx
import pytest
import respx

from replicate.client import Client


@pytest.fixture
def router():
    router = respx.Router(base_url="https://api.replicate.com/v1")

    router.route(
        method="GET",
        path="/deployments/replicate/my-app-image-generator",
        name="deployments.get",
    ).mock(
        return_value=httpx.Response(
            200,
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
                        "min_instances": 1,
                        "max_instances": 5,
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
    router.route(
        method="GET",
        path="/deployments",
        name="deployments.list",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "owner": "acme",
                        "name": "image-upscaler",
                        "current_release": {
                            "number": 1,
                            "model": "acme/esrgan",
                            "version": "5c7d5dc6dd8bf75c1acaa8565735e7986bc5b66206b55cca93cb72c9bf15ccaa",
                            "created_at": "2022-01-01T00:00:00Z",
                            "created_by": {
                                "type": "organization",
                                "username": "acme",
                                "name": "Acme, Inc.",
                            },
                            "configuration": {
                                "hardware": "gpu-t4",
                                "min_instances": 1,
                                "max_instances": 5,
                            },
                        },
                    },
                    {
                        "owner": "acme",
                        "name": "text-generator",
                        "current_release": {
                            "number": 2,
                            "model": "acme/acme-llama",
                            "version": "4b7d5dc6dd8bf75c1acaa8565735e7986bc5b66206b55cca93cb72c9bf15ccbb",
                            "created_at": "2022-02-02T00:00:00Z",
                            "created_by": {
                                "type": "organization",
                                "username": "acme",
                                "name": "Acme, Inc.",
                            },
                            "configuration": {
                                "hardware": "cpu",
                                "min_instances": 2,
                                "max_instances": 10,
                            },
                        },
                    },
                ]
            },
        )
    )

    router.route(
        method="POST",
        path="/deployments",
        name="deployments.create",
    ).mock(
        return_value=httpx.Response(
            201,
            json={
                "owner": "acme",
                "name": "new-deployment",
                "current_release": {
                    "number": 1,
                    "model": "acme/new-model",
                    "version": "5c7d5dc6dd8bf75c1acaa8565735e7986bc5b66206b55cca93cb72c9bf15ccaa",
                    "created_at": "2022-01-01T00:00:00Z",
                    "created_by": {
                        "type": "organization",
                        "username": "acme",
                        "name": "Acme, Inc.",
                    },
                    "configuration": {
                        "hardware": "gpu-t4",
                        "min_instances": 1,
                        "max_instances": 5,
                    },
                },
            },
        )
    )

    router.route(
        method="PATCH",
        path="/deployments/acme/image-upscaler",
        name="deployments.update",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "owner": "acme",
                "name": "image-upscaler",
                "current_release": {
                    "number": 2,
                    "model": "acme/esrgan-updated",
                    "version": "new-version-id",
                    "created_at": "2022-02-02T00:00:00Z",
                    "created_by": {
                        "type": "organization",
                        "username": "acme",
                        "name": "Acme, Inc.",
                    },
                    "configuration": {
                        "hardware": "gpu-v100",
                        "min_instances": 2,
                        "max_instances": 10,
                    },
                },
            },
        )
    )

    router.route(
        method="DELETE",
        path="/deployments/acme/image-upscaler",
        name="deployments.delete",
    ).mock(return_value=httpx.Response(204))

    router.route(host="api.replicate.com").pass_through()

    return router


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_deployment_get(router, async_flag):
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
    assert deployment.current_release is not None
    assert deployment.current_release.created_by is not None
    assert deployment.current_release.created_by.type == "organization"
    assert deployment.current_release.created_by.username == "acme"
    assert deployment.current_release.created_by.name == "Acme Corp, Inc."
    assert deployment.current_release.created_by.github_url == "https://github.com/acme"


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_deployment_predictions_create(router, async_flag):
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
@pytest.mark.parametrize("wait_param", [True, 10])
@pytest.mark.parametrize("async_flag", [True, False])
async def test_deployment_predictions_create_blocking(
    router,
    async_flag: bool,  # noqa: FBT001
    wait_param: bool | int,  # noqa: FBT001
):
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
            wait=wait_param,
        )
    else:
        deployment = client.deployments.get("replicate/my-app-image-generator")
        prediction = deployment.predictions.create(
            input={"text": "world"},
            webhook="https://example.com/webhook",
            webhook_events_filter=["completed"],
            stream=True,
            wait=wait_param,
        )

    assert router["deployments.predictions.create"].called
    request = cast(
        httpx.Request, router["deployments.predictions.create"].calls[0].request
    )

    if wait_param is True:
        assert request.headers.get("Prefer") == "wait"
    else:
        assert request.headers.get("Prefer") == f"wait={wait_param}"

    request_body = json.loads(request.content)
    assert request_body["input"] == {"text": "world"}
    assert request_body["webhook"] == "https://example.com/webhook"
    assert request_body["webhook_events_filter"] == ["completed"]
    assert request_body["stream"] is True

    assert prediction.id == "p1"
    assert prediction.input == {"text": "world"}


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_deployments_predictions_create(router, async_flag):
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
@pytest.mark.parametrize("wait_param", [True, 10])
@pytest.mark.parametrize("async_flag", [True, False])
async def test_deployments_predictions_create_blocking(
    router,
    async_flag: bool,  # noqa: FBT001
    wait_param: bool | int,  # noqa: FBT001
):
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
            wait=wait_param,
        )
    else:
        prediction = client.deployments.predictions.create(
            deployment="replicate/my-app-image-generator",
            input={"text": "world"},
            webhook="https://example.com/webhook",
            webhook_events_filter=["completed"],
            stream=True,
            wait=wait_param,
        )

    assert router["deployments.predictions.create"].called
    request = cast(
        httpx.Request, router["deployments.predictions.create"].calls[0].request
    )

    if wait_param is True:
        assert request.headers.get("Prefer") == "wait"
    else:
        assert request.headers.get("Prefer") == f"wait={wait_param}"

    request_body = json.loads(request.content)
    assert request_body["input"] == {"text": "world"}
    assert request_body["webhook"] == "https://example.com/webhook"
    assert request_body["webhook_events_filter"] == ["completed"]
    assert request_body["stream"] is True

    assert prediction.id == "p1"
    assert prediction.input == {"text": "world"}


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_deployments_list(router, async_flag):
    client = Client(
        api_token="test-token", transport=httpx.MockTransport(router.handler)
    )

    if async_flag:
        deployments = await client.deployments.async_list()
    else:
        deployments = client.deployments.list()

    assert router["deployments.list"].called

    assert len(deployments.results) == 2
    assert deployments.results[0].owner == "acme"
    assert deployments.results[0].name == "image-upscaler"
    assert deployments.results[0].current_release is not None
    assert deployments.results[0].current_release.number == 1
    assert deployments.results[0].current_release.model == "acme/esrgan"
    assert deployments.results[1].owner == "acme"
    assert deployments.results[1].name == "text-generator"
    assert deployments.results[1].current_release is not None
    assert deployments.results[1].current_release.number == 2
    assert deployments.results[1].current_release.model == "acme/acme-llama"


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_create_deployment(router, async_flag):
    client = Client(
        api_token="test-token", transport=httpx.MockTransport(router.handler)
    )

    config = {
        "name": "new-deployment",
        "model": "acme/new-model",
        "version": "5c7d5dc6dd8bf75c1acaa8565735e7986bc5b66206b55cca93cb72c9bf15ccaa",
        "hardware": "gpu-t4",
        "min_instances": 1,
        "max_instances": 5,
    }

    if async_flag:
        deployment = await client.deployments.async_create(**config)
    else:
        deployment = client.deployments.create(**config)

    assert router["deployments.create"].called

    assert deployment.owner == "acme"
    assert deployment.name == "new-deployment"
    assert deployment.current_release is not None
    assert deployment.current_release.number == 1
    assert deployment.current_release.model == "acme/new-model"
    assert (
        deployment.current_release.version
        == "5c7d5dc6dd8bf75c1acaa8565735e7986bc5b66206b55cca93cb72c9bf15ccaa"
    )
    assert deployment.current_release.created_by is not None
    assert deployment.current_release.created_by.type == "organization"
    assert deployment.current_release.created_by.username == "acme"
    assert deployment.current_release.created_by.name == "Acme, Inc."
    assert deployment.current_release.configuration.hardware == "gpu-t4"
    assert deployment.current_release.configuration.min_instances == 1
    assert deployment.current_release.configuration.max_instances == 5


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_update_deployment(router, async_flag):
    config = {
        "version": "new-version-id",
        "hardware": "gpu-v100",
        "min_instances": 2,
        "max_instances": 10,
    }

    client = Client(
        api_token="test-token", transport=httpx.MockTransport(router.handler)
    )

    if async_flag:
        updated_deployment = await client.deployments.async_update(
            deployment_owner="acme", deployment_name="image-upscaler", **config
        )
    else:
        updated_deployment = client.deployments.update(
            deployment_owner="acme", deployment_name="image-upscaler", **config
        )

    assert router["deployments.update"].called
    request = router["deployments.update"].calls[0].request
    request_body = json.loads(request.content)
    assert request_body == config

    assert updated_deployment.owner == "acme"
    assert updated_deployment.name == "image-upscaler"
    assert updated_deployment.current_release is not None
    assert updated_deployment.current_release.number == 2
    assert updated_deployment.current_release.model == "acme/esrgan-updated"
    assert updated_deployment.current_release.version == "new-version-id"
    assert updated_deployment.current_release.configuration.hardware == "gpu-v100"
    assert updated_deployment.current_release.configuration.min_instances == 2
    assert updated_deployment.current_release.configuration.max_instances == 10


@respx.mock
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_delete_deployment(router, async_flag):
    client = Client(
        api_token="test-token", transport=httpx.MockTransport(router.handler)
    )

    if async_flag:
        await client.deployments.async_delete(
            deployment_owner="acme", deployment_name="image-upscaler"
        )
    else:
        client.deployments.delete(
            deployment_owner="acme", deployment_name="image-upscaler"
        )

    assert router["deployments.delete"].called
    assert router["deployments.delete"].calls[0].request.method == "DELETE"
    assert (
        router["deployments.delete"].calls[0].request.url
        == "https://api.replicate.com/v1/deployments/acme/image-upscaler"
    )
