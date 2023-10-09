from typing import Dict, List, Optional, Union

from typing_extensions import deprecated

from replicate.base_model import BaseModel
from replicate.collection import Collection
from replicate.exceptions import ReplicateException
from replicate.prediction import Prediction
from replicate.version import Version, VersionCollection


class Model(BaseModel):
    """
    A machine learning model hosted on Replicate.
    """

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
    def versions(self) -> VersionCollection:
        """
        Get the versions of this model.
        """

        return VersionCollection(client=self._client, model=self)


class ModelCollection(Collection):
    model = Model

    def list(self) -> List[Model]:
        """
        List all public models.

        Returns:
            A list of models.
        """

        resp = self._client._request("GET", "/v1/models")
        # TODO: paginate
        models = resp.json()["results"]
        return [self.prepare_model(obj) for obj in models]

    def get(self, key: str) -> Model:
        """
        Get a model by name.

        Args:
            key: The qualified name of the model, in the format `owner/model-name`.
        Returns:
            The model.
        """

        resp = self._client._request("GET", f"/v1/models/{key}")
        return self.prepare_model(resp.json())

    def create(self, **kwargs) -> Model:
        raise NotImplementedError()

    def prepare_model(self, attrs: Union[Model, Dict]) -> Model:
        if isinstance(attrs, BaseModel):
            attrs.id = f"{attrs.owner}/{attrs.name}"
        elif isinstance(attrs, dict):
            attrs["id"] = f"{attrs['owner']}/{attrs['name']}"

            if attrs is not None:
                if "default_example" in attrs and attrs["default_example"]:
                    attrs["default_example"].pop("version")

                if "latest_version" in attrs and attrs["latest_version"] == {}:
                    attrs.pop("latest_version")

        model = super().prepare_model(attrs)

        if model.default_example is not None:
            model.default_example._client = self._client

        if model.latest_version is not None:
            model.latest_version._client = self._client

        return model
