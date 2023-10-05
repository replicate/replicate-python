import httpx
import pytest
import respx

import replicate
from replicate.client import Client
from replicate.exceptions import ReplicateError


@pytest.mark.vcr("run.yaml")
@pytest.mark.asyncio
async def test_run(mock_replicate_api_token):
    version = "a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5"

    input = {
        "prompt": "a studio photo of a rainbow colored corgi",
        "width": 512,
        "height": 512,
        "seed": 42069,
    }

    output = replicate.run(
        f"stability-ai/sdxl:{version}",
        input=input,
    )

    assert output is not None
    assert isinstance(output, list)
    assert len(output) > 0
    assert output[0].startswith("https://")


@pytest.mark.vcr
def test_run_with_invalid_identifier(mock_replicate_api_token):
    with pytest.raises(ReplicateError):
        replicate.run("invalid")


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

    output = client.run(
        "test/example:invalid",
        input={
            "text": "Hello, world!",
        },
    )

    assert output == "Hello, world!"
