import pytest

from replicate.identifier import ModelVersionIdentifier


@pytest.mark.parametrize(
    "id, expected",
    [
        (
            "meta/llama-2-70b-chat",
            {
                "owner": "meta",
                "name": "llama-2-70b-chat",
                "version": None,
                "error": False,
            },
        ),
        (
            "mistralai/mistral-7b-instruct-v1.4",
            {
                "owner": "mistralai",
                "name": "mistral-7b-instruct-v1.4",
                "version": None,
                "error": False,
            },
        ),
        (
            "nateraw/video-llava:a494250c04691c458f57f2f8ef5785f25bc851e0c91fd349995081d4362322dd",
            {
                "owner": "nateraw",
                "name": "video-llava",
                "version": "a494250c04691c458f57f2f8ef5785f25bc851e0c91fd349995081d4362322dd",
                "error": False,
            },
        ),
        (
            "",
            {"error": True},
        ),
        (
            "invalid",
            {"error": True},
        ),
        (
            "invalid/id/format",
            {"error": True},
        ),
    ],
)
def test_parse_model_id(id, expected):
    try:
        result = ModelVersionIdentifier.parse(id)
        assert result.owner == expected["owner"]
        assert result.name == expected["name"]
        assert result.version == expected["version"]
    except ValueError:
        assert expected["error"]
