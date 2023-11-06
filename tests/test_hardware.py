import pytest

import replicate


@pytest.mark.vcr("hardware-list.yaml")
@pytest.mark.asyncio
async def test_hardware_list(mock_replicate_api_token):
    hardware = replicate.hardware.list()

    assert hardware is not None
    assert isinstance(hardware, list)
    assert len(hardware) > 0
