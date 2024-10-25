from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Optional,
    Union,
)

from typing_extensions import Unpack

from replicate import identifier
from replicate.exceptions import ModelError
from replicate.helpers import transform_output
from replicate.model import Model
from replicate.prediction import Prediction
from replicate.schema import make_schema_backwards_compatible
from replicate.version import Version, Versions

if TYPE_CHECKING:
    from replicate.client import Client
    from replicate.identifier import ModelVersionIdentifier
    from replicate.prediction import Predictions


def run(
    client: "Client",
    ref: Union["Model", "Version", "ModelVersionIdentifier", str],
    input: Optional[Dict[str, Any]] = None,
    *,
    use_file_output: Optional[bool] = True,
    **params: Unpack["Predictions.CreatePredictionParams"],
) -> Union[Any, Iterator[Any]]:  # noqa: ANN401
    """
    Run a model and wait for its output.
    """

    if "wait" not in params:
        params["wait"] = True
    is_blocking = params["wait"] != False  # noqa: E712

    version, owner, name, version_id = identifier._resolve(ref)

    if version_id is not None:
        prediction = client.predictions.create(
            version=version_id, input=input or {}, **params
        )
    elif owner and name:
        prediction = client.models.predictions.create(
            model=(owner, name), input=input or {}, **params
        )
    else:
        raise ValueError(
            f"Invalid argument: {ref}. Expected model, version, or reference in the format owner/name or owner/name:version"
        )

    if not version and (owner and name and version_id):
        version = Versions(client, model=(owner, name)).get(version_id)

    # Currently the "Prefer: wait" interface will return a prediction with a status
    # of "processing" rather than a terminal state because it returns before the
    # prediction has been fully processed. If request exceeds the wait time, even if
    # it is actually processing, the prediction will be in a "starting" state.
    #
    # We should fix this in the blocking API itself. Predictions that are done should
    # be in a terminal state and predictions that are processing should be in state
    # "processing".
    in_terminal_state = is_blocking and prediction.status != "starting"
    if not in_terminal_state:
        # Return a "polling" iterator if the model has an output iterator array type.
        if version and (iterator := _make_output_iterator(client, version, prediction)):
            return iterator

        prediction.wait()

    if prediction.status == "failed":
        raise ModelError(prediction)

    # Return an iterator for the completed prediction when needed.
    if version and (iterator := _make_output_iterator(client, version, prediction)):
        return iterator

    if use_file_output:
        return transform_output(prediction.output, client)

    return prediction.output


async def async_run(
    client: "Client",
    ref: Union["Model", "Version", "ModelVersionIdentifier", str],
    input: Optional[Dict[str, Any]] = None,
    *,
    use_file_output: Optional[bool] = True,
    **params: Unpack["Predictions.CreatePredictionParams"],
) -> Union[Any, AsyncIterator[Any]]:  # noqa: ANN401
    """
    Run a model and wait for its output asynchronously.
    """

    if "wait" not in params:
        params["wait"] = True
    is_blocking = params["wait"] != False  # noqa: E712

    version, owner, name, version_id = identifier._resolve(ref)

    if version or version_id:
        prediction = await client.predictions.async_create(
            version=(version or version_id), input=input or {}, **params
        )
    elif owner and name:
        prediction = await client.models.predictions.async_create(
            model=(owner, name), input=input or {}, **params
        )
    else:
        raise ValueError(
            f"Invalid argument: {ref}. Expected model, version, or reference in the format owner/name or owner/name:version"
        )

    if not version and (owner and name and version_id):
        version = await Versions(client, model=(owner, name)).async_get(version_id)

    # Currently the "Prefer: wait" interface will return a prediction with a status
    # of "processing" rather than a terminal state because it returns before the
    # prediction has been fully processed. If request exceeds the wait time, even if
    # it is actually processing, the prediction will be in a "starting" state.
    #
    # We should fix this in the blocking API itself. Predictions that are done should
    # be in a terminal state and predictions that are processing should be in state
    # "processing".
    in_terminal_state = is_blocking and prediction.status != "starting"
    if not in_terminal_state:
        # Return a "polling" iterator if the model has an output iterator array type.
        if version and (
            iterator := _make_async_output_iterator(client, version, prediction)
        ):
            return iterator

        await prediction.async_wait()

    # Return an iterator for completed output if the model has an output iterator array type.
    if version and (
        iterator := _make_async_output_iterator(client, version, prediction)
    ):
        return iterator

    if prediction.status == "failed":
        raise ModelError(prediction)

    if use_file_output:
        return transform_output(prediction.output, client)

    return prediction.output


def _has_output_iterator_array_type(version: Version) -> bool:
    schema = make_schema_backwards_compatible(
        version.openapi_schema, version.cog_version
    )
    output = schema.get("components", {}).get("schemas", {}).get("Output", {})
    return (
        output.get("type") == "array" and output.get("x-cog-array-type") == "iterator"
    )


def _make_output_iterator(
    client: "Client", version: Version, prediction: Prediction
) -> Optional[Iterator[Any]]:
    if not _has_output_iterator_array_type(version):
        return None

    if prediction.status == "starting":
        iterator = prediction.output_iterator()
    elif prediction.output is not None:
        iterator = iter(prediction.output)
    else:
        return None

    def _iterate(iter: Iterator[Any]) -> Iterator[Any]:
        for chunk in iter:
            yield transform_output(chunk, client)

    return _iterate(iterator)


def _make_async_output_iterator(
    client: "Client", version: Version, prediction: Prediction
) -> Optional[AsyncIterator[Any]]:
    if not _has_output_iterator_array_type(version):
        return None

    if prediction.status == "starting":
        iterator = prediction.async_output_iterator()
    elif prediction.output is not None:

        async def _list_to_aiter(lst: list) -> AsyncIterator:
            for item in lst:
                yield item

        iterator = _list_to_aiter(prediction.output)
    else:
        return None

    async def _transform(iter: AsyncIterator[Any]) -> AsyncIterator:
        async for chunk in iter:
            yield transform_output(chunk, client)

    return _transform(iterator)


__all__: List = []
