import os

import httpx
import pytest
import respx

import replicate

# Allow use() to be called in test context
os.environ["REPLICATE_ALWAYS_ALLOW_USE"] = "1"


def mock_model_endpoints(
    owner="acme",
    name="hotdog-detector",
    version_id="xyz123",
    versions_response_status=200,
    versions_results=None,
    *,
    include_specific_version=False,
    output_schema=None,
):
    """Mock the model and versions endpoints."""
    if output_schema is None:
        output_schema = {"type": "string", "title": "Output"}

    if versions_results is None:
        versions_results = [
            {
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
                                "properties": {
                                    "prompt": {"type": "string", "title": "Prompt"}
                                },
                                "required": ["prompt"],
                            },
                            "Output": output_schema,
                        }
                    },
                },
            }
        ]

    # Mock the model endpoint
    respx.get(f"https://api.replicate.com/v1/models/{owner}/{name}").mock(
        return_value=httpx.Response(
            200,
            json={
                "url": f"https://replicate.com/{owner}/{name}",
                "owner": owner,
                "name": name,
                "description": "A model to detect hotdogs",
                "visibility": "public",
                "github_url": f"https://github.com/{owner}/{name}",
                "paper_url": None,
                "license_url": None,
                "run_count": 42,
                "cover_image_url": None,
                "default_example": None,
                "latest_version": {
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
                                    "properties": {
                                        "prompt": {"type": "string", "title": "Prompt"}
                                    },
                                    "required": ["prompt"],
                                },
                                "Output": output_schema,
                            }
                        },
                    },
                },
            },
        )
    )

    # Mock the versions list endpoint
    if versions_response_status == 404:
        respx.get(f"https://api.replicate.com/v1/models/{owner}/{name}/versions").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )
    else:
        respx.get(f"https://api.replicate.com/v1/models/{owner}/{name}/versions").mock(
            return_value=httpx.Response(
                versions_response_status, json={"results": versions_results}
            )
        )

    # Mock specific version endpoint if requested
    if include_specific_version:
        respx.get(
            f"https://api.replicate.com/v1/models/{owner}/{name}/versions/{version_id}"
        ).mock(
            return_value=httpx.Response(
                200, json=versions_results[0] if versions_results else {}
            )
        )


def mock_prediction_endpoints(
    owner="acme",
    name="hotdog-detector",
    version_id="xyz123",
    prediction_id="pred123",
    input_data=None,
    output_data="not hotdog",
    *,
    use_versionless_api=False,
    polling_responses=None,
):
    """Mock the prediction creation and polling endpoints."""
    if input_data is None:
        input_data = {"prompt": "hello world"}

    if polling_responses is None:
        polling_responses = [
            {
                "id": prediction_id,
                "model": f"{owner}/{name}",
                "version": "hidden" if use_versionless_api else version_id,
                "urls": {
                    "get": f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    "cancel": f"https://api.replicate.com/v1/predictions/{prediction_id}/cancel",
                },
                "created_at": "2024-01-01T00:00:00Z",
                "source": "api",
                "status": "processing",
                "input": input_data,
                "output": None,
                "error": None,
                "logs": "Starting prediction...",
            },
            {
                "id": prediction_id,
                "model": f"{owner}/{name}",
                "version": "hidden" if use_versionless_api else version_id,
                "urls": {
                    "get": f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    "cancel": f"https://api.replicate.com/v1/predictions/{prediction_id}/cancel",
                },
                "created_at": "2024-01-01T00:00:00Z",
                "source": "api",
                "status": "succeeded",
                "input": input_data,
                "output": output_data,
                "error": None,
                "logs": "Starting prediction...\nPrediction completed.",
            },
        ]

    # Mock the prediction creation endpoint
    if use_versionless_api:
        respx.post(
            f"https://api.replicate.com/v1/models/{owner}/{name}/predictions"
        ).mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": prediction_id,
                    "model": f"{owner}/{name}",
                    "version": "hidden",
                    "urls": {
                        "get": f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        "cancel": f"https://api.replicate.com/v1/predictions/{prediction_id}/cancel",
                    },
                    "created_at": "2024-01-01T00:00:00Z",
                    "source": "api",
                    "status": "processing",
                    "input": input_data,
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
                    "id": prediction_id,
                    "model": f"{owner}/{name}",
                    "version": version_id,
                    "urls": {
                        "get": f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        "cancel": f"https://api.replicate.com/v1/predictions/{prediction_id}/cancel",
                    },
                    "created_at": "2024-01-01T00:00:00Z",
                    "source": "api",
                    "status": "processing",
                    "input": input_data,
                    "output": None,
                    "error": None,
                    "logs": "",
                },
            )
        )

    # Mock the prediction polling endpoint
    respx.get(f"https://api.replicate.com/v1/predictions/{prediction_id}").mock(
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
    mock_model_endpoints(include_specific_version=True)
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
    mock_model_endpoints(versions_results=[])
    mock_prediction_endpoints(use_versionless_api=True)

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
    mock_model_endpoints(versions_response_status=404)
    mock_prediction_endpoints(use_versionless_api=True)

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
    concatenate_iterator_output_schema = {
        "type": "array",
        "items": {"type": "string"},
        "x-cog-array-type": "iterator",
        "x-cog-array-display": "concatenate",
        "title": "Output",
    }

    mock_model_endpoints(output_schema=concatenate_iterator_output_schema)
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
    list_of_strings_output_schema = {
        "type": "array",
        "items": {"type": "string"},
        "title": "Output",
    }

    mock_model_endpoints(output_schema=list_of_strings_output_schema)
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
    iterator_of_strings_output_schema = {
        "type": "array",
        "items": {"type": "string"},
        "x-cog-array-type": "iterator",
        "title": "Output",
    }

    mock_model_endpoints(output_schema=iterator_of_strings_output_schema)
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
    path_output_schema = {"type": "string", "format": "uri", "title": "Output"}

    mock_model_endpoints(output_schema=path_output_schema)
    mock_prediction_endpoints(output_data="https://example.com/output.jpg")

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is returned as a string URL
    assert output == "https://example.com/output.jpg"


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_list_of_paths_output(use_async_client):
    list_of_paths_output_schema = {
        "type": "array",
        "items": {"type": "string", "format": "uri"},
        "title": "Output",
    }

    mock_model_endpoints(output_schema=list_of_paths_output_schema)
    mock_prediction_endpoints(
        output_data=[
            "https://example.com/output1.jpg",
            "https://example.com/output2.jpg",
        ]
    )

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is returned as a list of URLs
    assert output == [
        "https://example.com/output1.jpg",
        "https://example.com/output2.jpg",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use_iterator_of_paths_output(use_async_client):
    iterator_of_paths_output_schema = {
        "type": "array",
        "items": {"type": "string", "format": "uri"},
        "x-cog-array-type": "iterator",
        "title": "Output",
    }

    mock_model_endpoints(output_schema=iterator_of_paths_output_schema)
    mock_prediction_endpoints(
        output_data=[
            "https://example.com/output1.jpg",
            "https://example.com/output2.jpg",
        ]
    )

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")

    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")

    # Assert that output is returned as a list of URLs
    assert output == [
        "https://example.com/output1.jpg",
        "https://example.com/output2.jpg",
    ]


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
