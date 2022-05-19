import responses
from replicate.__about__ import __version__
from replicate.client import Client
from responses import matchers


@responses.activate
def test_client_sets_authorization_token_and_user_agent_headers():
    client = Client(api_token="abc123")
    model = client.models.get("test/model")

    responses.get(
        "https://api.replicate.com/v1/models/test/model/versions",
        match=[
            matchers.header_matcher({"Authorization": "Token abc123"}),
            matchers.header_matcher({"User-Agent": f"replicate-python@{__version__}"}),
        ],
        json={"results": []},
    )

    model.versions.list()
