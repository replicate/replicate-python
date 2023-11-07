from typing import Any, Dict, List

from typing_extensions import deprecated

from replicate.resource import Namespace, Resource


class Hardware(Resource):
    """
    Hardware for running a model on Replicate.
    """

    sku: str
    """
    The SKU of the hardware.
    """

    name: str
    """
    The name of the hardware.
    """

    @property
    @deprecated("Use `sku` instead of `id`")
    def id(self) -> str:
        """
        DEPRECATED: Use `sku` instead.
        """
        return self.sku


class Hardwares(Namespace):
    """
    Namespace for operations related to hardware.
    """

    def list(self) -> List[Hardware]:
        """
        List all hardware available for you to run models on Replicate.

        Returns:
            List[Hardware]: A list of hardware.
        """

        resp = self._client._request("GET", "/v1/hardware")
        obj = resp.json()

        return [self._json_to_hardware(entry) for entry in obj]

    def _json_to_hardware(self, json: Dict[str, Any]) -> Hardware:
        return Hardware(**json)
