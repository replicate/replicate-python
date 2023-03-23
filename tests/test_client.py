from collections.abc import Iterable

import pytest
import responses
from responses import matchers

from replicate.__about__ import __version__
from replicate.client import Client
from replicate.exceptions import ModelError

from .factories import (
    mock_version_get,
    mock_version_get_with_iterator_output,
    mock_version_get_with_iterator_output_backwards_compatibility_0_3_8,
    mock_version_get_with_list_output,
)


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


@responses.activate
def test_run():
    mock_version_get(owner="test", model="model", version="v1")
    responses.post(
        "https://api.replicate.com/v1/predictions",
        match=[
            matchers.json_params_matcher({"version": "v1", "input": {"text": "world"}})
        ],
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "processing",
            "input": {"text": "world"},
            "output": None,
            "error": None,
            "logs": "",
        },
    )
    responses.get(
        "https://api.replicate.com/v1/predictions/p1",
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "succeeded",
            "input": {"text": "world"},
            "output": "hello world",
            "error": None,
            "logs": "",
        },
    )

    client = Client(api_token="abc123")
    assert client.run("test/model:v1", input={"text": "world"}) == "hello world"


@responses.activate
def test_run_with_iterator():
    mock_version_get_with_iterator_output(owner="test", model="model", version="v1")
    responses.post(
        "https://api.replicate.com/v1/predictions",
        match=[
            matchers.json_params_matcher({"version": "v1", "input": {"text": "world"}})
        ],
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "processing",
            "input": {"text": "world"},
            "output": None,
            "error": None,
            "logs": "",
        },
    )
    responses.get(
        "https://api.replicate.com/v1/predictions/p1",
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "succeeded",
            "input": {"text": "world"},
            "output": ["hello world"],
            "error": None,
            "logs": "",
        },
    )

    client = Client(api_token="abc123")
    output = client.run("test/model:v1", input={"text": "world"})
    assert isinstance(output, Iterable)
    assert list(output) == ["hello world"]


@responses.activate
def test_run_with_list():
    mock_version_get_with_list_output(owner="test", model="model", version="v1")
    responses.post(
        "https://api.replicate.com/v1/predictions",
        match=[
            matchers.json_params_matcher({"version": "v1", "input": {"text": "world"}})
        ],
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "processing",
            "input": {"text": "world"},
            "output": None,
            "error": None,
            "logs": "",
        },
    )
    responses.get(
        "https://api.replicate.com/v1/predictions/p1",
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "succeeded",
            "input": {"text": "world"},
            "output": ["hello world"],
            "error": None,
            "logs": "",
        },
    )

    client = Client(api_token="abc123")
    output = client.run("test/model:v1", input={"text": "world"})
    assert isinstance(output, list)
    assert output == ["hello world"]


@responses.activate
def test_run_with_iterator_backwards_compatibility_cog_0_3_8():
    mock_version_get_with_iterator_output_backwards_compatibility_0_3_8(
        owner="test", model="model", version="v1"
    )
    responses.post(
        "https://api.replicate.com/v1/predictions",
        match=[
            matchers.json_params_matcher({"version": "v1", "input": {"text": "world"}})
        ],
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "processing",
            "input": {"text": "world"},
            "output": None,
            "error": None,
            "logs": "",
        },
    )
    responses.get(
        "https://api.replicate.com/v1/predictions/p1",
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "succeeded",
            "input": {"text": "world"},
            "output": ["hello world"],
            "error": None,
            "logs": "",
        },
    )

    client = Client(api_token="abc123")
    output = client.run("test/model:v1", input={"text": "world"})
    assert isinstance(output, Iterable)
    assert list(output) == ["hello world"]


@responses.activate
def test_predict_with_iterator_with_failed_prediction():
    mock_version_get_with_iterator_output(owner="test", model="model", version="v1")
    responses.post(
        "https://api.replicate.com/v1/predictions",
        match=[
            matchers.json_params_matcher({"version": "v1", "input": {"text": "world"}})
        ],
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "processing",
            "input": {"text": "world"},
            "output": None,
            "error": None,
            "logs": "",
        },
    )
    responses.get(
        "https://api.replicate.com/v1/predictions/p1",
        json={
            "id": "p1",
            "version": "v1",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/p1",
                "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
            },
            "created_at": "2022-04-26T20:00:40.658234Z",
            "completed_at": "2022-04-26T20:02:27.648305Z",
            "source": "api",
            "status": "failed",
            "input": {"text": "world"},
            "output": None,
            "error": "it broke",
            "logs": "",
        },
    )

    client = Client(api_token="abc123")
    output = client.run("test/model:v1", input={"text": "world"})
    assert isinstance(output, Iterable)
    with pytest.raises(ModelError) as excinfo:
        list(output)
    assert "it broke" in str(excinfo.value)
