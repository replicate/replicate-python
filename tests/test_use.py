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
                    "PredictionResponse": {
                        "type": "object",
                        "title": "PredictionResponse",
                        "properties": {
                            "id": {"type": "string", "title": "Id"},
                            "logs": {"type": "string", "title": "Logs", "default": ""},
                            "error": {"type": "string", "title": "Error"},
                            "input": {"$ref": "#/components/schemas/Input"},
                            "output": {"$ref": "#/components/schemas/Output"},
                            "status": {"$ref": "#/components/schemas/Status"},
                            "metrics": {"type": "object", "title": "Metrics"},
                            "version": {"type": "string", "title": "Version"},
                            "created_at": {
                                "type": "string",
                                "title": "Created At",
                                "format": "date-time",
                            },
                            "started_at": {
                                "type": "string",
                                "title": "Started At",
                                "format": "date-time",
                            },
                            "completed_at": {
                                "type": "string",
                                "title": "Completed At",
                                "format": "date-time",
                            },
                        },
                    },
                    "PredictionRequest": {
                        "type": "object",
                        "title": "PredictionRequest",
                        "properties": {
                            "id": {"type": "string", "title": "Id"},
                            "input": {"$ref": "#/components/schemas/Input"},
                            "webhook": {
                                "type": "string",
                                "title": "Webhook",
                                "format": "uri",
                                "maxLength": 65536,
                                "minLength": 1,
                            },
                            "created_at": {
                                "type": "string",
                                "title": "Created At",
                                "format": "date-time",
                            },
                            "output_file_prefix": {
                                "type": "string",
                                "title": "Output File Prefix",
                            },
                            "webhook_events_filter": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/WebhookEvent"},
                                "default": ["start", "output", "logs", "completed"],
                            },
                        },
                    },
                    "Status": {
                        "enum": [
                            "starting",
                            "processing",
                            "succeeded",
                            "canceled",
                            "failed",
                        ],
                        "type": "string",
                        "title": "Status",
                        "description": "An enumeration.",
                    },
                    "WebhookEvent": {
                        "enum": ["start", "output", "logs", "completed"],
                        "type": "string",
                        "title": "WebhookEvent",
                        "description": "An enumeration.",
                    },
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
                "latest_version": latest_version,
            },
        )
    )

    versions_results = versions
    if uses_versionless_api == "empty":
        versions_results = []

    if uses_versionless_api == "notfound":
        respx.get(
            "https://api.replicate.com/v1/models/acme/hotdog-detector/versions"
        ).mock(return_value=httpx.Response(404, json={"detail": "Not found"}))
    else:
        respx.get(
            "https://api.replicate.com/v1/models/acme/hotdog-detector/versions"
        ).mock(return_value=httpx.Response(200, json={"results": versions_results}))

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

    prediction_id = initial_prediction["id"]
    respx.get(f"https://api.replicate.com/v1/predictions/{prediction_id}").mock(
        side_effect=[httpx.Response(200, json=response) for response in predictions]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_use(client_mode):
    mock_model_endpoints()
    mock_prediction_endpoints()

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
        output = hotdog_detector(prompt="hello world")

    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_use_with_version_identifier(client_mode):
    mock_model_endpoints()
    mock_prediction_endpoints()

    hotdog_detector = replicate.use(
        "acme/hotdog-detector:xyz123", use_async=client_mode == ClientMode.ASYNC
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
        output = hotdog_detector(prompt="hello world")

    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_use_with_function_ref(client_mode):
    mock_model_endpoints()
    mock_prediction_endpoints()

    class HotdogDetector:
        name = "acme/hotdog-detector:xyz123"

        def __call__(self, prompt: str) -> str: ...

    hotdog_detector = replicate.use(
        HotdogDetector(), use_async=client_mode == ClientMode.ASYNC
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
        output = hotdog_detector(prompt="hello world")

    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_use_versionless_empty_versions_list(client_mode):
    mock_model_endpoints(uses_versionless_api="empty")
    mock_prediction_endpoints(uses_versionless_api="empty")

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
        output = hotdog_detector(prompt="hello world")

    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_use_versionless_404_versions_list(client_mode):
    mock_model_endpoints(uses_versionless_api="notfound")
    mock_prediction_endpoints(uses_versionless_api="notfound")

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
        output = hotdog_detector(prompt="hello world")

    assert output == "not hotdog"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_use_function_create_method(client_mode):
    mock_model_endpoints()
    mock_prediction_endpoints()

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )
    if client_mode == ClientMode.ASYNC:
        run = await hotdog_detector.create(prompt="hello world")
    else:
        run = hotdog_detector.create(prompt="hello world")

    from replicate.use import AsyncRun, Run

    if client_mode == ClientMode.ASYNC:
        assert isinstance(run, AsyncRun)
    else:
        assert isinstance(run, Run)
    assert run._prediction.id == "pred123"
    assert run._prediction.status == "processing"
    assert run._prediction.input == {"prompt": "hello world"}


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_use_function_openapi_schema_dereferenced(client_mode):
    mock_model_endpoints(
        versions=[
            create_mock_version(
                {
                    "openapi_schema": {
                        "components": {
                            "schemas": {
                                "Extra": {"type": "object"},
                                "Output": {"$ref": "#/components/schemas/ModelOutput"},
                                "ModelOutput": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"},
                                        "image": {
                                            "type": "string",
                                            "format": "uri",
                                        },
                                        "count": {"type": "integer"},
                                    },
                                },
                            }
                        }
                    }
                }
            )
        ]
    )

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )

    if client_mode == ClientMode.ASYNC:
        schema = await hotdog_detector.openapi_schema()
    else:
        schema = hotdog_detector.openapi_schema()

    assert schema["components"]["schemas"]["Extra"] == {"type": "object"}
    assert schema["components"]["schemas"]["Input"] == {
        "type": "object",
        "properties": {"prompt": {"type": "string", "title": "Prompt"}},
        "required": ["prompt"],
    }
    assert schema["components"]["schemas"]["Output"] == {
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

    # Assert everything else is stripped out
    assert schema["paths"] == {}

    assert "PredictionRequest" not in schema["components"]["schemas"]
    assert "PredictionResponse" not in schema["components"]["schemas"]
    assert "ModelOutput" not in schema["components"]["schemas"]
    assert "Status" not in schema["components"]["schemas"]
    assert "WebhookEvent" not in schema["components"]["schemas"]


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
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

    hotdog_detector = replicate.use(
        "acme/hotdog-detector",
        use_async=client_mode == ClientMode.ASYNC,
        streaming=True,
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
        output = hotdog_detector(prompt="hello world")

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
    if client_mode == ClientMode.ASYNC:
        await hotdog_detector.create(text_input=output)
    else:
        hotdog_detector.create(text_input=output)

    # Verify the request body contains the stringified version
    assert request_body
    parsed_body = json.loads(request_body)
    assert parsed_body["input"]["text_input"] == "Hello world!"


@pytest.mark.asyncio
async def test_output_iterator_async_iteration():
    """Test OutputIterator async iteration capabilities."""
    from replicate.use import OutputIterator

    # Create mock sync and async iterators
    def sync_iterator():
        return iter(["Hello", " ", "world", "!"])

    async def async_iterator():
        for item in ["Hello", " ", "world", "!"]:
            yield item

    # Test concatenate iterator
    concatenate_output = OutputIterator(
        sync_iterator, async_iterator, {}, is_concatenate=True
    )

    # Test sync iteration
    sync_result = list(concatenate_output)
    assert sync_result == ["Hello", " ", "world", "!"]

    # Test async iteration
    async_result = []
    async for item in concatenate_output:
        async_result.append(item)
    assert async_result == ["Hello", " ", "world", "!"]

    # Test sync string conversion
    assert str(concatenate_output) == "Hello world!"

    # Test async await (should return joined string for concatenate)
    async_result = await concatenate_output
    assert async_result == "Hello world!"


@pytest.mark.asyncio
async def test_output_iterator_async_non_concatenate():
    """Test OutputIterator async iteration for non-concatenate iterators."""
    from replicate.use import OutputIterator

    # Create mock sync and async iterators for non-concatenate case
    test_items = ["item1", "item2", "item3"]

    def sync_iterator():
        return iter(test_items)

    async def async_iterator():
        for item in test_items:
            yield item

    # Test non-concatenate iterator
    regular_output = OutputIterator(
        sync_iterator, async_iterator, {}, is_concatenate=False
    )

    # Test sync iteration
    sync_result = list(regular_output)
    assert sync_result == test_items

    # Test async iteration
    async_result = []
    async for item in regular_output:
        async_result.append(item)
    assert async_result == test_items

    # Test sync string conversion
    assert str(regular_output) == str(test_items)

    # Test async await (should return list for non-concatenate)
    async_result = await regular_output
    assert async_result == test_items


@pytest.mark.asyncio
@respx.mock
async def test_async_function_concatenate_iterator_output():
    """Test AsyncFunction with concatenate iterator output."""
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
                {"status": "succeeded", "output": ["Async", " ", "Hello", " ", "World"]}
            ),
        ]
    )

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=True, streaming=True
    )

    run = await hotdog_detector.create(prompt="hello world")
    output = await run.output()

    from replicate.use import OutputIterator

    assert isinstance(output, OutputIterator)
    assert str(output) == "Async Hello World"

    # Test async await (should return joined string for concatenate)
    async_result = await output
    assert async_result == "Async Hello World"

    # Test async iteration
    async_result = []
    async for item in output:
        async_result.append(item)
    assert async_result == ["Async", " ", "Hello", " ", "World"]

    # Also test that it's still sync iterable
    sync_result = list(output)
    assert sync_result == ["Async", " ", "Hello", " ", "World"]


