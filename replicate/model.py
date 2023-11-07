from typing import Dict, Optional, Union

from typing_extensions import deprecated

from replicate.exceptions import ReplicateException
from replicate.pagination import Page
from replicate.prediction import Prediction
from replicate.resource import Namespace, Resource
from replicate.version import Version, Versions


class Model(Resource):
    """
    A machine learning model hosted on Replicate.
    """

    _namespace: "Models"

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

    visibility: str
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

        obj = self._namespace.get(f"{self.owner}/{self.name}")  # pylint: disable=no-member
        for name, value in obj.dict().items():
            setattr(self, name, value)


class Models(Namespace):
    """
    Namespace for operations related to models.
    """

    model = Model

    def list(self, cursor: Union[str, "ellipsis"] = ...) -> Page[Model]:  # noqa: F821
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
        return Page[Model](self._client, self, **resp.json())

    def get(self, key: str) -> Model:
        """
        Get a model by name.

        Args:
            key: The qualified name of the model, in the format `owner/model-name`.
        Returns:
            The model.
        """

        resp = self._client._request("GET", f"/v1/models/{key}")
        return self._prepare_model(resp.json())

    def create(  # pylint: disable=arguments-differ disable=too-many-arguments
        self,
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
    ) -> Model:
        """
        Create a model.

        Args:
            owner: The name of the user or organization that will own the model.
            name: The name of the model.
            visibility: Whether the model should be public or private.
            hardware: The SKU for the hardware used to run the model. Possible values can be found by calling `replicate.hardware.list()`.
            description: A description of the model.
            github_url: A URL for the model's source code on GitHub.
            paper_url: A URL for the model's paper.
            license_url: A URL for the model's license.
            cover_image_url: A URL for the model's cover image.

        Returns:
            The created model.
        """

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

        resp = self._client._request("POST", "/v1/models", json=body)

        return self._prepare_model(resp.json())

    def _prepare_model(self, attrs: Union[Model, Dict]) -> Model:
        if isinstance(attrs, Resource):
            attrs.id = f"{attrs.owner}/{attrs.name}"
        elif isinstance(attrs, dict):
            attrs["id"] = f"{attrs['owner']}/{attrs['name']}"

            if attrs is not None:
                if "default_example" in attrs and attrs["default_example"]:
                    attrs["default_example"].pop("version")

                if "latest_version" in attrs and attrs["latest_version"] == {}:
                    attrs.pop("latest_version")

        model = super()._prepare_model(attrs)

        if model.default_example is not None:
            model.default_example._client = self._client

        if model.latest_version is not None:
            model.latest_version._client = self._client

        return model
