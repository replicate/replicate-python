import httpx
import pytest
import respx

import replicate
from replicate.prediction import Prediction


@pytest.mark.vcr("predictions-create.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_predictions_create(async_flag):
    input = {
        "prompt": "a studio photo of a rainbow colored corgi",
        "width": 512,
        "height": 512,
        "seed": 42069,
    }

    if async_flag:
        model = await replicate.models.async_get("stability-ai/sdxl")
        version = await model.versions.async_get(
            "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
        )
        prediction = await replicate.predictions.async_create(
            version=version,
            input=input,
        )
    else:
        model = replicate.models.get("stability-ai/sdxl")
        version = model.versions.get(
            "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
        )
        prediction = replicate.predictions.create(
            version=version,
            input=input,
        )

    assert prediction.id is not None
    assert prediction.version == version.id
    assert prediction.status == "starting"


@pytest.mark.vcr()
# @pytest.mark.asyncio
@pytest.mark.parametrize("wait_param", [True, 10])
@pytest.mark.parametrize("async_flag", [True, False])
def test_predictions_create_blocking(async_flag, wait_param):
    input = {
        "prompt": "a studio photo of a rainbow colored corgi",
        "width": 512,
        "height": 512,
        "seed": 42069,
    }

    if False:
        model = replicate.models.async_get("stability-ai/sdxl")
        version = model.versions.async_get(
            "7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"
        )
        prediction = replicate.predictions.async_create(
            version=version,
            input=input,
            wait=wait_param,
        )
    else:
        model = replicate.models.get("stability-ai/sdxl")
        version = model.versions.get(
            "7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"
        )
        prediction = replicate.predictions.create(
            version=version,
            input=input,
            wait=wait_param,
        )

    assert prediction.id is not None
    assert prediction.version == version.id
    assert prediction.status == "processing"

    assert prediction.output
    assert prediction.output[0].startswith("data:")


@pytest.mark.vcr("predictions-create.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_predictions_create_with_positional_argument(async_flag):
    version = "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"

    input = {
        "prompt": "a studio photo of a rainbow colored corgi",
        "width": 512,
        "height": 512,
        "seed": 42069,
    }

    if async_flag:
        prediction = await replicate.predictions.async_create(
            version,
            input,
        )
    else:
        prediction = replicate.predictions.create(
            version,
            input,
        )

    assert prediction.id is not None
    assert prediction.version == version
    assert prediction.status == "starting"


@pytest.mark.vcr("predictions-create-by-model.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_predictions_create_by_model(async_flag):
    model = "meta/meta-llama-3-8b-instruct"
    input = {
        "prompt": "write a haiku about llamas",
    }

    if async_flag:
        prediction = await replicate.predictions.async_create(
            model=model,
            input=input,
        )
    else:
        prediction = replicate.predictions.create(
            model=model,
            input=input,
        )

    assert prediction.id is not None
    # assert prediction.model == model
    assert prediction.status == "starting"


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_predictions_create_by_deployment(async_flag):
    router = respx.Router(base_url="https://api.replicate.com/v1")

    router.route(
        method="POST",
        path="/deployments/replicate/my-app-image-generator/predictions",
        name="deployments.predictions.create",
    ).mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "p1",
                "model": "replicate/my-app-image-generator",
                "version": "v1",
                "urls": {
                    "get": "https://api.replicate.com/v1/predictions/p1",
                    "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
                },
                "created_at": "2022-04-26T20:00:40.658234Z",
                "source": "api",
                "status": "starting",
                "input": {"text": "world"},
                "output": None,
                "error": None,
                "logs": "",
            },
        )
    )

    router.route(host="api.replicate.com").pass_through()

    client = replicate.Client(
        api_token="test-token", transport=httpx.MockTransport(router.handler)
    )

    input = {"text": "world"}

    if async_flag:
        prediction = await client.predictions.async_create(
            deployment="replicate/my-app-image-generator",
            input=input,
        )
    else:
        prediction = client.predictions.create(
            deployment="replicate/my-app-image-generator",
            input=input,
        )

    assert prediction.id is not None
    assert prediction.status == "starting"


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_predictions_create_fail_with_too_many_arguments(async_flag):
    router = respx.Router(base_url="https://api.replicate.com/v1")

    client = replicate.Client(
        api_token="test-token", transport=httpx.MockTransport(router.handler)
    )

    version = "02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3"
    model = "meta/meta-llama-3-8b-instruct"
    deployment = "replicate/my-app-image-generator"
    input = {}

    with pytest.raises(ValueError) as exc_info:
        if async_flag:
            await client.predictions.async_create(
                version=version,
                model=model,
                deployment=deployment,
                input=input,
            )
        else:
            client.predictions.create(
                version=version,
                model=model,
                deployment=deployment,
                input=input,
            )
    assert (
        str(exc_info.value)
        == "Exactly one of 'model', 'version', or 'deployment' must be specified."
    )


