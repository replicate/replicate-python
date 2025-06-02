import asyncio
import io
import json
import os
import sys
from email.message import EmailMessage
from email.parser import BytesParser
from email.policy import HTTP
from typing import AsyncIterator, Iterator, Optional, cast

import httpx
import pytest
import respx

import replicate
from replicate.client import Client
from replicate.exceptions import ModelError, ReplicateError
from replicate.helpers import FileOutput

# Allow use() to be called in test context
os.environ["REPLICATE_ALWAYS_ALLOW_USE"] = "1"


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async_client", [False])
@respx.mock
async def test_use(use_async_client):
    # Mock the model endpoint
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
                "latest_version": {
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
                                                "schema": {"$ref": "#/components/schemas/PredictionRequest"}
                                            }
                                        }
                                    },
                                    "responses": {
                                        "200": {
                                            "content": {
                                                "application/json": {
                                                    "schema": {"$ref": "#/components/schemas/PredictionResponse"}
                                                }
                                            }
                                        }
                                    }
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
                                    "required": ["prompt"]
                                },
                                "Output": {
                                    "type": "string",
                                    "title": "Output"
                                }
                            }
                        }
                    }
                }
            }
        )
    )

    # Mock the versions list endpoint
    respx.get("https://api.replicate.com/v1/models/acme/hotdog-detector/versions").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
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
                                                    "schema": {"$ref": "#/components/schemas/PredictionRequest"}
                                                }
                                            }
                                        },
                                        "responses": {
                                            "200": {
                                                "content": {
                                                    "application/json": {
                                                        "schema": {"$ref": "#/components/schemas/PredictionResponse"}
                                                    }
                                                }
                                            }
                                        }
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
                                        "required": ["prompt"]
                                    },
                                    "Output": {
                                        "type": "string",
                                        "title": "Output"
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        )
    )

    # Mock the prediction creation endpoint
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
            }
        )
    )

    # Mock the prediction polling endpoint - first call returns processing, second returns completed
    prediction_responses = [
        httpx.Response(
            200,
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
                "logs": "Starting prediction...",
            }
        ),
        httpx.Response(
            200,
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
                "status": "succeeded",
                "input": {"prompt": "hello world"},
                "output": "not hotdog",
                "error": None,
                "logs": "Starting prediction...\nPrediction completed.",
            }
        )
    ]
    
    respx.get("https://api.replicate.com/v1/predictions/pred123").mock(
        side_effect=prediction_responses
    )

    # Call use with "acme/hotdog-detector"
    hotdog_detector = replicate.use("acme/hotdog-detector")
    
    # Call function with prompt="hello world"
    output = hotdog_detector(prompt="hello world")
    
    # Assert that output is the completed output from the prediction request
    assert output == "not hotdog"

# TODO
#
# - [ ] Test a model with a version identifier acme/hotdog-detector:xyz
# - [ ] Test a versionless model acme/hotdog-dectector when versions list is empty
# - [ ] Test a versionless model acme/hotdog-dectector when versions list returns a 404
# - [ ] Test a model that returns a list of strings
# - [ ] Test a model that returns an Iterator of strings
# - [ ] Test a model that returns a ConcatenateIterator of strings
# - [ ] Test a model that returns a Path
# - [ ] Test a model that returns a list of Path
# - [ ] Test a model that returns an iterator of Path
# - [ ] Test the `create` method on Function.
# - [ ] Test the logs method on Function returns an iterator where the first iteration is the current value of logs
# - [ ] Test the logs method on Function returns an iterator that polls for new logs
