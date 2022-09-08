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
            time.sleep(0.5)
            self.reload()

    def output_iterator(self) -> Iterator[Any]:
        # TODO: check output is list
        previous_output = self.output or []
        while self.status not in ["succeeded", "failed", "canceled"]:
            output = self.output or []
            new_output = output[len(previous_output) :]
            for output in new_output:
                yield output
            previous_output = output
            time.sleep(0.5)
            self.reload()

        if self.status == "failed":
            raise ModelError(self.error)

        output = self.output or []
        new_output = output[len(previous_output) :]
        for output in new_output:
            yield output

    def cancel(self):
        """Cancel a currently running prediction"""
        self._client._request("POST", f"/v1/predictions/{self.id}/cancel")


class PredictionCollection(Collection):
    model = Prediction

    def create(
        self,
        version: Version,
        input: Dict[str, Any],
        webhook_completed: Optional[str] = None,
    ) -> Prediction:
        input = encode_json(input, upload_file=upload_file)
        body = {
            "version": version.id,
            "input": input,
        }
        if webhook_completed is not None:
            body["webhook_completed"] = webhook_completed

        resp = self._client._request(
            "POST",
            "/v1/predictions",
            json=body,
        )
        obj = resp.json()
        obj["version"] = version
        return self.prepare_model(obj)

    def get(self, id: str) -> Prediction:
        resp = self._client._request("GET", f"/v1/predictions/{id}")
        obj = resp.json()
        # HACK: resolve this? make it lazy somehow?
        del obj["version"]
        return self.prepare_model(obj)

    def list(self) -> List[Prediction]:
        resp = self._client._request("GET", f"/v1/predictions")
        # TODO: paginate
        predictions = resp.json()["results"]
        for prediction in predictions:
            # HACK: resolve this? make it lazy somehow?
            del prediction["version"]
        return [self.prepare_model(obj) for obj in predictions]
