import json
import os
from pathlib import Path

import httpx
import pytest
import respx

import replicate

# Allow use() to be called in test context
os.environ["REPLICATE_ALWAYS_ALLOW_USE"] = "1"


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


def mock_model_endpoints(
    version_overrides=None,
    *,
    uses_versionless_api=False,
    has_no_versions=False,
):
    """Mock the model and versions endpoints."""
    # Validate arguments
    if version_overrides and has_no_versions:
        raise ValueError(
            "Cannot specify both 'version_overrides' and 'has_no_versions=True'"
        )

    # Create default version
    default_version = {
        "id": "xyz123",
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

    version = _deep_merge(default_version, version_overrides)
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
                "latest_version": None
                if has_no_versions and not uses_versionless_api
                else version,
            },
        )
    )

    # Determine versions list
    if uses_versionless_api or has_no_versions:
        versions_results = []
    else:
        versions_results = [version] if version else []

    # Mock the versions list endpoint
    if uses_versionless_api:
        respx.get(
            "https://api.replicate.com/v1/models/acme/hotdog-detector/versions"
        ).mock(return_value=httpx.Response(404, json={"detail": "Not found"}))
    else:
        respx.get(
            "https://api.replicate.com/v1/models/acme/hotdog-detector/versions"
        ).mock(return_value=httpx.Response(200, json={"results": versions_results}))

    # Mock specific version endpoints
    for version_obj in versions_results:
        if uses_versionless_api:
            respx.get(
                f"https://api.replicate.com/v1/models/acme/hotdog-detector/versions/{version_obj['id']}"
            ).mock(return_value=httpx.Response(404, json={}))
        else:
            respx.get(
                f"https://api.replicate.com/v1/models/acme/hotdog-detector/versions/{version_obj['id']}"
            ).mock(return_value=httpx.Response(200, json=version_obj))


