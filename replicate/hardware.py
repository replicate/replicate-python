from typing import Dict, List, Union

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


class Hardwares(Namespace):
    """
    Namespace for operations related to hardware.
    """

    model = Hardware

    def list(self) -> List[Hardware]:
        """
        List all hardware available for you to run models on Replicate.

        Returns:
            List[Hardware]: A list of hardware.
        """

        resp = self._client._request("GET", "/v1/hardware")
        return [self._prepare_model(obj) for obj in resp.json()]

    def _prepare_model(self, attrs: Union[Hardware, Dict]) -> Hardware:
        if isinstance(attrs, Resource):
            attrs.id = attrs.sku
        elif isinstance(attrs, dict):
            attrs["id"] = attrs["sku"]

        return super()._prepare_model(attrs)
