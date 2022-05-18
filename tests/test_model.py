import responses

from replicate.client import Client


@responses.activate
def test_versions():
    client = Client(api_token="abc123")

    model = client.models.get("test/model")

    responses.get(
        "https://api.replicate.com/v1/models/test/model/versions",
        json={
            "results": [
                {
                    "id": "v1",
                    "created_at": "2022-04-26T19:29:04.418669Z",
                    "cog_version": "0.3.0",
                    "openapi_schema": {},
                },
                {
                    "id": "v2",
                    "created_at": "2022-03-21T13:01:04.418669Z",
                    "cog_version": "0.3.0",
                    "openapi_schema": {},
                },
            ]
        },
    )

    versions = model.versions.list()
    assert len(versions) == 2
    assert versions[0].id == "v1"
    assert versions[1].id == "v2"