@pytest.mark.asyncio
async def test_output_iterator_await_syntax_demo():
    """Demonstrate the clean await syntax for OutputIterator."""
    from replicate.use import OutputIterator

    # Create mock iterators
    def sync_iterator():
        return iter(["Hello", " ", "World"])

    async def async_iterator():
        for item in ["Hello", " ", "World"]:
            yield item

    # Test concatenate mode - await returns string
    concatenate_output = OutputIterator(
        sync_iterator, async_iterator, {}, is_concatenate=True
    )

    # This is the clean syntax we wanted: str(await iterator)
    result = await concatenate_output
    assert result == "Hello World"
    assert str(result) == "Hello World"  # Can use str() on the result

    # Test non-concatenate mode - await returns list
    regular_output = OutputIterator(
        sync_iterator, async_iterator, {}, is_concatenate=False
    )

    result = await regular_output
    assert result == ["Hello", " ", "World"]
    assert str(result) == "['Hello', ' ', 'World']"  # str() gives list representation


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_use_concatenate_iterator_without_streaming_returns_string(client_mode):
    """Test that concatenate iterator models without streaming=True return final concatenated string."""
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

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
        output = hotdog_detector(prompt="hello world")

    assert output == "Hello world!"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_iterator_output_returns_immediately(client_mode):
    """Test that OutputIterator is returned immediately without waiting for completion."""
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
            create_mock_prediction({"status": "processing", "output": []}),
            create_mock_prediction({"status": "processing", "output": ["Hello"]}),
            create_mock_prediction(
                {"status": "succeeded", "output": ["Hello", " ", "World"]}
            ),
        ]
    )

    hotdog_detector = replicate.use(
        "acme/hotdog-detector",
        use_async=client_mode == ClientMode.ASYNC,
        streaming=True,
    )

    # Get the output iterator - this should return immediately even though prediction is processing
    if client_mode == ClientMode.ASYNC:
        run = await hotdog_detector.create(prompt="hello world")
        output_iterator = await run.output()
    else:
        run = hotdog_detector.create(prompt="hello world")
        output_iterator = run.output()

    from replicate.use import OutputIterator

    assert isinstance(output_iterator, OutputIterator)

    # Verify the prediction is still processing when we get the iterator
    assert run._prediction.status == "processing"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_streaming_output_yields_incrementally(client_mode):
    """Test that OutputIterator yields results incrementally during polling."""
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

    # Create a prediction that will be polled multiple times
    prediction_id = "pred123"

    initial_prediction = create_mock_prediction(
        {"id": prediction_id, "status": "processing", "output": []},
        prediction_id=prediction_id,
    )

    if client_mode == ClientMode.ASYNC:
        respx.post("https://api.replicate.com/v1/predictions").mock(
            return_value=httpx.Response(201, json=initial_prediction)
        )
    else:
        respx.post("https://api.replicate.com/v1/predictions").mock(
            return_value=httpx.Response(201, json=initial_prediction)
        )

    poll_responses = [
        create_mock_prediction(
            {"status": "processing", "output": ["Hello"]}, prediction_id=prediction_id
        ),
        create_mock_prediction(
            {"status": "processing", "output": ["Hello", " "]},
            prediction_id=prediction_id,
        ),
        create_mock_prediction(
            {"status": "processing", "output": ["Hello", " ", "streaming"]},
            prediction_id=prediction_id,
        ),
        create_mock_prediction(
            {"status": "processing", "output": ["Hello", " ", "streaming", " "]},
            prediction_id=prediction_id,
        ),
        create_mock_prediction(
            {
                "status": "succeeded",
                "output": ["Hello", " ", "streaming", " ", "world!"],
            },
            prediction_id=prediction_id,
        ),
    ]

    respx.get(f"https://api.replicate.com/v1/predictions/{prediction_id}").mock(
        side_effect=[httpx.Response(200, json=resp) for resp in poll_responses]
    )

    hotdog_detector = replicate.use(
        "acme/hotdog-detector",
        use_async=client_mode == ClientMode.ASYNC,
        streaming=True,
    )

    # Get the output iterator immediately
    if client_mode == ClientMode.ASYNC:
        run = await hotdog_detector.create(prompt="hello world", use_async=True)
        output_iterator = await run.output()
    else:
        run = hotdog_detector.create(prompt="hello world")
        output_iterator = run.output()

    from replicate.use import OutputIterator

    assert isinstance(output_iterator, OutputIterator)

    # Track when we receive each item to verify incremental delivery
    collected_items = []

    if client_mode == ClientMode.ASYNC:
        async for item in output_iterator:
            collected_items.append(item)
            # Break after we get some incremental results to verify polling works
            if len(collected_items) >= 3:
                break
    else:
        for item in output_iterator:
            collected_items.append(item)
            # Break after we get some incremental results to verify polling works
            if len(collected_items) >= 3:
                break

    # Verify we got incremental streaming results
    assert len(collected_items) >= 3
    # The items should be the concatenated string parts from the incremental output
    result = "".join(collected_items)
    assert "Hello" in result  # Should contain the first part we streamed


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_non_streaming_output_waits_for_completion(client_mode):
    """Test that non-iterator outputs still wait for completion."""
    mock_model_endpoints(
        versions=[
            create_mock_version(
                {
                    "openapi_schema": {
                        "components": {
                            "schemas": {
                                "Output": {"type": "string"}  # Non-iterator output
                            }
                        }
                    }
                }
            )
        ]
    )

    mock_prediction_endpoints(
        predictions=[
            create_mock_prediction({"status": "processing", "output": None}),
            create_mock_prediction({"status": "succeeded", "output": "Final result"}),
        ]
    )

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )

    # For non-iterator output, this should wait for completion
    if client_mode == ClientMode.ASYNC:
        run = await hotdog_detector.create(prompt="hello world")
        output = await run.output()
    else:
        run = hotdog_detector.create(prompt="hello world")
        output = run.output()

    # Should get the final result directly
    assert output == "Final result"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
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

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
        output = hotdog_detector(prompt="hello world")

    assert output == ["hello", "world", "test"]


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
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

    hotdog_detector = replicate.use(
        "acme/hotdog-detector",
        use_async=client_mode == ClientMode.ASYNC,
        streaming=True,
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
        output = hotdog_detector(prompt="hello world")

    from replicate.use import OutputIterator

    assert isinstance(output, OutputIterator)
    # Convert to list to check contents
    output_list = list(output)
    assert output_list == ["hello", "world", "test"]


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
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

    respx.get("https://example.com/output.jpg").mock(
        return_value=httpx.Response(200, content=b"fake image data")
    )

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
        output = hotdog_detector(prompt="hello world")

    assert isinstance(output, os.PathLike)
    assert get_path_url(output) == "https://example.com/output.jpg"
    assert os.path.exists(output)
    assert open(output, "rb").read() == b"fake image data"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
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

    respx.get("https://example.com/output1.jpg").mock(
        return_value=httpx.Response(200, content=b"fake image 1 data")
    )
    respx.get("https://example.com/output2.jpg").mock(
        return_value=httpx.Response(200, content=b"fake image 2 data")
    )

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
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
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
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

    respx.get("https://example.com/output1.jpg").mock(
        return_value=httpx.Response(200, content=b"fake image 1 data")
    )
    respx.get("https://example.com/output2.jpg").mock(
        return_value=httpx.Response(200, content=b"fake image 2 data")
    )

    hotdog_detector = replicate.use(
        "acme/hotdog-detector",
        use_async=client_mode == ClientMode.ASYNC,
        streaming=True,
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
        output = hotdog_detector(prompt="hello world")

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
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_use_pathproxy_input_conversion(client_mode):
    mock_model_endpoints()

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

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )
    if client_mode == ClientMode.ASYNC:
        await hotdog_detector.create(image=urlpath)
    else:
        hotdog_detector.create(image=urlpath)

    # Verify the request body contains the URL, not the downloaded file
    assert request_body
    parsed_body = json.loads(request_body)
    assert parsed_body["input"]["image"] == "https://example.com/input.jpg"

    assert file_request_mock.call_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_use_function_logs_method(client_mode):
    mock_model_endpoints()
    mock_prediction_endpoints(predictions=[create_mock_prediction()])

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )
    if client_mode == ClientMode.ASYNC:
        run = await hotdog_detector.create(prompt="hello world")
    else:
        run = hotdog_detector.create(prompt="hello world")

    if client_mode == ClientMode.ASYNC:
        logs = await run.logs()
    else:
        logs = run.logs()

    assert logs == "Starting prediction..."


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
@respx.mock
async def test_use_function_logs_method_polling(client_mode):
    mock_model_endpoints()

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

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )
    if client_mode == ClientMode.ASYNC:
        run = await hotdog_detector.create(prompt="hello world")
    else:
        run = hotdog_detector.create(prompt="hello world")

    if client_mode == ClientMode.ASYNC:
        initial_logs = await run.logs()
    else:
        initial_logs = run.logs()
    assert initial_logs == "Starting prediction..."

    if client_mode == ClientMode.ASYNC:
        updated_logs = await run.logs()
    else:
        updated_logs = run.logs()
    assert updated_logs == "Starting prediction...\nProcessing input..."


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
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

    respx.get("https://example.com/generated.png").mock(
        return_value=httpx.Response(200, content=b"fake png data")
    )

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
        output = hotdog_detector(prompt="hello world")

    assert isinstance(output, dict)
    assert output["text"] == "Generated text"
    assert output["count"] == 42
    assert isinstance(output["image"], os.PathLike)
    assert get_path_url(output["image"]) == "https://example.com/generated.png"
    assert os.path.exists(output["image"])
    assert open(output["image"], "rb").read() == b"fake png data"


@pytest.mark.asyncio
@pytest.mark.parametrize("client_mode", [ClientMode.DEFAULT, ClientMode.ASYNC])
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

    respx.get("https://example.com/image1.png").mock(
        return_value=httpx.Response(200, content=b"fake png 1 data")
    )
    respx.get("https://example.com/image2.png").mock(
        return_value=httpx.Response(200, content=b"fake png 2 data")
    )

    hotdog_detector = replicate.use(
        "acme/hotdog-detector", use_async=client_mode == ClientMode.ASYNC
    )

    if client_mode == ClientMode.ASYNC:
        output = await hotdog_detector(prompt="hello world")
    else:
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
