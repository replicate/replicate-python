import datetime
import warnings
from typing import TYPE_CHECKING, Any, Iterator, List, Union

if TYPE_CHECKING:
    from replicate.client import Client
    from replicate.model import Model


from replicate.base_model import BaseModel
from replicate.collection import Collection
from replicate.exceptions import ModelError
from replicate.schema import make_schema_backwards_compatible


class Version(BaseModel):
    id: str
    created_at: datetime.datetime
    cog_version: str
    openapi_schema: dict

    def predict(self, **kwargs) -> Union[Any, Iterator[Any]]:
        warnings.warn(
            "version.predict() is deprecated. Use replicate.run() instead. It will be removed before version 1.0.",
            DeprecationWarning,
            stacklevel=1,
        )

        prediction = self._client.predictions.create(version=self, input=kwargs)
        # Return an iterator of the output
        schema = self.get_transformed_schema()
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

    def get_transformed_schema(self) -> dict:
        schema = self.openapi_schema
        schema = make_schema_backwards_compatible(schema, self.cog_version)
        return schema


class VersionCollection(Collection):
    model = Version

    def __init__(self, client: "Client", model: "Model") -> None:
        super().__init__(client=client)
        self._model = model

    # doesn't exist yet
    def get(self, id: str) -> Version:
        """
        Get a specific version.
        """
        resp = self._client._request(
            "GET", f"/v1/models/{self._model.username}/{self._model.name}/versions/{id}"
        )
        return self.prepare_model(resp.json())

    def create(self, **kwargs) -> Version:
        raise NotImplementedError()

    def list(self) -> List[Version]:
        """
        Return a list of all versions for a model.
        """
        resp = self._client._request(
            "GET", f"/v1/models/{self._model.username}/{self._model.name}/versions"
        )
        return [self.prepare_model(obj) for obj in resp.json()["results"]]
