from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, Union

from typing_extensions import NotRequired, TypedDict, Unpack, deprecated

from replicate.exceptions import ReplicateException
from replicate.pagination import Page
from replicate.prediction import Prediction
from replicate.resource import Namespace, Resource
from replicate.version import Version, Versions

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore


if TYPE_CHECKING:
    from replicate.client import Client


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

    def get(self, key: str) -> Model:
        """
        Get a model by name.

        Args:
            key: The qualified name of the model, in the format `owner/model-name`.
        Returns:
            The model.
        """

        resp = self._client._request("GET", f"/v1/models/{key}")

        return _json_to_model(self._client, resp.json())

    async def async_get(self, key: str) -> Model:
        """
        Get a model by name.

        Args:
            key: The qualified name of the model, in the format `owner/model-name`.
        Returns:
            The model.
        """

        resp = await self._client._async_request("GET", f"/v1/models/{key}")

        return _json_to_model(self._client, resp.json())

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


def _json_to_model(client: "Client", json: Dict[str, Any]) -> Model:
    model = Model(**json)
    model._client = client
    if model.default_example is not None:
        model.default_example._client = client
    return model
