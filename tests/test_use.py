import os

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

    # Assert that output is concatenated from the list
    assert output == "Hello world!"


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

    # Assert that output is returned as a list (iterators are returned as lists)
    assert output == ["hello", "world", "test"]


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

    # Assert that output is returned as a Path object
    from pathlib import Path

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

    # Assert that output is returned as a list of Path objects
    from pathlib import Path

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

    # Assert that output is returned as a list of Path objects
    from pathlib import Path

    assert isinstance(output, list)
    assert len(output) == 2
    assert all(isinstance(path, Path) for path in output)
    assert all(path.exists() for path in output)
    assert output[0].read_bytes() == b"fake image 1 data"
    assert output[1].read_bytes() == b"fake image 2 data"


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

    # Assert that output is returned as an object with file downloaded
    from pathlib import Path

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

    # Assert that output is returned as an object with files downloaded
    from pathlib import Path

    assert isinstance(output, dict)
    assert output["text"] == "Generated text"
    assert isinstance(output["images"], list)
    assert len(output["images"]) == 2
    assert all(isinstance(path, Path) for path in output["images"])
    assert all(path.exists() for path in output["images"])
    assert output["images"][0].read_bytes() == b"fake png 1 data"
    assert output["images"][1].read_bytes() == b"fake png 2 data"
