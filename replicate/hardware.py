from typing import TYPE_CHECKING, Any, Dict, List

from typing_extensions import deprecated

from replicate.resource import Namespace, Resource

if TYPE_CHECKING:
    pass


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


class HardwareNamespace(Namespace):
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

        return [_json_to_hardware(entry) for entry in obj]

    async def async_list(self) -> List[Hardware]:
        """
        List all hardware available for you to run models on Replicate.

        Returns:
            List[Hardware]: A list of hardware.
        """

        resp = await self._client._async_request("GET", "/v1/hardware")
        obj = resp.json()

        return [_json_to_hardware(entry) for entry in obj]


def _json_to_hardware(json: Dict[str, Any]) -> Hardware:
    return Hardware(**json)
