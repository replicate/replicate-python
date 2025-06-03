import json
import os
from enum import Enum
from pathlib import Path
from typing import Literal, Union

import httpx
import pytest
import respx

import replicate
from replicate.use import get_path_url


class ClientMode(str, Enum):
    DEFAULT = "default"
    ASYNC = "async"


# Allow use() to be called in test context
os.environ["REPLICATE_ALWAYS_ALLOW_USE"] = "1"
os.environ["REPLICATE_POLL_INTERVAL"] = "0"


def _deep_merge(base, override):
    if override is None:
        return base

    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def create_mock_version(version_overrides=None, version_id="xyz123"):
    default_version = {
        "id": version_id,
        "created_at": "2024-01-01T00:00:00Z",
        "cog_version": "0.8.0",
        "openapi_schema": {
            "openapi": "3.0.2",
            "info": {"title": "Cog", "version": "0.1.0"},
            "paths": {
                "/": {
                    "post": {
                        "summary": "Make a prediction",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/PredictionRequest"
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/PredictionResponse"
                                        }
                                    }
                                }
                            }
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "Input": {
                        "type": "object",
                        "properties": {"prompt": {"type": "string", "title": "Prompt"}},
                        "required": ["prompt"],
                    },
                    "Output": {"type": "string", "title": "Output"},
                }
            },
        },
    }

    return _deep_merge(default_version, version_overrides)


def create_mock_prediction(
    prediction_overrides=None, prediction_id="pred123", uses_versionless_api=None
):
    default_prediction = {
        "id": prediction_id,
        "model": "acme/hotdog-detector",
        "version": "hidden"
        if uses_versionless_api in ("notfound", "empty")
        else "xyz123",
        "urls": {
            "get": f"https://api.replicate.com/v1/predictions/{prediction_id}",
            "cancel": f"https://api.replicate.com/v1/predictions/{prediction_id}/cancel",
        },
        "created_at": "2024-01-01T00:00:00Z",
        "source": "api",
        "status": "processing",
        "input": {"prompt": "hello world"},
        "output": None,
        "error": None,
        "logs": "Starting prediction...",
    }

    return _deep_merge(default_prediction, prediction_overrides)


def mock_model_endpoints(
    versions=None,
    *,
    # This is a workaround while we have a bug in the api
    uses_versionless_api: Union[Literal["notfound"], Literal["empty"], None] = None,
):
    if versions is None:
        versions = [create_mock_version()]

    # Get the latest version (first in list) for the model endpoint
    # For empty case, we provide the version in latest_version but return empty versions list
    latest_version = versions[0] if versions else None
    respx.get("https://api.replicate.com/v1/models/acme/hotdog-detector").mock(
        return_value=httpx.Response(
            200,
            json={
                "url": "https://replicate.com/acme/hotdog-detector",
                "owner": "acme",
                "name": "hotdog-detector",
                "description": "A model to detect hotdogs",
                "visibility": "public",
                "github_url": "https://github.com/acme/hotdog-detector",
                "paper_url": None,
                "license_url": None,
                "run_count": 42,
                "cover_image_url": None,
                "default_example": None,
                # This one is a bit weird due to a bug in procedures that currently return an empty
                # version list from the `model.versions.list` endpoint instead of 404ing
                "latest_version": latest_version,
            },
        )
    )

    versions_results = versions
    if uses_versionless_api == "empty":
        versions_results = []

    # Mock the versions list endpoint
    if uses_versionless_api == "notfound":
        respx.get(
            "https://api.replicate.com/v1/models/acme/hotdog-detector/versions"
        ).mock(return_value=httpx.Response(404, json={"detail": "Not found"}))
    else:
        respx.get(
            "https://api.replicate.com/v1/models/acme/hotdog-detector/versions"
        ).mock(return_value=httpx.Response(200, json={"results": versions_results}))

    # Mock specific version endpoints
    for version_obj in versions_results:
        if uses_versionless_api == "notfound":
            respx.get(
                f"https://api.replicate.com/v1/models/acme/hotdog-detector/versions/{version_obj['id']}"
            ).mock(return_value=httpx.Response(404, json={}))
        else:
            respx.get(
                f"https://api.replicate.com/v1/models/acme/hotdog-detector/versions/{version_obj['id']}"
            ).mock(return_value=httpx.Response(200, json=version_obj))


