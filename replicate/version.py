import datetime
from typing import Any, Iterator, List, Union

import requests

from replicate.base_model import BaseModel
from replicate.collection import Collection
from replicate.exceptions import ModelError
from replicate.schema import make_schema_backwards_compatible, map_items


def _process_output_item(schema, value):
    if schema.get("type") == "string" and schema.get("format") == "uri":
        # TODO: make request with client to pass auth, only for replicate.com URLs so as not to leak token
        return requests.get(value, stream=True).raw
    return value


def _process_output(schema, value):
    return map_items(_process_output_item, schema, value)


class Version(BaseModel):
    id: str
    created_at: datetime.datetime
    cog_version: str
    openapi_schema: Any

    def predict(self, **kwargs) -> Union[Any, Iterator[Any]]:
        # TODO: support args
        prediction = self._client.predictions.create(version=self, input=kwargs)
        # Return an iterator of the output
        # FIXME: might just be a list, not an iterator. I wonder if we should differentiate?
        schema = self.get_transformed_schema()
        output_schema = schema["components"]["schemas"]["Output"]
        if (
            output_schema.get("type") == "array"
            and output_schema.get("x-cog-array-type") == "iterator"
        ):
            return prediction.output_iterator()

        prediction.wait()
        if prediction.status == "failed":
            raise ModelError(prediction.error)

        return _process_output(output_schema, prediction.output)

    def get_transformed_schema(self):
        schema = self.openapi_schema
        schema = make_schema_backwards_compatible(schema, self.cog_version)
        return schema


class VersionCollection(Collection):
    model = Version

    def __init__(self, client, model):
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

    def list(self) -> List[Version]:
        """
        Return a list of all versions for a model.
        """
        resp = self._client._request(
            "GET", f"/v1/models/{self._model.username}/{self._model.name}/versions"
        )
        return [self.prepare_model(obj) for obj in resp.json()["results"]]
