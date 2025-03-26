import os
import unittest.mock as mock

import pytest

from replicate.exceptions import ModelError
from replicate.include import (
    Function,
    Run,
    include,
    run_state,
    run_token,
)


@pytest.fixture
def client():
    with mock.patch("replicate.Client") as client_class:
        client_instance = mock.MagicMock()
        client_class.return_value = client_instance
        yield client_class, client_instance


@pytest.fixture
def model():
    model_obj = mock.MagicMock()
    yield model_obj


@pytest.fixture
def version():
    version_obj = mock.MagicMock()
    version_obj.openapi_schema = {
        "components": {"schemas": {"Output": {"type": "string"}}}
    }
    version_obj.cog_version = "0.4.0"
    yield version_obj


@pytest.fixture
def prediction():
    pred = mock.MagicMock()
    pred.status = "succeeded"
    pred.output = "test output"
    pred.id = "pred123"
    yield pred


@pytest.fixture
def iterator_version():
    iter_version = mock.MagicMock()
    iter_version.openapi_schema = {
        "components": {
            "schemas": {"Output": {"type": "array", "x-cog-array-type": "iterator"}}
        }
    }
    iter_version.cog_version = "0.4.0"
    yield iter_version


def test_run_state_context_manager():
    with pytest.raises(RuntimeError):
        include("owner/model:version")

    with run_state("load"):
        include("owner/model:version")

    with run_state("load"):
        include("owner/model:version")
        with run_state("setup"):
            with pytest.raises(RuntimeError):
                include("owner/model:version")


def test_run_token_context_manager(client):
    client_class, _ = client

    fn = Function("owner/model:version")

    with mock.patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="No run token found"):
            fn._client()

    with run_token("test-token"):
        fn._client()
        client_class.assert_called_with(api_token="test-token")

        with run_token("another-token"):
            fn._client()
            client_class.assert_called_with(api_token="another-token")


def test_find_api_token_from_env(monkeypatch, client):
    client_class, _ = client
    monkeypatch.setenv("REPLICATE_API_TOKEN", "env-token")
    with mock.patch("sys.stderr"):
        fn = Function("owner/model:version")
        fn._client()
        client_class.assert_called_with(api_token="env-token")


def test_find_api_token_from_context(client):
    client_class, _ = client
    with run_token("context-token"):
        fn = Function("owner/model:version")
        fn._client()
        client_class.assert_called_with(api_token="context-token")


def test_find_api_token_raises_error():
    with mock.patch.dict(os.environ, {}, clear=True):
        fn = Function("owner/model:version")
        with pytest.raises(ValueError, match="No run token found"):
            fn._client()


def test_include_outside_load_state():
    with pytest.raises(RuntimeError, match="You may only call .* at the top level"):
        include("owner/model:version")


def test_include_in_load_state():
    with run_state("load"):
        fn = include("owner/model:version")
        assert isinstance(fn, Function)
        assert fn.function_ref == "owner/model:version"


def test_function_split_function_ref():
    fn = Function("owner/model:version")
    assert fn._split_function_ref() == ("owner", "model", "version")

    fn = Function("owner/model")
    assert fn._split_function_ref() == ("owner", "model", None)


def test_function_client(client):
    client_class, client_instance = client

    with run_token("test-token"):
        fn = Function("owner/model:version")
        client = fn._client()

        client_class.assert_called_once_with(api_token="test-token")
        assert client == client_instance


def test_function_model(client, model):
    _, client_instance = client
    client_instance.models.get.return_value = model

    with run_token("test-token"):
        fn = Function("owner/model:version")
        result = fn._model()

        client_instance.models.get.assert_called_once_with("owner/model")
        assert result == model


def test_function_version_with_version_id(client, model, version):
    _, client_instance = client
    client_instance.models.get.return_value = model
    model.versions.get.return_value = version

    with run_token("test-token"):
        fn = Function("owner/model:version")
        result = fn._version()

        client_instance.models.get.assert_called_once_with("owner/model")
        model.versions.get.assert_called_once_with("version")
        assert result == version


def test_function_version_with_latest(client, model, version):
    _, client_instance = client
    client_instance.models.get.return_value = model
    model.latest_version = version

    with run_token("test-token"):
        fn = Function("owner/model")
        result = fn._version()

        client_instance.models.get.assert_called_once_with("owner/model")
        assert result == version


@mock.patch.object(Function, "start")
@mock.patch.object(Function, "_version")
def test_function_call(version_patch, start_patch):
    run_obj = mock.MagicMock()
    start_patch.return_value = run_obj

    with run_token("test-token"):
        fn = Function("owner/model:version")
        fn(prompt="Hello", temperature=0.7)

        start_patch.assert_called_once_with(prompt="Hello", temperature=0.7)
        run_obj.wait.assert_called_once()


def test_function_start(client, model, version, prediction, capsys):
    _, client_instance = client

    client_instance.models.get.return_value = model
    model.versions.get.return_value = version
    client_instance.predictions.create.return_value = prediction

    with run_token("test-token"):
        fn = Function("owner/model:version")
        run = fn.start(prompt="Hello", temperature=0.7)

        client_instance.predictions.create.assert_called_once_with(
            version=version, input={"prompt": "Hello", "temperature": 0.7}
        )

        assert isinstance(run, Run)
        assert run.prediction == prediction
        assert run.version == version

        captured = capsys.readouterr()
        assert "https://replicate.com/p/pred123" in captured.out


def test_function_default_example(client, model):
    _, client_instance = client
    example_obj = mock.MagicMock()
    client_instance.models.get.return_value = model
    model.default_example = example_obj

    with run_token("test-token"):
        fn = Function("owner/model:version")
        example = fn.default_example

        assert example == example_obj


def test_function_openapi_schema(client, model, version):
    _, client_instance = client
    client_instance.models.get.return_value = model
    model.versions.get.return_value = version

    with run_token("test-token"):
        fn = Function("owner/model:version")
        schema = fn.openapi_schema

        assert schema == version.openapi_schema


def test_run_wait_success(prediction, version):
    with mock.patch(
        "replicate.include._has_output_iterator_array_type", return_value=False
    ):
        run = Run(prediction=prediction, version=version)
        result = run.wait()

        prediction.wait.assert_called_once()
        assert result == "test output"


def test_run_wait_failure(version):
    failed_prediction = mock.MagicMock()
    failed_prediction.status = "failed"

    run = Run(prediction=failed_prediction, version=version)
    with pytest.raises(ModelError):
        run.wait()

    failed_prediction.wait.assert_called_once()


def test_run_wait_iterator_output(iterator_version):
    iter_prediction = mock.MagicMock()
    iter_prediction.status = "succeeded"
    iter_prediction.output = ["Hello", " ", "world"]

    with mock.patch(
        "replicate.include._has_output_iterator_array_type", return_value=True
    ):
        run = Run(prediction=iter_prediction, version=iterator_version)
        result = run.wait()

        iter_prediction.wait.assert_called_once()
        assert result == "Hello world"


def test_run_logs(prediction, version):
    prediction.logs = "log content"

    run = Run(prediction=prediction, version=version)
    logs = run.logs()

    prediction.reload.assert_called_once()
    assert logs == "log content"