def mock_prediction_endpoints(
    predictions=None,
    *,
    uses_versionless_api=None,
):
    if predictions is None:
        # Create default two-step prediction flow (processing -> succeeded)
        predictions = [
            create_mock_prediction(
                {
                    "status": "processing",
                    "output": None,
                    "logs": "",
                },
                uses_versionless_api=uses_versionless_api,
            ),
            create_mock_prediction(
                {
                    "status": "succeeded",
                    "output": "not hotdog",
                    "logs": "Starting prediction...\nPrediction completed.",
                },
                uses_versionless_api=uses_versionless_api,
            ),
        ]

    initial_prediction = predictions[0]
    if uses_versionless_api in ("notfound", "empty"):
        respx.post(
            "https://api.replicate.com/v1/models/acme/hotdog-detector/predictions"
        ).mock(return_value=httpx.Response(201, json=initial_prediction))
    else:
        respx.post("https://api.replicate.com/v1/predictions").mock(
            return_value=httpx.Response(201, json=initial_prediction)
        )

    # Mock the prediction polling endpoint
    prediction_id = initial_prediction["id"]
    respx.get(f"https://api.replicate.com/v1/predictions/{prediction_id}").mock(
        side_effect=[httpx.Response(200, json=response) for response in predictions]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use(client_mode):
    mock_model_endpoints()
    mock_prediction_endpoints()

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is the completed output from the prediction request
    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_with_version_identifier(client_mode):
    mock_model_endpoints()
    mock_prediction_endpoints()

    # Call use with version identifier "acme/hotdog-detector:xyz123"
    hotdog_detector = replicate.use("acme/hotdog-detector:xyz123")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is the completed output from the prediction request
    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_with_function_ref(client_mode):
    mock_model_endpoints()
    mock_prediction_endpoints()

    class HotdogDetector:
        name = "acme/hotdog-detector:xyz123"

        def __call__(self, prompt: str) -> str: ...

    hotdog_detector = replicate.use(HotdogDetector())

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is the completed output from the prediction request
    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_versionless_empty_versions_list(client_mode):
    mock_model_endpoints(uses_versionless_api="empty")
    mock_prediction_endpoints(uses_versionless_api="empty")

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is the completed output from the prediction request
    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_versionless_404_versions_list(client_mode):
    mock_model_endpoints(uses_versionless_api="notfound")
    mock_prediction_endpoints(uses_versionless_api="notfound")

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is the completed output from the prediction request
    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_function_create_method(client_mode):
    mock_model_endpoints()
    mock_prediction_endpoints()

    # Call use and then create method
    hotdog_detector = replicate.use("acme/hotdog-detector")
    run = hotdog_detector.create(prompt="hello world")

    # Assert that run is a Run object with a prediction
    from replicate.use import Run

    assert isinstance(run, Run)
    assert run.prediction.id == "pred123"
    assert run.prediction.status == "processing"
    assert run.prediction.input == {"prompt": "hello world"}


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_concatenate_iterator_output(client_mode):
    mock_model_endpoints(
        versions=[
            create_mock_version(
                {
                    "openapi_schema": {
                        "components": {
                            "schemas": {
                                "Output": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "x-cog-array-type": "iterator",
                                    "x-cog-array-display": "concatenate",
                                }
                            }
                        }
                    }
                }
            )
        ]
    )
    mock_prediction_endpoints(
        predictions=[
            create_mock_prediction(),
            create_mock_prediction(
                {"status": "succeeded", "output": ["Hello", " ", "world", "!"]}
            ),
        ]
    )

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is an OutputIterator that concatenates when converted to string
    from replicate.use import OutputIterator

    assert isinstance(output, OutputIterator)
    assert str(output) == "Hello world!"

    # Also test that it's iterable
    output_list = list(output)
    assert output_list == ["Hello", " ", "world", "!"]

    # Test that concatenate OutputIterators are stringified when passed to create()
    # Set up a mock for the prediction creation to capture the request
    request_body = None

    def capture_request(request):
        nonlocal request_body
        request_body = request.read()
        return httpx.Response(
            201,
            json={
                "id": "pred456",
                "model": "acme/hotdog-detector",
                "version": "xyz123",
                "urls": {
                    "get": "https://api.replicate.com/v1/predictions/pred456",
                    "cancel": "https://api.replicate.com/v1/predictions/pred456/cancel",
                },
                "created_at": "2024-01-01T00:00:00Z",
                "source": "api",
                "status": "processing",
                "input": {"text_input": "Hello world!"},
                "output": None,
                "error": None,
                "logs": "",
            },
        )

    respx.post("https://api.replicate.com/v1/predictions").mock(
        side_effect=capture_request
    )

    # Pass the OutputIterator as input to create()
    hotdog_detector.create(text_input=output)

    # Verify the request body contains the stringified version
    parsed_body = json.loads(request_body)
    assert parsed_body["input"]["text_input"] == "Hello world!"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_list_of_strings_output(client_mode):
    mock_model_endpoints(
        versions=[
            create_mock_version(
                {
                    "openapi_schema": {
                        "components": {
                            "schemas": {
                                "Output": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                }
                            }
                        }
                    }
                }
            )
        ]
    )
    mock_prediction_endpoints(
        predictions=[
            create_mock_prediction(),
            create_mock_prediction(
                {"status": "succeeded", "output": ["hello", "world", "test"]}
            ),
        ]
    )

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is returned as a list
    assert output == ["hello", "world", "test"]


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_iterator_of_strings_output(client_mode):
    mock_model_endpoints(
        versions=[
            create_mock_version(
                {
                    "openapi_schema": {
                        "components": {
                            "schemas": {
                                "Output": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "x-cog-array-type": "iterator",
                                }
                            }
                        }
                    }
                }
            )
        ]
    )
    mock_prediction_endpoints(
        predictions=[
            create_mock_prediction(),
            create_mock_prediction(
                {"status": "succeeded", "output": ["hello", "world", "test"]}
            ),
        ]
    )

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is returned as an OutputIterator
    from replicate.use import OutputIterator

    assert isinstance(output, OutputIterator)
    # Convert to list to check contents
    output_list = list(output)
    assert output_list == ["hello", "world", "test"]


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_path_output(client_mode):
    mock_model_endpoints(
        versions=[
            create_mock_version(
                {
                    "openapi_schema": {
                        "components": {
                            "schemas": {
                                "Output": {
                                    "type": "string",
                                    "format": "uri",
                                }
                            }
                        }
                    }
                }
            )
        ]
    )
    mock_prediction_endpoints(
        predictions=[
            create_mock_prediction(),
            create_mock_prediction(
                {"status": "succeeded", "output": "https://example.com/output.jpg"}
            ),
        ]
    )

    # Mock the file download
    respx.get("https://example.com/output.jpg").mock(
        return_value=httpx.Response(200, content=b"fake image data")
    )

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    assert isinstance(output, os.PathLike)
    assert get_path_url(output) == "https://example.com/output.jpg"
    assert os.path.exists(output)
    assert open(output, "rb").read() == b"fake image data"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_list_of_paths_output(client_mode):
    mock_model_endpoints(
        versions=[
            create_mock_version(
                {
                    "openapi_schema": {
                        "components": {
                            "schemas": {
                                "Output": {
                                    "type": "array",
                                    "items": {"type": "string", "format": "uri"},
                                }
                            }
                        }
                    }
                }
            )
        ]
    )
    mock_prediction_endpoints(
        predictions=[
            create_mock_prediction(),
            create_mock_prediction(
                {
                    "status": "succeeded",
                    "output": [
                        "https://example.com/output1.jpg",
                        "https://example.com/output2.jpg",
                    ],
                }
            ),
        ]
    )

    # Mock the file downloads
    respx.get("https://example.com/output1.jpg").mock(
        return_value=httpx.Response(200, content=b"fake image 1 data")
    )
    respx.get("https://example.com/output2.jpg").mock(
        return_value=httpx.Response(200, content=b"fake image 2 data")
    )

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    assert isinstance(output, list)
    assert len(output) == 2

    assert all(isinstance(path, os.PathLike) for path in output)
    assert get_path_url(output[0]) == "https://example.com/output1.jpg"
    assert get_path_url(output[1]) == "https://example.com/output2.jpg"

    assert all(os.path.exists(path) for path in output)
    assert open(output[0], "rb").read() == b"fake image 1 data"
    assert open(output[1], "rb").read() == b"fake image 2 data"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_iterator_of_paths_output(client_mode):
    mock_model_endpoints(
        versions=[
            create_mock_version(
                {
                    "openapi_schema": {
                        "components": {
                            "schemas": {
                                "Output": {
                                    "type": "array",
                                    "items": {"type": "string", "format": "uri"},
                                    "x-cog-array-type": "iterator",
                                }
                            }
                        }
                    }
                }
            )
        ]
    )
    mock_prediction_endpoints(
        predictions=[
            create_mock_prediction(),
            create_mock_prediction(
                {
                    "status": "succeeded",
                    "output": [
                        "https://example.com/output1.jpg",
                        "https://example.com/output2.jpg",
                    ],
                }
            ),
        ]
    )

    # Mock the file downloads
    respx.get("https://example.com/output1.jpg").mock(
        return_value=httpx.Response(200, content=b"fake image 1 data")
    )
    respx.get("https://example.com/output2.jpg").mock(
        return_value=httpx.Response(200, content=b"fake image 2 data")
    )

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is returned as an OutputIterator of Path objects
    from replicate.use import OutputIterator

    assert isinstance(output, OutputIterator)
    # Convert to list to check contents
    output_list = list(output)
    assert len(output_list) == 2
    assert all(isinstance(path, os.PathLike) for path in output_list)
    assert get_path_url(output_list[0]) == "https://example.com/output1.jpg"
    assert get_path_url(output_list[1]) == "https://example.com/output2.jpg"
    assert all(os.path.exists(path) for path in output_list)
    assert open(output_list[0], "rb").read() == b"fake image 1 data"
    assert open(output_list[1], "rb").read() == b"fake image 2 data"


