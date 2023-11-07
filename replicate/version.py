import datetime
import warnings
from typing import TYPE_CHECKING, Any, Iterator, List, Union

if TYPE_CHECKING:
    from replicate.client import Client
    from replicate.model import Model


from replicate.exceptions import ModelError
from replicate.resource import Namespace, Resource
from replicate.schema import make_schema_backwards_compatible


class Version(Resource):
    """
    A version of a model.
    """

    _namespace: "Versions"

    id: str
    """The unique ID of the version."""

    created_at: datetime.datetime
    """When the version was created."""

    cog_version: str
    """The version of the Cog used to create the version."""

    openapi_schema: dict
    """An OpenAPI description of the model inputs and outputs."""

    def predict(self, **kwargs) -> Union[Any, Iterator[Any]]:  # noqa: ANN401
        """
        DEPRECATED: Use `replicate.run()` instead.

        Create a prediction using this model version.

        Args:
            kwargs: The input to the model.
        Returns:
            The output of the model.
        """

        warnings.warn(
            "version.predict() is deprecated. Use replicate.run() instead. It will be removed before version 1.0.",
            DeprecationWarning,
            stacklevel=1,
        )

        prediction = self._client.predictions.create(version=self, input=kwargs)  # pylint: disable=no-member
        # Return an iterator of the output
        schema = make_schema_backwards_compatible(self.openapi_schema, self.cog_version)
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

    def reload(self) -> None:
        """
        Load this object from the server.
        """

        obj = self._namespace.get(self.id)  # pylint: disable=no-member
        for name, value in obj.dict().items():
            setattr(self, name, value)


class Versions(Namespace):
    """
    Namespace for operations related to model versions.
    """

    model = Version

    def __init__(self, client: "Client", model: "Model") -> None:
        super().__init__(client=client)
        self._model = model

    def get(self, id: str) -> Version:  # pylint: disable=invalid-name
        """
        Get a specific model version.

        Args:
            id: The version ID.
        Returns:
            The model version.
        """
        resp = self._client._request(
            "GET", f"/v1/models/{self._model.owner}/{self._model.name}/versions/{id}"
        )
        return self._prepare_model(resp.json())

    def list(self) -> List[Version]:
        """
        Return a list of all versions for a model.

        Returns:
            List[Version]: A list of version objects.
        """
        resp = self._client._request(
            "GET", f"/v1/models/{self._model.owner}/{self._model.name}/versions"
        )
        return [self._prepare_model(obj) for obj in resp.json()["results"]]
