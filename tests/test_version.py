from collections.abc import Iterable

import pytest
import responses
from replicate.exceptions import ModelError
from responses import matchers

from .factories import (
    create_version,
    create_version_with_iterator_output,
    create_version_with_iterator_output_backwards_compatibility_0_3_8,
    create_version_with_list_output,
)


@responses.activate
def test_predict():
    version = create_version()

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

    assert version.predict(text="world") == "hello world"


@responses.activate
def test_predict_with_iterator():
    version = create_version_with_iterator_output()
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

    output = version.predict(text="world")
    assert isinstance(output, Iterable)
    assert list(output) == ["hello world"]


@responses.activate
def test_predict_with_list():
    version = create_version_with_list_output()
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

    output = version.predict(text="world")
    assert isinstance(output, list)
    assert output == ["hello world"]


@responses.activate
def test_predict_with_iterator_backwards_compatibility_cog_0_3_8():
    version = create_version_with_iterator_output_backwards_compatibility_0_3_8()
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

    output = version.predict(text="world")
    assert isinstance(output, Iterable)
    assert list(output) == ["hello world"]


@responses.activate
def test_predict_with_iterator_with_failed_prediction():
    version = create_version_with_iterator_output()
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

    output = version.predict(text="world")
    assert isinstance(output, Iterable)
    with pytest.raises(ModelError) as excinfo:
        list(output)
    assert "it broke" in str(excinfo.value)
