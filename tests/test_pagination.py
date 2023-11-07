import pytest

import replicate


@pytest.mark.asyncio
async def test_paginate_with_none_cursor(mock_replicate_api_token):
    with pytest.raises(ValueError):
        replicate.models.list(None)
