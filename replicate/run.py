import asyncio
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union

from typing_extensions import Unpack

from replicate.exceptions import ModelError
from replicate.identifier import ModelVersionIdentifier
from replicate.schema import make_schema_backwards_compatible
from replicate.version import Versions

if TYPE_CHECKING:
    from replicate.client import Client
    from replicate.prediction import Predictions


def run(
    client: "Client",
    ref: str,
    input: Optional[Dict[str, Any]] = None,
    **params: Unpack["Predictions.CreatePredictionParams"],
) -> Union[Any, Iterator[Any]]:  # noqa: ANN401
    """
    Run a model and wait for its output.
    """

    owner, name, version_id = ModelVersionIdentifier.parse(ref)

    prediction = client.predictions.create(
        version=version_id, input=input or {}, **params
    )

    if owner and name:
        version = Versions(client, model=(owner, name)).get(version_id)

        # Return an iterator of the output
        schema = make_schema_backwards_compatible(
            version.openapi_schema, version.cog_version
        )
        output = schema["components"]["schemas"]["Output"]
        if (
            output.get("type") == "array"
            and output.get("x-cog-array-type") == "iterator"
        ):
            return prediction.output_iterator()

    prediction.wait()

    if prediction.status == "failed":
        raise ModelError(prediction.error)

    return prediction.output


async def async_run(
    client: "Client",
    ref: str,
    input: Optional[Dict[str, Any]] = None,
    **params: Unpack["Predictions.CreatePredictionParams"],
) -> Union[Any, Iterator[Any]]:  # noqa: ANN401
    """
    Run a model and wait for its output asynchronously.
    """

    owner, name, version_id = ModelVersionIdentifier.parse(ref)

    prediction = await client.predictions.async_create(
        version=version_id, input=input or {}, **params
    )

    if owner and name:
        version = await Versions(client, model=(owner, name)).async_get(version_id)

        # Return an iterator of the output
        schema = make_schema_backwards_compatible(
            version.openapi_schema, version.cog_version
        )
        output = schema["components"]["schemas"]["Output"]
        if (
            output.get("type") == "array"
            and output.get("x-cog-array-type") == "iterator"
        ):
            return prediction.output_iterator()

    while prediction.status not in ["succeeded", "failed", "canceled"]:
        await asyncio.sleep(client.poll_interval)
        prediction = await client.predictions.async_get(prediction.id)

    if prediction.status == "failed":
        raise ModelError(prediction.error)

    return prediction.output


__all__: List = []
