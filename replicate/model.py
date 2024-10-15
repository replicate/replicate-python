from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, Tuple, Union, overload

from typing_extensions import NotRequired, TypedDict, Unpack, deprecated

from replicate.exceptions import ReplicateException
from replicate.helpers import async_encode_json, encode_json
from replicate.identifier import ModelVersionIdentifier
from replicate.pagination import Page
from replicate.prediction import (
    Prediction,
    _create_prediction_body,
    _create_prediction_request_params,
    _json_to_prediction,
)
from replicate.resource import Namespace, Resource
from replicate.version import Version, Versions

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore


if TYPE_CHECKING:
    from replicate.client import Client
    from replicate.prediction import Predictions


class Model(Resource):
    """
    A machine learning model hosted on Replicate.
    """

    _client: "Client" = pydantic.PrivateAttr()

    url: str
    """
    The URL of the model.
    """

    owner: str
    """
    The owner of the model.
    """

    name: str
    """
    The name of the model.
    """

    description: Optional[str]
    """
    The description of the model.
    """

    visibility: Literal["public", "private"]
    """
    The visibility of the model. Can be 'public' or 'private'.
    """

    github_url: Optional[str]
    """
    The GitHub URL of the model.
    """

    paper_url: Optional[str]
    """
    The URL of the paper related to the model.
    """

    license_url: Optional[str]
    """
    The URL of the license for the model.
    """

    run_count: int
    """
    The number of runs of the model.
    """

    cover_image_url: Optional[str]
    """
    The URL of the cover image for the model.
    """

    default_example: Optional[Prediction]
    """
    The default example of the model.
    """

    latest_version: Optional[Version]
    """
    The latest version of the model.
    """

    @property
    def id(self) -> str:
        """
        Return the qualified model name, in the format `owner/name`.
        """
        return f"{self.owner}/{self.name}"

    @property
    @deprecated("Use `model.owner` instead.")
    def username(self) -> str:
        """
        The name of the user or organization that owns the model.
        This attribute is deprecated and will be removed in future versions.
        """
        return self.owner

    @username.setter
    @deprecated("Use `model.owner` instead.")
    def username(self, value: str) -> None:
        self.owner = value

    def predict(self, *args, **kwargs) -> None:
        """
        DEPRECATED: Use `replicate.run()` instead.
        """

        raise ReplicateException(
            "The `model.predict()` method has been removed, because it's unstable: if a new version of the model you're using is pushed and its API has changed, your code may break. Use `replicate.run()` instead. See https://github.com/replicate/replicate-python#readme"
        )

    @property
    def versions(self) -> Versions:
        """
        Get the versions of this model.
        """

        return Versions(client=self._client, model=self)

    def reload(self) -> None:
        """
        Load this object from the server.
        """

        obj = self._client.models.get(f"{self.owner}/{self.name}")
        for name, value in obj.dict().items():
            setattr(self, name, value)


