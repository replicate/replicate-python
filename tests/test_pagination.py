import pytest

import replicate


@pytest.mark.asyncio
async def test_paginate_with_none_cursor(mock_replicate_api_token):
    with pytest.raises(ValueError):
        replicate.models.list(None)


@pytest.mark.vcr("collections-list.yaml")
@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_paginate(async_flag):
    found = False

    if async_flag:
        async for page in replicate.async_paginate(replicate.collections.async_list):
            assert page.next is None
            assert page.previous is None

            for collection in page:
                if collection.slug == "text-to-image":
                    found = True
                    break

    else:
        for page in replicate.paginate(replicate.collections.list):
            assert page.next is None
            assert page.previous is None

            for collection in page:
                if collection.slug == "text-to-image":
                    found = True
                    break

    assert found