def test_get_path_url_with_urlpath():
    """Test get_path_url returns the URL for PathProxy instances."""
    from replicate.use import URLPath, get_path_url

    url = "https://example.com/test.jpg"
    path_proxy = URLPath(url)

    result = get_path_url(path_proxy)
    assert result == url


def test_get_path_url_with_regular_path():
    """Test get_path_url returns None for regular Path instances."""
    from replicate.use import get_path_url

    regular_path = Path("test.txt")

    result = get_path_url(regular_path)
    assert result is None


def test_get_path_url_with_object_without_target():
    """Test get_path_url returns None for objects without __replicate_target__."""
    from replicate.use import get_path_url

    # Test with a string
    result = get_path_url("not a path")
    assert result is None

    # Test with a dict
    result = get_path_url({"key": "value"})
    assert result is None

    # Test with None
    result = get_path_url(None)
    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_pathproxy_input_conversion(client_mode):
    mock_model_endpoints()

    # Mock the file download - this should NOT be called
    file_request_mock = respx.get("https://example.com/input.jpg").mock(
        return_value=httpx.Response(200, content=b"fake input image data")
    )

    # Create a PathProxy instance
    from replicate.use import URLPath

    urlpath = URLPath("https://example.com/input.jpg")

    # Set up a mock for the prediction creation to capture the request
    request_body = None

    def capture_request(request):
        nonlocal request_body
        request_body = request.read()
        return httpx.Response(
            201,
            json={
                "id": "pred789",
                "model": "acme/hotdog-detector",
                "version": "xyz123",
                "urls": {
                    "get": "https://api.replicate.com/v1/predictions/pred789",
                    "cancel": "https://api.replicate.com/v1/predictions/pred789/cancel",
                },
                "created_at": "2024-01-01T00:00:00Z",
                "source": "api",
                "status": "processing",
                "input": {"image": "https://example.com/input.jpg"},
                "output": None,
                "error": None,
                "logs": "",
            },
        )

    respx.post("https://api.replicate.com/v1/predictions").mock(
        side_effect=capture_request
    )

    # Call use and create with URLPath
    hotdog_detector = replicate.use("acme/hotdog-detector")
    hotdog_detector.create(image=urlpath)

    # Verify the request body contains the URL, not the downloaded file
    assert request_body
    parsed_body = json.loads(request_body)
    assert parsed_body["input"]["image"] == "https://example.com/input.jpg"

    # Assert that the file was never downloaded
    assert file_request_mock.call_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_function_logs_method(client_mode):
    mock_model_endpoints()
    mock_prediction_endpoints(predictions=[create_mock_prediction()])

    # Call use and then create method
    hotdog_detector = replicate.use("acme/hotdog-detector")
    run = hotdog_detector.create(prompt="hello world")

    # Call logs method to get current logs
    logs = run.logs()

    # Assert that logs returns the current log value
    assert logs == "Starting prediction..."


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_function_logs_method_polling(client_mode):
    mock_model_endpoints()

    # Mock prediction endpoints with updated logs on polling
    polling_responses = [
        create_mock_prediction(
            {
                "logs": "Starting prediction...",
            }
        ),
        create_mock_prediction(
            {
                "logs": "Starting prediction...\nProcessing input...",
            }
        ),
    ]

    mock_prediction_endpoints(predictions=polling_responses)

    # Call use and then create method
    hotdog_detector = replicate.use("acme/hotdog-detector")
    run = hotdog_detector.create(prompt="hello world")

    # Call logs method initially
    initial_logs = run.logs()
    assert initial_logs == "Starting prediction..."

    # Call logs method again to get updated logs (simulates polling)
    updated_logs = run.logs()
    assert updated_logs == "Starting prediction...\nProcessing input..."


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_object_output_with_file_properties(client_mode):
    mock_model_endpoints(
        versions=[
            create_mock_version(
                {
                    "openapi_schema": {
                        "components": {
                            "schemas": {
                                "Output": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"},
                                        "image": {
                                            "type": "string",
                                            "format": "uri",
                                        },
                                        "count": {"type": "integer"},
                                    },
                                }
                            }
                        }
                    }
                }
            )
        ]
    )
    mock_prediction_endpoints(
        predictions=[
            create_mock_prediction(),
            create_mock_prediction(
                {
                    "status": "succeeded",
                    "output": {
                        "text": "Generated text",
                        "image": "https://example.com/generated.png",
                        "count": 42,
                    },
                }
            ),
        ]
    )

    # Mock the file download
    respx.get("https://example.com/generated.png").mock(
        return_value=httpx.Response(200, content=b"fake png data")
    )

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    assert isinstance(output, dict)
    assert output["text"] == "Generated text"
    assert output["count"] == 42
    assert isinstance(output["image"], os.PathLike)
    assert get_path_url(output["image"]) == "https://example.com/generated.png"
    assert os.path.exists(output["image"])
    assert open(output["image"], "rb").read() == b"fake png data"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT])
