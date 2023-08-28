import os

import pytest


@pytest.fixture(scope="module")
def vcr_config():
    return {"allowed_hosts": ["api.replicate.com"], "filter_headers": ["authorization"]}


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    module = request.node.fspath
    return os.path.join(module.dirname, "cassettes")
