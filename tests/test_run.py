import asyncio
import sys

import httpx
import pytest
import respx

import replicate
from replicate.client import Client
from replicate.exceptions import ReplicateError


@pytest.mark.vcr("run.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_run(async_flag, record_mode):
    if record_mode == "none":
        replicate.default_client.poll_interval = 0.001

    version = "a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5"

    input = {
        "prompt": "a studio photo of a rainbow colored corgi",
        "width": 512,
        "height": 512,
        "seed": 42069,
    }

    if async_flag:
        output = await replicate.async_run(
            f"stability-ai/sdxl:{version}",
            input=input,
        )
    else:
        output = replicate.run(
            f"stability-ai/sdxl:{version}",
            input=input,
        )

    assert output is not None
    assert isinstance(output, list)
    assert len(output) > 0
    assert output[0].startswith("https://")


@pytest.mark.vcr("run-concurrently.yaml")
@pytest.mark.asyncio
@pytest.mark.skipif(
    sys.version_info < (3, 11), reason="asyncio.TaskGroup requires Python 3.11"
)
async def test_run_concurrently(mock_replicate_api_token, record_mode):
    if record_mode == "none":
        replicate.default_client.poll_interval = 0.001

    # https://replicate.com/stability-ai/sdxl
    model_version = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"

    prompts = [
        f"A chariot pulled by a team of {count} rainbow unicorns"
        for count in ["two", "four", "six", "eight"]
    ]

    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(replicate.async_run(model_version, input={"prompt": prompt}))
            for prompt in prompts
        ]

    results = await asyncio.gather(*tasks)
    assert len(results) == len(prompts)
    assert all(isinstance(result, list) for result in results)
    assert all(len(result) > 0 for result in results)


@pytest.mark.vcr("run.yaml")
@pytest.mark.asyncio
async def test_run_with_invalid_identifier(mock_replicate_api_token):
    with pytest.raises(ReplicateError):
        replicate.run("invalid")


@pytest.mark.vcr("run.yaml")
@pytest.mark.asyncio
async def test_run_without_token():
    with pytest.raises(ReplicateError) as excinfo:
        version = "01d17250ffa554142c31e96e7dc0e4d313d62006e15684062c84d2eadb13bf11"

        input = {
            "prompt": "write a haiku about camelids",
        }

        replicate.run(
            f"meta/codellama-13b:{version}",
            input=input,
        )

    assert "You did not pass an authentication token" in str(excinfo.value)


@pytest.mark.asyncio
async def test_run_version_with_invalid_cog_version(mock_replicate_api_token):
    def prediction_with_status(status: str) -> dict:
        return {
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2023-10-05T12:00:00.000000Z",
            "source": "api",
            "status": status,
            "input": {"text": "world"},
            "output": "Hello, world!" if status == "succeeded" else None,
            "error": None,
            "logs": "",
        }

    router = respx.Router(base_url="https://api.replicate.com/v1")
    router.route(method="POST", path="/predictions").mock(
        return_value=httpx.Response(
            201,
            json=prediction_with_status("running"),
        )
    )
    router.route(method="GET", path="/predictions/p1").mock(
        return_value=httpx.Response(
            200,
            json=prediction_with_status("succeeded"),
        )
    )
    router.route(
        method="GET",
        path="/models/test/example/versions/invalid",
    ).mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "f2d6b24e6002f25f77ae89c2b0a5987daa6d0bf751b858b94b8416e8542434d1",
                "created_at": "2022-03-16T00:35:56.210272Z",
                "cog_version": "dev",
                "openapi_schema": {
                    "openapi": "3.0.2",
                    "info": {"title": "Cog", "version": "0.1.0"},
                    "paths": {},
                    "components": {
                        "schemas": {
                            "Input": {
                                "type": "object",
                                "title": "Input",
                                "required": ["text"],
                                "properties": {
                                    "text": {
                                        "type": "string",
                                        "title": "Text",
                                        "x-order": 0,
                                        "description": "The text input",
                                    },
                                },
                            },
                            "Output": {
                                "type": "string",
                                "title": "Output",
                            },
                        }
                    },
                },
            },
        )
    )
    router.route(host="api.replicate.com").pass_through()

    client = Client(
        api_token="test-token", transport=httpx.MockTransport(router.handler)
    )
    client.poll_interval = 0.001

    output = client.run(
        "test/example:invalid",
        input={
            "text": "Hello, world!",
        },
    )

    assert output == "Hello, world!"
