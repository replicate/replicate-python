import httpx
import pytest
import respx

from replicate.client import Client

router = respx.Router(base_url="https://api.replicate.com/v1")

router.route(
    method="GET",
    path="/models/replicate/hello-world",
    name="models.get",
).mock(
    return_value=httpx.Response(
        200,
        json={
            "owner": "replicate",
            "name": "hello-world",
            "description": "A tiny model that says hello",
            "visibility": "public",
            "run_count": 1e10,
            "url": "https://replicate.com/replicate/hello-world",
            "created_at": "2022-04-26T19:13:45.911328Z",
            "latest_version": {
                "id": "5c7d5dc6dd8bf75c1acaa8565735e7986bc5b66206b55cca93cb72c9bf15ccaa",
                "cog_version": "0.3.0",
                "openapi_schema": {
                    "openapi": "3.0.2",
                    "info": {"title": "Cog", "version": "0.1.0"},
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
                                        "description": "Text to prefix with 'hello '",
                                    }
                                },
                            },
                            "Output": {"type": "string", "title": "Output"},
                        }
                    },
                },
                "created_at": "2022-04-26T19:29:04.418669Z",
            },
        },
    )
)

router.route(
    method="DELETE",
    path__regex=r"^/models/replicate/hello-world/versions/(?P<id>\w+)/?",
    name="models.versions.delete",
).mock(
    return_value=httpx.Response(
        202,
    )
)


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_version_delete(async_flag):
    client = Client(
        api_token="test-token", transport=httpx.MockTransport(router.handler)
    )

    if async_flag:
        model = await client.models.async_get("replicate/hello-world")
        assert model is not None
        assert model.latest_version is not None

        await model.versions.async_delete(model.latest_version.id)
    else:
        model = client.models.get("replicate/hello-world")
        assert model is not None
        assert model.latest_version is not None

        model.versions.delete(model.latest_version.id)

    assert router["models.get"].called
    assert router["models.versions.delete"].called
