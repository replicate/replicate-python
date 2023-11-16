import pytest

import replicate


@pytest.mark.vcr("collections-list.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_collections_list(async_flag):
    if async_flag:
        page = await replicate.collections.async_list()
    else:
        page = replicate.collections.list()

    assert page.next is None
    assert page.previous is None

    found = False
    for collection in page.results:
        if collection.slug == "text-to-image":
            found = True
            break

    assert found


@pytest.mark.vcr("collections-get.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_collections_get(async_flag):
    if async_flag:
        collection = await replicate.collections.async_get("text-to-image")
    else:
        collection = replicate.collections.get("text-to-image")

    assert collection.slug == "text-to-image"
    assert collection.name == "Text to image"
    assert collection.models is not None
    assert len(collection.models) > 0

    found = False
    for model in collection.models:
        if model.name == "stable-diffusion":
            found = True
            break

    assert found
