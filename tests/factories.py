import datetime

import responses
from responses import matchers

from replicate.client import Client
from replicate.version import Version


def create_client():
    client = Client(api_token="abc123")
    return client


def get_mock_schema():
    return {
        "info": {"title": "Cog", "version": "0.1.0"},
        "paths": {
            "/": {
                "get": {
                    "summary": "Root",
                    "responses": {
                        "200": {
                            "content": {"application/json": {"schema": {}}},
                            "description": "Successful Response",
                        }
                    },
                    "operationId": "root__get",
                }
            },
            "/predictions": {
                "post": {
                    "summary": "Predict",
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Response"}
                                }
                            },
                            "description": "Successful Response",
                        },
                        "422": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HTTPValidationError"
                                    }
                                }
                            },
                            "description": "Validation Error",
                        },
                    },
                    "description": "Run a single prediction on the model",
                    "operationId": "predict_predictions_post",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Request"}
                            }
                        }
                    },
                }
            },
        },
        "openapi": "3.0.2",
        "components": {
            "schemas": {
                "Input": {
                    "type": "object",
                    "title": "Input",
                    "required": ["text"],
                    "properties": {
                        "text": {
                            "type": "string",
                            "title": "Text",
                            "x-order": 0,
                            "description": "Text to prefix with 'hello '",
                        }
                    },
                },
                "Output": {"type": "string", "title": "Output"},
                "Status": {
                    "enum": ["processing", "succeeded", "failed"],
                    "type": "string",
                    "title": "Status",
                    "description": "An enumeration.",
                },
                "Request": {
                    "type": "object",
                    "title": "Request",
                    "properties": {
                        "input": {"$ref": "#/components/schemas/Input"},
                        "output_file_prefix": {
                            "type": "string",
                            "title": "Output File Prefix",
                        },
                    },
                    "description": "The request body for a prediction",
                },
                "Response": {
                    "type": "object",
                    "title": "Response",
                    "required": ["status"],
                    "properties": {
                        "error": {"type": "string", "title": "Error"},
                        "output": {"$ref": "#/components/schemas/Output"},
                        "status": {"$ref": "#/components/schemas/Status"},
                    },
                    "description": "The response body for a prediction",
                },
                "ValidationError": {
                    "type": "object",
                    "title": "ValidationError",
                    "required": ["loc", "msg", "type"],
                    "properties": {
                        "loc": {
                            "type": "array",
                            "items": {
                                "anyOf": [
                                    {"type": "string"},
                                    {"type": "integer"},
                                ]
                            },
                            "title": "Location",
                        },
                        "msg": {"type": "string", "title": "Message"},
                        "type": {"type": "string", "title": "Error Type"},
                    },
                },
                "HTTPValidationError": {
                    "type": "object",
                    "title": "HTTPValidationError",
                    "properties": {
                        "detail": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/ValidationError"},
                            "title": "Detail",
                        }
                    },
                },
            }
        },
    }


def mock_version_get(
    owner="test", model="model", version="v1", openapi_schema=None, cog_version="0.3.9"
):
    responses.get(
        f"https://api.replicate.com/v1/models/{owner}/{model}/versions/{version}",
        match=[
            matchers.header_matcher({"Authorization": "Token abc123"}),
        ],
        json={
            "id": version,
            "created_at": "2022-04-26T19:29:04.418669Z",
            "cog_version": "0.3.9",
            "openapi_schema": openapi_schema or get_mock_schema(),
        },
    )


def mock_version_get_with_iterator_output(**kwargs):
    schema = get_mock_schema()
    schema["components"]["schemas"]["Output"] = {
        "type": "array",
        "items": {"type": "string"},
        "title": "Output",
        "x-cog-array-type": "iterator",
    }
    mock_version_get(openapi_schema=schema, cog_version="0.3.9", **kwargs)


def mock_version_get_with_list_output(**kwargs):
    schema = get_mock_schema()
    schema["components"]["schemas"]["Output"] = {
        "type": "array",
        "items": {"type": "string"},
        "title": "Output",
    }
    mock_version_get(openapi_schema=schema, cog_version="0.3.9", **kwargs)


def mock_version_get_with_iterator_output_backwards_compatibility_0_3_8(**kwargs):
    schema = get_mock_schema()
    schema["components"]["schemas"]["Output"] = {
        "type": "array",
        "items": {"type": "string"},
        "title": "Output",
    }
    mock_version_get(openapi_schema=schema, cog_version="0.3.8", **kwargs)


def create_version(client=None, openapi_schema=None, cog_version="0.3.0"):
    if client is None:
        client = create_client()
    version = Version(
        id="v1",
        created_at=datetime.datetime.now(),
        cog_version=cog_version,
        openapi_schema=openapi_schema or get_mock_schema(),
    )
    version._client = client
    return version


def create_version_with_iterator_output():
    version = create_version(cog_version="0.3.9")
    version.openapi_schema["components"]["schemas"]["Output"] = {
        "type": "array",
        "items": {"type": "string"},
        "title": "Output",
        "x-cog-array-type": "iterator",
    }
    return version


def create_version_with_list_output():
    version = create_version(cog_version="0.3.9")
    version.openapi_schema["components"]["schemas"]["Output"] = {
        "type": "array",
        "items": {"type": "string"},
        "title": "Output",
    }
    return version


def create_version_with_iterator_output_backwards_compatibility_0_3_8():
    version = create_version(cog_version="0.3.8")
    version.openapi_schema["components"]["schemas"]["Output"] = {
        "type": "array",
        "items": {"type": "string"},
        "title": "Output",
    }
    return version