def mock_prediction_endpoints(
    output_data="not hotdog",
    *,
    uses_versionless_api=False,
    polling_responses=None,
):
    """Mock the prediction creation and polling endpoints."""

    if polling_responses is None:
        polling_responses = [
            {
                "id": "pred123",
                "model": "acme/hotdog-detector",
                "version": "hidden" if uses_versionless_api else "xyz123",
                "urls": {
                    "get": "https://api.replicate.com/v1/predictions/pred123",
                    "cancel": "https://api.replicate.com/v1/predictions/pred123/cancel",
                },
                "created_at": "2024-01-01T00:00:00Z",
                "source": "api",
                "status": "processing",
                "input": {"prompt": "hello world"},
                "output": None,
                "error": None,
                "logs": "Starting prediction...",
            },
            {
                "id": "pred123",
                "model": "acme/hotdog-detector",
                "version": "hidden" if uses_versionless_api else "xyz123",
                "urls": {
                    "get": "https://api.replicate.com/v1/predictions/pred123",
                    "cancel": "https://api.replicate.com/v1/predictions/pred123/cancel",
                },
                "created_at": "2024-01-01T00:00:00Z",
                "source": "api",
                "status": "succeeded",
                "input": {"prompt": "hello world"},
                "output": output_data,
                "error": None,
                "logs": "Starting prediction...\nPrediction completed.",
            },
        ]

    # Mock the prediction creation endpoint
    if uses_versionless_api:
        respx.post(
            "https://api.replicate.com/v1/models/acme/hotdog-detector/predictions"
        ).mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": "pred123",
                    "model": "acme/hotdog-detector",
                    "version": "hidden",
                    "urls": {
                        "get": "https://api.replicate.com/v1/predictions/pred123",
                        "cancel": "https://api.replicate.com/v1/predictions/pred123/cancel",
                    },
                    "created_at": "2024-01-01T00:00:00Z",
                    "source": "api",
                    "status": "processing",
                    "input": {"prompt": "hello world"},
                    "output": None,
                    "error": None,
                    "logs": "",
                },
            )
        )
    else:
        respx.post("https://api.replicate.com/v1/predictions").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": "pred123",
                    "model": "acme/hotdog-detector",
                    "version": "xyz123",
                    "urls": {
                        "get": "https://api.replicate.com/v1/predictions/pred123",
                        "cancel": "https://api.replicate.com/v1/predictions/pred123/cancel",
                    },
                    "created_at": "2024-01-01T00:00:00Z",
                    "source": "api",
                    "status": "processing",
                    "input": {"prompt": "hello world"},
                    "output": None,
                    "error": None,
                    "logs": "",
                },
            )
        )

    # Mock the prediction polling endpoint
    respx.get("https://api.replicate.com/v1/predictions/pred123").mock(
        side_effect=[
            httpx.Response(200, json=response) for response in polling_responses
        ]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use(use_async_client):
    mock_model_endpoints()
    mock_prediction_endpoints()

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is the completed output from the prediction request
    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_with_version_identifier(use_async_client):
    mock_model_endpoints()
    mock_prediction_endpoints()

    # Call use with version identifier "acme/hotdog-detector:xyz123"
    hotdog_detector = replicate.use("acme/hotdog-detector:xyz123")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is the completed output from the prediction request
    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_versionless_empty_versions_list(use_async_client):
    mock_model_endpoints(has_no_versions=True, uses_versionless_api=True)
    mock_prediction_endpoints(uses_versionless_api=True)

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is the completed output from the prediction request
    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_versionless_404_versions_list(use_async_client):
    mock_model_endpoints(uses_versionless_api=True)
    mock_prediction_endpoints(uses_versionless_api=True)

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is the completed output from the prediction request
    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_function_create_method(use_async_client):
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
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_concatenate_iterator_output(use_async_client):
    mock_model_endpoints(
        version_overrides={
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Output": {
                            "type": "array",
                            "items": {"type": "string"},
                            "x-cog-array-type": "iterator",
                            "x-cog-array-display": "concatenate",
                            "title": "Output",
                        }
                    }
                }
            }
        }
    )
    mock_prediction_endpoints(output_data=["Hello", " ", "world", "!"])

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
    run = hotdog_detector.create(text_input=output)

    # Verify the request body contains the stringified version
    parsed_body = json.loads(request_body)
    assert parsed_body["input"]["text_input"] == "Hello world!"


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_list_of_strings_output(use_async_client):
    mock_model_endpoints(
        version_overrides={
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Output": {
                            "type": "array",
                            "items": {"type": "string"},
                            "title": "Output",
                        }
                    }
                }
            }
        }
    )
    mock_prediction_endpoints(output_data=["hello", "world", "test"])

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is returned as a list
    assert output == ["hello", "world", "test"]


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_iterator_of_strings_output(use_async_client):
    mock_model_endpoints(
        version_overrides={
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Output": {
                            "type": "array",
                            "items": {"type": "string"},
                            "x-cog-array-type": "iterator",
                            "title": "Output",
                        }
                    }
                }
            }
        }
    )
    mock_prediction_endpoints(output_data=["hello", "world", "test"])

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
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_path_output(use_async_client):
    mock_model_endpoints(
        version_overrides={
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Output": {"type": "string", "format": "uri", "title": "Output"}
                    }
                }
            }
        }
    )
    mock_prediction_endpoints(output_data="https://example.com/output.jpg")

    # Mock the file download
    respx.get("https://example.com/output.jpg").mock(
        return_value=httpx.Response(200, content=b"fake image data")
    )

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    assert isinstance(output, Path)
    assert output.exists()
    assert output.read_bytes() == b"fake image data"


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_list_of_paths_output(use_async_client):
    mock_model_endpoints(
        version_overrides={
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Output": {
                            "type": "array",
                            "items": {"type": "string", "format": "uri"},
                            "title": "Output",
                        }
                    }
                }
            }
        }
    )
    mock_prediction_endpoints(
        output_data=[
            "https://example.com/output1.jpg",
            "https://example.com/output2.jpg",
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
    assert all(isinstance(path, Path) for path in output)
    assert all(path.exists() for path in output)
    assert output[0].read_bytes() == b"fake image 1 data"
    assert output[1].read_bytes() == b"fake image 2 data"


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_iterator_of_paths_output(use_async_client):
    mock_model_endpoints(
        version_overrides={
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Output": {
                            "type": "array",
                            "items": {"type": "string", "format": "uri"},
                            "x-cog-array-type": "iterator",
                            "title": "Output",
                        }
                    }
                }
            }
        }
    )
    mock_prediction_endpoints(
        output_data=[
            "https://example.com/output1.jpg",
            "https://example.com/output2.jpg",
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
    assert all(isinstance(path, Path) for path in output_list)
    assert all(path.exists() for path in output_list)
    assert output_list[0].read_bytes() == b"fake image 1 data"
    assert output_list[1].read_bytes() == b"fake image 2 data"


def test_get_path_url_with_pathproxy():
    """Test get_path_url returns the URL for PathProxy instances."""
    from replicate.use import get_path_url, PathProxy

    url = "https://example.com/test.jpg"
    path_proxy = PathProxy(url)

    result = get_path_url(path_proxy)
    assert result == url


def test_get_path_url_with_regular_path():
    """Test get_path_url returns None for regular Path instances."""
    from replicate.use import get_path_url

    regular_path = Path("/tmp/test.txt")

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


def test_get_path_url_with_object_with_target():
    """Test get_path_url returns URL for any object with __replicate_target__."""
    from replicate.use import get_path_url

    class MockObjectWithTarget:
        def __init__(self, target):
            object.__setattr__(self, "__replicate_target__", target)

    url = "https://example.com/mock.png"
    mock_obj = MockObjectWithTarget(url)

    result = get_path_url(mock_obj)
    assert result == url


def test_get_path_url_with_empty_target():
    """Test get_path_url with empty/falsy target values."""
    from replicate.use import get_path_url

    class MockObjectWithEmptyTarget:
        def __init__(self, target):
            object.__setattr__(self, "__replicate_target__", target)

    # Test with empty string
    mock_obj = MockObjectWithEmptyTarget("")
    result = get_path_url(mock_obj)
    assert result == ""

    # Test with None
    mock_obj = MockObjectWithEmptyTarget(None)
    result = get_path_url(mock_obj)
    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_pathproxy_input_conversion(use_async_client):
    """Test that PathProxy instances are converted to URLs when passed to create()."""
    mock_model_endpoints()

    # Mock the file download - this should NOT be called
    file_request_mock = respx.get("https://example.com/input.jpg").mock(
        return_value=httpx.Response(200, content=b"fake input image data")
    )

    # Create a PathProxy instance
    from replicate.use import PathProxy

    path_proxy = PathProxy("https://example.com/input.jpg")

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

    # Call use and create with PathProxy
    hotdog_detector = replicate.use("acme/hotdog-detector")
    run = hotdog_detector.create(image=path_proxy)

    # Verify the request body contains the URL, not the downloaded file
    parsed_body = json.loads(request_body)
    assert parsed_body["input"]["image"] == "https://example.com/input.jpg"

    # Assert that the file was never downloaded
    assert file_request_mock.call_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_function_logs_method(use_async_client):
    mock_model_endpoints()
    mock_prediction_endpoints()

    # Call use and then create method
    hotdog_detector = replicate.use("acme/hotdog-detector")
    run = hotdog_detector.create(prompt="hello world")

    # Call logs method to get current logs
    logs = run.logs()

    # Assert that logs returns the current log value
    assert logs == "Starting prediction..."


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_function_logs_method_polling(use_async_client):
    mock_model_endpoints()

    # Mock prediction endpoints with updated logs on polling
    polling_responses = [
        {
            "id": "pred123",
            "model": "acme/hotdog-detector",
            "version": "xyz123",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/pred123",
                "cancel": "https://api.replicate.com/v1/predictions/pred123/cancel",
            },
            "created_at": "2024-01-01T00:00:00Z",
            "source": "api",
            "status": "processing",
            "input": {"prompt": "hello world"},
            "output": None,
            "error": None,
            "logs": "Starting prediction...",
        },
        {
            "id": "pred123",
            "model": "acme/hotdog-detector",
            "version": "xyz123",
            "urls": {
                "get": "https://api.replicate.com/v1/predictions/pred123",
                "cancel": "https://api.replicate.com/v1/predictions/pred123/cancel",
            },
            "created_at": "2024-01-01T00:00:00Z",
            "source": "api",
            "status": "processing",
            "input": {"prompt": "hello world"},
            "output": None,
            "error": None,
            "logs": "Starting prediction...\nProcessing input...",
        },
    ]

    mock_prediction_endpoints(polling_responses=polling_responses)

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
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_object_output_with_file_properties(use_async_client):
    mock_model_endpoints(
        version_overrides={
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Output": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string", "title": "Text"},
                                "image": {
                                    "type": "string",
                                    "format": "uri",
                                    "title": "Image",
                                },
                                "count": {"type": "integer", "title": "Count"},
                            },
                            "title": "Output",
                        }
                    }
                }
            }
        }
    )
    mock_prediction_endpoints(
        output_data={
            "text": "Generated text",
            "image": "https://example.com/generated.png",
            "count": 42,
        }
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
    assert isinstance(output["image"], Path)
    assert output["image"].exists()
    assert output["image"].read_bytes() == b"fake png data"


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_object_output_with_file_list_property(use_async_client):
    mock_model_endpoints(
        version_overrides={
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Output": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string", "title": "Text"},
                                "images": {
                                    "type": "array",
                                    "items": {"type": "string", "format": "uri"},
                                    "title": "Images",
                                },
                            },
                            "title": "Output",
                        }
                    }
                }
            }
        }
    )
    mock_prediction_endpoints(
        output_data={
            "text": "Generated text",
            "images": [
                "https://example.com/image1.png",
                "https://example.com/image2.png",
            ],
        }
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
    assert all(isinstance(path, Path) for path in output["images"])
    assert all(path.exists() for path in output["images"])
    assert output["images"][0].read_bytes() == b"fake png 1 data"
    assert output["images"][1].read_bytes() == b"fake png 2 data"
