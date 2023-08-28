import pytest

import replicate
from replicate.exceptions import ReplicateError


@pytest.mark.vcr("run.yaml")
@pytest.mark.asyncio
async def test_run():
    version = "a00d0b7dcbb9c3fbb34ba87d2d5b46c56969c84a628bf778a7fdaec30b1b99c5"

    input = {
        "prompt": "a studio photo of a rainbow colored corgi",
        "width": 512,
        "height": 512,
        "seed": 42069,
    }

    output = replicate.run(
        f"stability-ai/sdxl:{version}",
        input=input,
    )

    assert output is not None
    assert isinstance(output, list)
    assert len(output) > 0
    assert output[0].startswith("https://")


@pytest.mark.vcr
def test_run_with_invalid_identifier():
    with pytest.raises(ReplicateError):
        replicate.run("invalid")
