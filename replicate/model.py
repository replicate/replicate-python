from typing import Optional

from replicate.resource import Namespace, Resource

from .prediction import Prediction
from .version import Version, Versions, AsyncVersions


class Model(Resource):
    """A machine learning model hosted on Replicate."""

    owner: str
    """The name of the user or organization that owns the model."""

    name: str
    """The name of the model."""

    description: Optional[str] = None

    visibility: str

    github_url: Optional[str] = None

    paper_url: Optional[str] = None

    license_url: Optional[str] = None

    run_count: int

    cover_image_url: Optional[str] = None

    default_example: Optional[Prediction] = None

    latest_version: Optional[Version] = None


class Models(Namespace):
    model = Model

    def get(self, owner_name: str, model_name: str) -> Model:
        """Get a model by name.

        Args:
            name: The name of the model, in the format `owner/model-name`.
        Returns:
            The model.
        """

        resp = self._client.request("GET", f"/models/{owner_name}/{model_name}")

        return Model(**resp.json())

    @property
    def versions(self) -> Versions:
        return Versions(client=self._client)


class AsyncModels(Models):
    async def get(self, owner_name: str, model_name: str) -> Model:
        resp = await self._client.request("GET", f"/models/{owner_name}/{model_name}")

        return Model(**resp.json())
    
    @property
    def versions(self) -> AsyncVersions:
        return AsyncVersions(client=self._client)
