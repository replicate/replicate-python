from typing import Dict, List, Union

from replicate.base_model import BaseModel
from replicate.collection import Collection


class Hardware(BaseModel):
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


class HardwareCollection(Collection):
    """
    Namespace for operations related to hardware.
    """

    model = Hardware

    def list(self) -> List[Hardware]:
        """
        List all public models.

        Returns:
            A list of models.
        """

        resp = self._client._request("GET", "/v1/hardware")
        hardware = resp.json()
        return [self._prepare_model(obj) for obj in hardware]

    def _prepare_model(self, attrs: Union[Hardware, Dict]) -> Hardware:
        if isinstance(attrs, BaseModel):
            attrs.id = attrs.sku
        elif isinstance(attrs, dict):
            attrs["id"] = attrs["sku"]

        hardware = super()._prepare_model(attrs)

        return hardware
