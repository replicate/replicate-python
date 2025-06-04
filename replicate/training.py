from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    TypedDict,
    Union,
    overload,
)

from typing_extensions import NotRequired, Unpack

from replicate.helpers import async_encode_json, encode_json
from replicate.identifier import ModelVersionIdentifier
from replicate.model import Model
from replicate.pagination import Page
from replicate.resource import Namespace, Resource
from replicate.version import Version

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore

if TYPE_CHECKING:
    from replicate.client import Client
    from replicate.file import FileEncodingStrategy


class Training(Resource):
    """
    A training made for a model hosted on Replicate.
    """

    _client: "Client" = pydantic.PrivateAttr()

    id: str
    """The unique ID of the training."""

    model: str
    """An identifier for the model used to create the prediction, in the form `owner/name`."""

    version: Union[str, Version]
    """The version of the model used to create the training."""

    destination: Optional[str]
    """The model destination of the training."""

    status: Literal["starting", "processing", "succeeded", "failed", "canceled"]
    """The status of the training."""

    input: Optional[Dict[str, Any]]
    """The input to the training."""

    output: Optional[Any]
    """The output of the training."""

    logs: Optional[str]
    """The logs of the training."""

    metrics: Optional[Dict[str, Any]]
    """Metrics for the training."""

    error: Optional[str]
    """The error encountered during the training, if any."""

    created_at: Optional[str]
    """When the training was created."""

    started_at: Optional[str]
    """When the training was started."""

    completed_at: Optional[str]
    """When the training was completed, if finished."""

    urls: Optional[Dict[str, str]]
    """
    URLs associated with the training.

    The following keys are available:
    - `get`: A URL to fetch the training.
    - `cancel`: A URL to cancel the training.
    """

    def cancel(self) -> None:
        """
        Cancel a running training.
        """

        canceled = self._client.trainings.cancel(self.id)
        for name, value in canceled.dict().items():
            setattr(self, name, value)

    async def async_cancel(self) -> None:
        """
        Cancel a running training asynchronously.
        """

        canceled = await self._client.trainings.async_cancel(self.id)
        for name, value in canceled.dict().items():
            setattr(self, name, value)

    def reload(self) -> None:
        """
        Load the training from the server.
        """

        updated = self._client.trainings.get(self.id)
        for name, value in updated.dict().items():
            setattr(self, name, value)

    async def async_reload(self) -> None:
        """
        Load the training from the server asynchronously.
        """

        updated = await self._client.trainings.async_get(self.id)
        for name, value in updated.dict().items():
            setattr(self, name, value)