class Models(Namespace):
    """
    Namespace for operations related to models.
    """

    model = Model

    @property
    def predictions(self) -> "ModelsPredictions":
        """
        Get a namespace for operations related to predictions on a model.
        """

        return ModelsPredictions(client=self._client)

    def list(self, cursor: Union[str, "ellipsis", None] = ...) -> Page[Model]:  # noqa: F821
        """
        List all public models.

        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Model]: A page of of models.
        Raises:
            ValueError: If `cursor` is `None`.
        """

        if cursor is None:
            raise ValueError("cursor cannot be None")

        resp = self._client._request("GET", "/v1/models" if cursor is ... else cursor)

        obj = resp.json()
        obj["results"] = [
            _json_to_model(self._client, result) for result in obj["results"]
        ]

        return Page[Model](**obj)

    async def async_list(
        self,
        cursor: Union[str, "ellipsis", None] = ...,  # noqa: F821
    ) -> Page[Model]:
        """
        List all public models.

        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Model]: A page of of models.
        Raises:
            ValueError: If `cursor` is `None`.
        """

        if cursor is None:
            raise ValueError("cursor cannot be None")

        resp = await self._client._async_request(
            "GET", "/v1/models" if cursor is ... else cursor
        )

        obj = resp.json()
        obj["results"] = [
            _json_to_model(self._client, result) for result in obj["results"]
        ]

        return Page[Model](**obj)

    def search(self, query: str) -> Page[Model]:
        """
        Search for public models.

        Parameters:
            query: The search query.
        Returns:
            Page[Model]: A page of models matching the search query.
        """
        resp = self._client._request(
            "QUERY", "/v1/models", content=query, headers={"Content-Type": "text/plain"}
        )

        obj = resp.json()
        obj["results"] = [
            _json_to_model(self._client, result) for result in obj["results"]
        ]

        return Page[Model](**obj)

    async def async_search(self, query: str) -> Page[Model]:
        """
        Asynchronously search for public models.

        Parameters:
            query: The search query.
        Returns:
            Page[Model]: A page of models matching the search query.
        """
        resp = await self._client._async_request(
            "QUERY", "/v1/models", content=query, headers={"Content-Type": "text/plain"}
        )

        obj = resp.json()
        obj["results"] = [
            _json_to_model(self._client, result) for result in obj["results"]
        ]

        return Page[Model](**obj)

    @overload
    def get(self, key: str) -> Model: ...

    @overload
    def get(self, owner: str, name: str) -> Model: ...

    def get(self, *args, **kwargs) -> Model:
        """
        Get a model by name.
        """

        url = _get_model_url(*args, **kwargs)
        resp = self._client._request("GET", url)

        return _json_to_model(self._client, resp.json())

    @overload
    async def async_get(self, key: str) -> Model: ...

    @overload
    async def async_get(self, owner: str, name: str) -> Model: ...

    async def async_get(self, *args, **kwargs) -> Model:
        """
        Get a model by name.

        Args:
            key: The qualified name of the model, in the format `owner/name`.
        Returns:
            The model.
        """

        url = _get_model_url(*args, **kwargs)
        resp = await self._client._async_request("GET", url)

        return _json_to_model(self._client, resp.json())

    @overload
    def delete(self, key: str) -> bool: ...

    @overload
    def delete(self, owner: str, name: str) -> bool: ...

    def delete(self, *args, **kwargs) -> bool:
        """
        Delete a model by name.

        Returns:
            `True` if deletion was successful, otherwise `False`.
        """
        url = _delete_model_url(*args, **kwargs)
        resp = self._client._request("DELETE", url)
        return resp.status_code == 204

    @overload
    async def async_delete(self, key: str) -> bool: ...

    @overload
    async def async_delete(self, owner: str, name: str) -> bool: ...

    async def async_delete(self, *args, **kwargs) -> bool:
        """
        Asynchronously delete a model by name.

        Returns:
            `True` if deletion was successful, otherwise `False`.
        """
        url = _delete_model_url(*args, **kwargs)
        resp = await self._client._async_request("DELETE", url)
        return resp.status_code == 204

    class CreateModelParams(TypedDict):
        """Parameters for creating a model."""

        hardware: str
        """The SKU for the hardware used to run the model.

        Possible values can be found by calling `replicate.hardware.list()`."""

        visibility: Literal["public", "private"]
        """Whether the model should be public or private."""

        description: NotRequired[str]
        """The description of the model."""

        github_url: NotRequired[str]
        """A URL for the model's source code on GitHub."""

        paper_url: NotRequired[str]
        """A URL for the model's paper."""

        license_url: NotRequired[str]
        """A URL for the model's license."""

        cover_image_url: NotRequired[str]
        """A URL for the model's cover image."""

    def create(
        self,
        owner: str,
        name: str,
        **params: Unpack["Models.CreateModelParams"],
    ) -> Model:
        """
        Create a model.
        """

        body = _create_model_body(owner, name, **params)
        resp = self._client._request("POST", "/v1/models", json=body)

        return _json_to_model(self._client, resp.json())

    async def async_create(
        self, owner: str, name: str, **params: Unpack["Models.CreateModelParams"]
    ) -> Model:
        """
        Create a model.
        """

        body = body = _create_model_body(owner, name, **params)
        resp = await self._client._async_request("POST", "/v1/models", json=body)

        return _json_to_model(self._client, resp.json())


