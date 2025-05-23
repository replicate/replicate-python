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
    is_blocking = params["wait"] is not False

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
        if version and _has_output_iterator_array_type(version):
            return (
                transform_output(chunk, client)
                for chunk in prediction.output_iterator()
            )

        prediction.wait()

    if prediction.status == "failed":
        raise ModelError(prediction)

    # Return an iterator for the completed prediction when needed.
    if (
        version
        and _has_output_iterator_array_type(version)
        and prediction.output is not None
    ):
        return (transform_output(chunk, client) for chunk in prediction.output)

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
    is_blocking = params["wait"] is not False

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
        if version and _has_output_iterator_array_type(version):
            return (
                transform_output(chunk, client)
                async for chunk in prediction.async_output_iterator()
            )

        await prediction.async_wait()

    if prediction.status == "failed":
        raise ModelError(prediction)

    # Return an iterator for completed output if the model has an output iterator array type.
    if (
        version
        and _has_output_iterator_array_type(version)
        and prediction.output is not None
    ):
        return (
            transform_output(chunk, client)
            async for chunk in _make_async_iterator(prediction.output)
        )

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


async def _make_async_iterator(list: list) -> AsyncIterator:
    for item in list:
        yield item


__all__: List = []
