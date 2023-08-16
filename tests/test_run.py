import pytest

import replicate
from replicate.version import InvalidVersionIdentifierError


@pytest.mark.vcr("run.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_run(async_flag):
    version = "a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5"

    input = {
        "prompt": "a studio photo of a rainbow colored corgi",
        "width": 512,
        "height": 512,
        "seed": 42069,
    }

    if async_flag:
        output = await replicate.async_run(
            f"stability-ai/sdxl:{version}",
            input,
            poll_interval=1e-4,
        )
    else:
        output = replicate.run(
            f"stability-ai/sdxl:{version}",
            input,
            poll_interval=1e-4,
        )

    assert output is not None
    assert isinstance(output, list)
    assert len(output) > 0
    assert output[0].startswith("https://")


@pytest.mark.vcr
def test_run_with_invalid_identifier():
    with pytest.raises(InvalidVersionIdentifierError):
        replicate.run("invalid", {})