class ModelsPredictions(Namespace):
    """
    Namespace for operations related to predictions in a deployment.
    """

    def create(
        self,
        model: Union[str, Tuple[str, str], "Model"],
        input: Dict[str, Any],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction:
        """
        Create a new prediction with the deployment.
        """

        wait = params.pop("wait", None)
        file_encoding_strategy = params.pop("file_encoding_strategy", None)

        path = _create_prediction_path_from_model(model)
        if input is not None:
            input = encode_json(
                input,
                client=self._client,
                file_encoding_strategy=file_encoding_strategy,
            )

        body = _create_prediction_body(version=None, input=input, **params)
        extras = _create_prediction_request_params(wait=wait)
        resp = self._client._request("POST", path, json=body, **extras)

        return _json_to_prediction(self._client, resp.json())

    async def async_create(
        self,
        model: Union[str, Tuple[str, str], "Model"],
        input: Dict[str, Any],
        **params: Unpack["Predictions.CreatePredictionParams"],
    ) -> Prediction:
        """
        Create a new prediction with the deployment.
        """

        wait = params.pop("wait", None)
        file_encoding_strategy = params.pop("file_encoding_strategy", None)

        path = _create_prediction_path_from_model(model)

        if input is not None:
            input = await async_encode_json(
                input,
                client=self._client,
                file_encoding_strategy=file_encoding_strategy,
            )

        body = _create_prediction_body(version=None, input=input, **params)
        extras = _create_prediction_request_params(wait=wait)
        resp = await self._client._async_request("POST", path, json=body, **extras)

        return _json_to_prediction(self._client, resp.json())


def _create_model_body(  # pylint: disable=too-many-arguments
    owner: str,
    name: str,
    *,
    visibility: str,
    hardware: str,
    description: Optional[str] = None,
    github_url: Optional[str] = None,
    paper_url: Optional[str] = None,
    license_url: Optional[str] = None,
    cover_image_url: Optional[str] = None,
) -> Dict[str, Any]:
    body = {
        "owner": owner,
        "name": name,
        "visibility": visibility,
        "hardware": hardware,
    }

    if description is not None:
        body["description"] = description

    if github_url is not None:
        body["github_url"] = github_url

    if paper_url is not None:
        body["paper_url"] = paper_url

    if license_url is not None:
        body["license_url"] = license_url

    if cover_image_url is not None:
        body["cover_image_url"] = cover_image_url

    return body


def _get_model_url(*args, **kwargs) -> str:
    if len(args) > 0 and len(kwargs) > 0:
        raise ValueError("Cannot mix positional and keyword arguments")

    owner = kwargs.get("owner", None)
    name = kwargs.get("name", None)
    key = kwargs.get("key", None)

    if key and (owner or name):
        raise ValueError(
            "Must specify exactly one of 'owner' and 'name' or single 'key' in the format 'owner/name'"
        )

    if args:
        if len(args) == 1:
            key = args[0]
        elif len(args) == 2:
            owner, name = args
        else:
            raise ValueError("Invalid number of arguments")

    if not key:
        if not (owner and name):
            raise ValueError(
                "Both 'owner' and 'name' must be provided if 'key' is not specified."
            )
        key = f"{owner}/{name}"

    return f"/v1/models/{key}"


def _delete_model_url(*args, **kwargs) -> str:
    return _get_model_url(*args, **kwargs)


def _json_to_model(client: "Client", json: Dict[str, Any]) -> Model:
    model = Model(**json)
    model._client = client
    if model.default_example is not None:
        model.default_example._client = client
    return model


def _create_prediction_path_from_model(
    model: Union[str, Tuple[str, str], "Model"],
) -> str:
    owner, name = None, None
    if isinstance(model, Model):
        owner, name = model.owner, model.name
    elif isinstance(model, tuple):
        owner, name = model[0], model[1]
    elif isinstance(model, str):
        owner, name, version_id = ModelVersionIdentifier.parse(model)
        if version_id is not None:
            raise ValueError(
                f"Invalid reference to model version: {model}. Expected model or reference in the format owner/name"
            )

    if owner is None or name is None:
        raise ValueError(
            "model must be a Model, a tuple of (owner, name), or a string in the format 'owner/name'"
        )

    return f"/v1/models/{owner}/{name}/predictions"
