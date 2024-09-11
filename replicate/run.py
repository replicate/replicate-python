from collections.abc import Mapping, Sequence
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
from replicate.model import Model
from replicate.prediction import Prediction
from replicate.schema import make_schema_backwards_compatible
from replicate.stream import FileOutput
from replicate.version import Version, Versions

if TYPE_CHECKING:
    from replicate.client import Client
    from replicate.identifier import ModelVersionIdentifier
    from replicate.prediction import Predictions


def run(
    client: "Client",
    ref: Union["Model", "Version", "ModelVersionIdentifier", str],
    input: Optional[Dict[str, Any]] = None,
    use_file_output: bool = False,
    **params: Unpack["Predictions.CreatePredictionParams"],
) -> Union[Any, Iterator[Any]]:  # noqa: ANN401
    """
    Run a model and wait for its output.
    """

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

    if version and (iterator := _make_output_iterator(version, prediction)):
        return iterator

    prediction.wait()

    if prediction.status == "failed":
        raise ModelError(prediction)

    if use_file_output:
        return transform_output(prediction.output, client)

    return prediction.output


async def async_run(
    client: "Client",
    ref: Union["Model", "Version", "ModelVersionIdentifier", str],
    input: Optional[Dict[str, Any]] = None,
    use_file_output: bool = False,
    **params: Unpack["Predictions.CreatePredictionParams"],
) -> Union[Any, AsyncIterator[Any]]:  # noqa: ANN401
    """
    Run a model and wait for its output asynchronously.
    """

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

    if version and (iterator := _make_async_output_iterator(version, prediction)):
        return iterator

    await prediction.async_wait()

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
    version: Version, prediction: Prediction
) -> Optional[Iterator[Any]]:
    if _has_output_iterator_array_type(version):
        return prediction.output_iterator()

    return None


def _make_async_output_iterator(
    version: Version, prediction: Prediction
) -> Optional[AsyncIterator[Any]]:
    if _has_output_iterator_array_type(version):
        return prediction.async_output_iterator()

    return None


def transform_output(value: Any, client: "Client") -> Any:
    def transform(obj: Any) -> Any:
        if isinstance(obj, Mapping):
            return {k: transform(v) for k, v in obj.items()}
        elif isinstance(obj, Sequence) and not isinstance(obj, str):
            return [transform(item) for item in obj]
        elif isinstance(obj, str) and (
            obj.startswith("https:") or obj.startswith("data:")
        ):
            return FileOutput(obj, client)
        return obj

    return transform(value)


__all__: List = []
