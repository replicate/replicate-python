import time
from typing import Any, Dict, Iterator, List, Optional

from replicate.base_model import BaseModel
from replicate.collection import Collection
from replicate.exceptions import ModelError, ReplicateException
from replicate.files import upload_file
from replicate.json import encode_json
from replicate.version import Version


class Prediction(BaseModel):
    id: str
    error: Optional[str]
    input: Optional[Dict[str, Any]]
    logs: Optional[str]
    output: Optional[Any]
    status: str
    version: Optional[Version]

    def wait(self):
        """Wait for prediction to finish."""
        while self.status not in ["succeeded", "failed", "canceled"]:
            time.sleep(0.1)
            self.reload()

    def output_iterator(self) -> Iterator[Any]:
        # TODO: check output is list
        previous_output = self.output or []
        while self.status not in ["succeeded", "failed"]:
            if self.status == "failed":
                raise ModelError(self.error)
            output = self.output or []
            new_output = output[len(previous_output) :]
            for output in new_output:
                yield output
            previous_output = output
            time.sleep(0.1)
            self.reload()
        output = self.output or []
        new_output = output[len(previous_output) :]
        for output in new_output:
            yield output

    def cancel(self):
        """ Cancel a currently running prediction """
        resp = self._client._post(f"/v1/predictions/{self.id}/cancel")
        resp.raise_for_status()


class PredictionCollection(Collection):
    model = Prediction

    def create(self, version: Version, input: Dict[str, Any]) -> Prediction:
        input = encode_json(input, upload_file=upload_file)
        resp = self._client._post(
            "/v1/predictions", json={"version": version.id, "input": input}
        )
        resp.raise_for_status()
        obj = resp.json()
        obj["version"] = version
        return self.prepare_model(obj)

    def get(self, id: str) -> Prediction:
        resp = self._client._get(f"/v1/predictions/{id}")
        resp.raise_for_status()
        obj = resp.json()
        # HACK: resolve this? make it lazy somehow?
        del obj["version"]
        return self.prepare_model(obj)

    def list(self) -> List[Prediction]:
        resp = self._client._get(f"/v1/predictions")
        resp.raise_for_status()
        # TODO: paginate
        predictions = resp.json()["results"]
        for prediction in predictions:
            # HACK: resolve this? make it lazy somehow?
            del prediction["version"]
        return [self.prepare_model(obj) for obj in predictions]
