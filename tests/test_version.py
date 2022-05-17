import datetime
import responses
from responses import matchers

from replicate.client import Client
from replicate.version import Version


@responses.activate
def test_predict():
    client = Client(api_token="abc123")
    # TODO: factories/fixtures
    version = Version(
        dict(
            id="v1",
            _client=client,
            created_at=datetime.datetime.now(),
            cog_version="0.3.0",
            openapi_schema={
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
                                            "schema": {
                                                "$ref": "#/components/schemas/Response"
                                            }
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
                                        "schema": {
                                            "$ref": "#/components/schemas/Request"
                                        }
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
                                    "items": {
                                        "$ref": "#/components/schemas/ValidationError"
                                    },
                                    "title": "Detail",
                                }
                            },
                        },
                    }
                },
            },
        ),
        client=client,
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
            "output": "hello world",
            "error": None,
            "logs": "",
        },
    )

    assert version.predict(text="world") == "hello world"