@pytest.mark.vcr("models-predictions-create.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_predictions_cancel(async_flag):
    input = {
        "prompt": "a studio photo of a rainbow colored corgi",
        "width": 512,
        "height": 512,
        "seed": 42069,
    }

    if async_flag:
        model = await replicate.models.async_get("stability-ai/sdxl")
        version = await model.versions.async_get(
            "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
        )
        prediction = await replicate.predictions.async_create(
            version=version,
            input=input,
        )

        id = prediction.id
        assert prediction.status == "starting"

        prediction = await replicate.predictions.async_cancel(prediction.id)
        assert prediction.id == id
        assert prediction.status == "canceled"
    else:
        model = replicate.models.get("stability-ai/sdxl")
        version = model.versions.get(
            "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
        )
        prediction = replicate.predictions.create(
            version=version,
            input=input,
        )

        id = prediction.id
        assert prediction.status == "starting"

        prediction = replicate.predictions.cancel(prediction.id)
        assert prediction.id == id
        assert prediction.status == "canceled"


@pytest.mark.vcr("predictions-get.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_predictions_get(async_flag):
    id = "vgcm4plb7tgzlyznry5d5jkgvu"

    if async_flag:
        prediction = await replicate.predictions.async_get(id)
    else:
        prediction = replicate.predictions.get(id)

    assert prediction.id == id


@pytest.mark.vcr("predictions-cancel.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_predictions_cancel_instance_method(async_flag):
    input = {
        "prompt": "a studio photo of a rainbow colored corgi",
        "width": 512,
        "height": 512,
        "seed": 42069,
    }

    if async_flag:
        model = await replicate.models.async_get("stability-ai/sdxl")
        version = await model.versions.async_get(
            "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
        )
        prediction = await replicate.predictions.async_create(
            version=version,
            input=input,
        )

        assert prediction.status == "starting"

        await prediction.async_cancel()
        assert prediction.status == "canceled"
    else:
        model = replicate.models.get("stability-ai/sdxl")
        version = model.versions.get(
            "39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
        )
        prediction = replicate.predictions.create(
            version=version,
            input=input,
        )

        assert prediction.status == "starting"

        prediction.cancel()
        assert prediction.status == "canceled"


@pytest.mark.vcr("predictions-stream.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_predictions_stream(async_flag):
    input = {
        "prompt": "write a sonnet about camelids",
    }

    if async_flag:
        model = await replicate.models.async_get("meta/llama-2-70b-chat")
        version = await model.versions.async_get(
            "02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3"
        )
        prediction = await replicate.predictions.async_create(
            version=version,
            input=input,
            stream=True,
        )
    else:
        model = replicate.models.get("meta/llama-2-70b-chat")
        version = model.versions.get(
            "02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3"
        )
        prediction = replicate.predictions.create(
            version=version,
            input=input,
            stream=True,
        )

    assert prediction.id is not None
    assert prediction.version == version.id
    assert prediction.status == "starting"
    assert prediction.urls is not None
    assert prediction.urls["stream"] is not None


# @responses.activate
# def test_stream():
#     client = create_client()
#     version = create_version(client)

#     rsp = responses.post(
#         "https://api.replicate.com/v1/predictions",
#         match=[
#             matchers.json_params_matcher(
#                 {
#                     "version": "v1",
#                     "input": {"text": "world"},
#                     "stream": "true",
#                 }
#             ),
#         ],
#         json={
#             "id": "p1",
#             "version": "v1",
#             "urls": {
#                 "get": "https://api.replicate.com/v1/predictions/p1",
#                 "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
#                 "stream": "https://streaming.api.replicate.com/v1/predictions/p1",
#             },
#             "created_at": "2022-04-26T20:00:40.658234Z",
#             "completed_at": "2022-04-26T20:02:27.648305Z",
#             "source": "api",
#             "status": "processing",
#             "input": {"text": "world"},
#             "output": None,
#             "error": None,
#             "logs": "",
#         },
#     )

#     prediction = client.predictions.create(
#         version=version,
#         input={"text": "world"},
#         stream=True,
#     )

#     assert rsp.call_count == 1

#     assert (
#         prediction.urls["stream"]
#         == "https://streaming.api.replicate.com/v1/predictions/p1"
#     )


# @responses.activate
# def test_async_timings():
#     client = create_client()
#     version = create_version(client)

#     responses.post(
#         "https://api.replicate.com/v1/predictions",
#         match=[
#             matchers.json_params_matcher(
#                 {
#                     "version": "v1",
#                     "input": {"text": "hello"},
#                     "webhook_completed": "https://example.com/webhook",
#                 }
#             ),
#         ],
#         json={
#             "id": "p1",
#             "version": "v1",
#             "urls": {
#                 "get": "https://api.replicate.com/v1/predictions/p1",
#                 "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
#             },
#             "created_at": "2022-04-26T20:00:40.658234Z",
#             "source": "api",
#             "status": "processing",
#             "input": {"text": "hello"},
#             "output": None,
#             "error": None,
#             "logs": "",
#         },
#     )

#     responses.get(
#         "https://api.replicate.com/v1/predictions/p1",
#         json={
#             "id": "p1",
#             "version": "v1",
#             "urls": {
#                 "get": "https://api.replicate.com/v1/predictions/p1",
#                 "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
#             },
#             "created_at": "2022-04-26T20:00:40.658234Z",
#             "completed_at": "2022-04-26T20:02:27.648305Z",
#             "source": "api",
#             "status": "succeeded",
#             "input": {"text": "hello"},
#             "output": "hello world",
#             "error": None,
#             "logs": "",
#             "metrics": {
#                 "predict_time": 1.2345,
#             },
#         },
#     )

#     prediction = client.predictions.create(
#         version=version,
#         input={"text": "hello"},
#         webhook_completed="https://example.com/webhook",
#     )

#     assert prediction.created_at == "2022-04-26T20:00:40.658234Z"
#     assert prediction.completed_at is None
#     assert prediction.output is None
#     assert prediction.urls["get"] == "https://api.replicate.com/v1/predictions/p1"
#     prediction.wait()
#     assert prediction.created_at == "2022-04-26T20:00:40.658234Z"
#     assert prediction.completed_at == "2022-04-26T20:02:27.648305Z"
#     assert prediction.output == "hello world"
#     assert prediction.metrics["predict_time"] == 1.2345


# def test_prediction_progress():
#     client = create_client()
#     version = create_version(client)
#     prediction = Prediction(
#         id="ufawqhfynnddngldkgtslldrkq", version=version, status="starting"
#     )

#     lines = [
#         "Using seed: 12345",
#         "0%|          | 0/5 [00:00<?, ?it/s]",
#         "20%|██        | 1/5 [00:00<00:01, 21.38it/s]",
#         "40%|████▍     | 2/5 [00:01<00:01, 22.46it/s]",
#         "60%|████▍     | 3/5 [00:01<00:01, 22.46it/s]",
#         "80%|████████  | 4/5 [00:01<00:00, 22.86it/s]",
#         "100%|██████████| 5/5 [00:02<00:00, 22.26it/s]",
#     ]
#     logs = ""

#     for i, line in enumerate(lines):
#         logs += "\n" + line
#         prediction.logs = logs

#         progress = prediction.progress

#         if i == 0:
#             prediction.status = "processing"
#             assert progress is None
#         elif i == 1:
#             assert progress is not None
#             assert progress.current == 0
#             assert progress.total == 5
#             assert progress.percentage == 0.0
#         elif i == 2:
#             assert progress is not None
#             assert progress.current == 1
#             assert progress.total == 5
#             assert progress.percentage == 0.2
#         elif i == 3:
#             assert progress is not None
#             assert progress.current == 2
#             assert progress.total == 5
#             assert progress.percentage == 0.4
#         elif i == 4:
#             assert progress is not None
#             assert progress.current == 3
#             assert progress.total == 5
#             assert progress.percentage == 0.6
#         elif i == 5:
#             assert progress is not None
#             assert progress.current == 4
#             assert progress.total == 5
#             assert progress.percentage == 0.8
#         elif i == 6:
#             assert progress is not None
#             prediction.status = "succeeded"
#             assert progress.current == 5
#             assert progress.total == 5
#             assert progress.percentage == 1.0


# ---------------------------------------------------------------------------
# Unit tests: output_iterator / async_output_iterator non-list guard
# ---------------------------------------------------------------------------


def _make_prediction(output, status="succeeded"):
    """Build a minimal Prediction with a mock client (no HTTP calls needed)."""
    p = Prediction(
        id="p1",
        model="owner/model",
        version="v1",
        urls={
            "get": "https://api.replicate.com/v1/predictions/p1",
            "cancel": "https://api.replicate.com/v1/predictions/p1/cancel",
        },
        created_at="2024-01-01T00:00:00.000000Z",
        source="api",
        status=status,
        input={"prompt": "hello"},
        output=output,
        error=None,
        logs="",
    )
    return p


def test_output_iterator_completed_with_list_output_yields_nothing():
    """output_iterator yields only items arriving *after* the iterator starts.

    When called on an already-completed prediction, all output tokens were
    present at start-time so no new items are yielded.  This documents the
    intended "streaming" contract: call output_iterator while the prediction
    is still running, not after it has completed.
    """
    p = _make_prediction(output=["token1", "token2", "token3"], status="succeeded")
    # The full list is the "previous_output" baseline, so nothing is yielded.
    assert list(p.output_iterator()) == []


def test_output_iterator_none_output_yields_nothing():
    """output_iterator must handle None output gracefully (empty sequence)."""
    p = _make_prediction(output=None)
    assert list(p.output_iterator()) == []


def test_output_iterator_string_output_raises():
    """output_iterator must raise ValueError when output is a plain string.

    Before the fix, ``self.output or []`` returned the string intact, causing
    ``yield from "hello world"`` to silently iterate over individual characters
    instead of raising a clear error.
    """
    p = _make_prediction(output="hello world")
    with pytest.raises(ValueError, match="array output type"):
        list(p.output_iterator())


def test_output_iterator_dict_output_raises():
    """output_iterator must raise ValueError when output is a dict."""
    p = _make_prediction(output={"url": "https://example.com/file.png"})
    with pytest.raises(ValueError, match="array output type"):
        list(p.output_iterator())


@pytest.mark.asyncio
async def test_async_output_iterator_none_output_yields_nothing():
    """async_output_iterator must handle None output gracefully."""
    p = _make_prediction(output=None)
    results = []
    async for item in p.async_output_iterator():
        results.append(item)
    assert results == []


@pytest.mark.asyncio
async def test_async_output_iterator_string_output_raises():
    """async_output_iterator must raise ValueError for non-list outputs.

    Before the fix, ``self.output or []`` returned the string intact,
    causing iteration over individual characters silently.
    """
    p = _make_prediction(output="some string")
    with pytest.raises(ValueError, match="array output type"):
        async for _ in p.async_output_iterator():
            pass