@respx.mock
async def test_use_object_output_with_file_list_property(client_mode):
    mock_model_endpoints(
        versions=[
            create_mock_version(
                {
                    "openapi_schema": {
                        "components": {
                            "schemas": {
                                "Output": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"},
                                        "images": {
                                            "type": "array",
                                            "items": {
                                                "type": "string",
                                                "format": "uri",
                                            },
                                        },
                                    },
                                }
                            }
                        }
                    }
                }
            )
        ]
    )
    mock_prediction_endpoints(
        predictions=[
            create_mock_prediction(),
            create_mock_prediction(
                {
                    "status": "succeeded",
                    "output": {
                        "text": "Generated text",
                        "images": [
                            "https://example.com/image1.png",
                            "https://example.com/image2.png",
                        ],
                    },
                }
            ),
        ]
    )

    # Mock the file downloads
    respx.get("https://example.com/image1.png").mock(
        return_value=httpx.Response(200, content=b"fake png 1 data")
    )
    respx.get("https://example.com/image2.png").mock(
        return_value=httpx.Response(200, content=b"fake png 2 data")
    )

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    assert isinstance(output, dict)
    assert output["text"] == "Generated text"
    assert isinstance(output["images"], list)
    assert len(output["images"]) == 2
    assert all(isinstance(path, os.PathLike) for path in output["images"])
    assert get_path_url(output["images"][0]) == "https://example.com/image1.png"
    assert get_path_url(output["images"][1]) == "https://example.com/image2.png"
    assert all(os.path.exists(path) for path in output["images"])
    assert open(output["images"][0], "rb").read() == b"fake png 1 data"
    assert open(output["images"][1], "rb").read() == b"fake png 2 data"