class Trainings(Namespace):
    """
    Namespace for operations related to trainings.
    """

    def list(self, cursor: Union[str, "ellipsis", None] = ...) -> Page[Training]:  # noqa: F821
        """
        List your trainings.

        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Training]: A page of trainings.
        Raises:
            ValueError: If `cursor` is `None`.
        """

        if cursor is None:
            raise ValueError("cursor cannot be None")

        resp = self._client._request(
            "GET", "/v1/trainings" if cursor is ... else cursor
        )

        obj = resp.json()
        obj["results"] = [
            _json_to_training(self._client, result) for result in obj["results"]
        ]

        return Page[Training](**obj)

    async def async_list(
        self,
        cursor: Union[str, "ellipsis", None] = ...,  # noqa: F821
    ) -> Page[Training]:
        """
        List your trainings.

        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Training]: A page of trainings.
        Raises:
            ValueError: If `cursor` is `None`.
        """

        if cursor is None:
            raise ValueError("cursor cannot be None")

        resp = await self._client._async_request(
            "GET", "/v1/trainings" if cursor is ... else cursor
        )

        obj = resp.json()
        obj["results"] = [
            _json_to_training(self._client, result) for result in obj["results"]
        ]

        return Page[Training](**obj)

    def get(self, id: str) -> Training:
        """
        Get a training by ID.

        Args:
            id: The ID of the training.
        Returns:
            Training: The training object.
        """

        resp = self._client._request(
            "GET",
            f"/v1/trainings/{id}",
        )

        return _json_to_training(self._client, resp.json())

    async def async_get(self, id: str) -> Training:
        """
        Get a training by ID.

        Args:
            id: The ID of the training.
        Returns:
            Training: The training object.
        """

        resp = await self._client._async_request(
            "GET",
            f"/v1/trainings/{id}",
        )

        return _json_to_training(self._client, resp.json())

    class CreateTrainingParams(TypedDict):
        """Parameters for creating a training."""

        destination: Union[str, Tuple[str, str], "Model"]
        """The destination for the trained model."""

        webhook: NotRequired[str]
        """The URL to receive a POST request with training updates."""

        webhook_completed: NotRequired[str]
        """The URL to receive a POST request when the training is completed."""

        webhook_events_filter: NotRequired[List[str]]
        """List of events to trigger webhooks."""

        file_encoding_strategy: NotRequired["FileEncodingStrategy"]
        """The strategy to use for encoding files in the training input."""

    @overload
    def create(  # pylint: disable=too-many-arguments
        self,
        version: str,
        input: Dict[str, Any],
        destination: str,
        webhook: Optional[str] = None,
        webhook_events_filter: Optional[List[str]] = None,
        **kwargs,
    ) -> Training: ...

    @overload
    def create(
        self,
        model: Union[str, Tuple[str, str], "Model"],
        version: Union[str, Version],
        input: Optional[Dict[str, Any]] = None,
        **params: Unpack["Trainings.CreateTrainingParams"],
    ) -> Training: ...

    def create(  # type: ignore
        self,
        *args,
        model: Optional[Union[str, Tuple[str, str], "Model"]] = None,
        version: Optional[Union[str, Version]] = None,
        input: Optional[Dict[str, Any]] = None,
        **params: Unpack["Trainings.CreateTrainingParams"],
    ) -> Training:
        """
        Create a new training using the specified model version as a base.
        """

        url = None

        # Support positional arguments for backwards compatibility
        if args:
            if shorthand := args[0] if len(args) > 0 else None:
                url = _create_training_url_from_shorthand(shorthand)

            input = args[1] if len(args) > 1 else input
            if len(args) > 2:
                params["destination"] = args[2]
            if len(args) > 3:
                params["webhook"] = args[3]
            if len(args) > 4:
                params["webhook_completed"] = args[4]
            if len(args) > 5:
                params["webhook_events_filter"] = args[5]
        elif model and version:
            url = _create_training_url_from_model_and_version(model, version)
        elif model is None and isinstance(version, str):
            url = _create_training_url_from_shorthand(version)

        if not url:
            raise ValueError("model and version or shorthand version must be specified")

        file_encoding_strategy = params.pop("file_encoding_strategy", None)
        if input is not None:
            input = encode_json(
                input,
                client=self._client,
                file_encoding_strategy=file_encoding_strategy,
            )

        body = _create_training_body(input, **params)

        resp = self._client._request(
            "POST",
            url,
            json=body,
        )

        return _json_to_training(self._client, resp.json())

    async def async_create(
        self,
        model: Union[str, Tuple[str, str], "Model"],
        version: Union[str, Version],
        input: Dict[str, Any],
        **params: Unpack["Trainings.CreateTrainingParams"],
    ) -> Training:
        """
        Create a new training using the specified model version as a base.

        Args:
            version: The ID of the base model version that you're using to train a new model version.
            input: The input to the training.
            destination: The desired model to push to in the format `{owner}/{model_name}`. This should be an existing model owned by the user or organization making the API request.
            webhook: The URL to send a POST request to when the training is completed. Defaults to None.
            webhook_completed: The URL to receive a POST request when the prediction is completed.
            webhook_events_filter: The events to send to the webhook. Defaults to None.
        Returns:
            The training object.
        """

        url = _create_training_url_from_model_and_version(model, version)

        file_encoding_strategy = params.pop("file_encoding_strategy", None)
        if input is not None:
            input = await async_encode_json(
                input,
                client=self._client,
                file_encoding_strategy=file_encoding_strategy,
            )
        body = _create_training_body(input, **params)

        resp = await self._client._async_request(
            "POST",
            url,
            json=body,
        )

        return _json_to_training(self._client, resp.json())

    def cancel(self, id: str) -> Training:
        """
        Cancel a training.

        Args:
            id: The ID of the training to cancel.
        Returns:
            Training: The canceled training object.
        """

        resp = self._client._request(
            "POST",
            f"/v1/trainings/{id}/cancel",
        )

        return _json_to_training(self._client, resp.json())

    async def async_cancel(self, id: str) -> Training:
        """
        Cancel a training.

        Args:
            id: The ID of the training to cancel.
        Returns:
            Training: The canceled training object.
        """

        resp = await self._client._async_request(
            "POST",
            f"/v1/trainings/{id}/cancel",
        )

        return _json_to_training(self._client, resp.json())


def _create_training_body(
    input: Optional[Dict[str, Any]] = None,
    *,
    destination: Optional[Union[str, Tuple[str, str], "Model"]] = None,
    webhook: Optional[str] = None,
    webhook_completed: Optional[str] = None,
    webhook_events_filter: Optional[List[str]] = None,
    **_kwargs,
) -> Dict[str, Any]:
    body = {}

    if input is not None:
        body["input"] = input

    if destination is None:
        raise ValueError(
            "A destination must be provided as a positional or keyword argument."
        )
    if isinstance(destination, Model):
        destination = f"{destination.owner}/{destination.name}"
    elif isinstance(destination, tuple):
        destination = f"{destination[0]}/{destination[1]}"
    body["destination"] = destination

    if webhook is not None:
        body["webhook"] = webhook

    if webhook_completed is not None:
        body["webhook_completed"] = webhook_completed

    if webhook_events_filter is not None:
        body["webhook_events_filter"] = webhook_events_filter

    return body


def _create_training_url_from_shorthand(ref: str) -> str:
    owner, name, version_id = ModelVersionIdentifier.parse(ref)
    return f"/v1/models/{owner}/{name}/versions/{version_id}/trainings"


def _create_training_url_from_model_and_version(
    model: Union[str, Tuple[str, str], "Model"],
    version: Union[str, "Version"],
) -> str:
    if isinstance(model, Model):
        owner, name = model.owner, model.name
    elif isinstance(model, tuple):
        owner, name = model[0], model[1]
    elif isinstance(model, str):
        owner, name, _ = ModelVersionIdentifier.parse(model)
    else:
        raise ValueError(
            "model must be a Model, a tuple of (owner, name), or a string in the format 'owner/name'"
        )

    if isinstance(version, Version):
        version_id = version.id
    else:
        version_id = version

    return f"/v1/models/{owner}/{name}/versions/{version_id}/trainings"


def _json_to_training(client: "Client", json: Dict[str, Any]) -> Training:
    training = Training(**json)
    training._client = client

    # FIXME: This should be populated by the API
    if (
        training.output
        and isinstance(training.output, dict)
        and "version" in training.output
    ):
        id = ModelVersionIdentifier.parse(training.output["version"])
        training.destination = f"{id.owner}/{id.name}"

    return training
