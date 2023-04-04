import re
import time
from typing import Any, Dict, Iterator, List, Optional

from replicate.base_model import BaseModel
from replicate.collection import Collection
from replicate.exceptions import ModelError, ReplicateException
from replicate.files import upload_file
from replicate.json import encode_json
from replicate.version import Version


class Training(BaseModel):
    completed_at: Optional[str]
    created_at: Optional[str]
    destination: Optional[str]
    error: Optional[str]
    id: str
    input: Optional[Dict[str, Any]]
    logs: Optional[str]
    output: Optional[Any]
    started_at: Optional[str]
    status: str
    version: str

    def cancel(self):
        """Cancel a running training"""
        self._client._request("POST", f"/v1/trainings/{self.id}/cancel")


class TrainingCollection(Collection):
    model = Training

    def create(
        self,
        version: str,
        input: Dict[str, Any],
        destination: str,
        webhook: Optional[str] = None,
        webhook_events_filter: Optional[List[str]] = None,
    ) -> Training:
        input = encode_json(input, upload_file=upload_file)
        body = {
            "input": input,
            "destination": destination,
        }
        if webhook is not None:
            body["webhook"] = webhook
        if webhook_events_filter is not None:
            body["webhook_events_filter"] = webhook_events_filter

        # Split version in format "username/model_name:version_id"
        match = re.match(
            r"^(?P<username>[^/]+)/(?P<model_name>[^:]+):(?P<version_id>.+)$", version
        )
        if not match:
            raise ReplicateException(
                f"version must be in format username/model_name:version_id"
            )
        username = match.group("username")
        model_name = match.group("model_name")
        version_id = match.group("version_id")

        resp = self._client._request(
            "POST",
            f"/v1/models/{username}/{model_name}/versions/{version_id}/trainings",
            json=body,
        )
        obj = resp.json()
        return self.prepare_model(obj)

    def get(self, id: str) -> Training:
        resp = self._client._request(
            "GET",
            f"/v1/trainings/{id}",
        )
        obj = resp.json()
        return self.prepare_model(obj)
