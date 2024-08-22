from replicate.client import Client
from replicate.pagination import async_paginate as _async_paginate
from replicate.pagination import paginate as _paginate

default_client = Client()

run = default_client.run
async_run = default_client.async_run

stream = default_client.stream
async_stream = default_client.async_stream

paginate = _paginate
async_paginate = _async_paginate

collections = default_client.collections
deployments = default_client.deployments
files = default_client.files
hardware = default_client.hardware
models = default_client.models
predictions = default_client.predictions
trainings = default_client.trainings
webhooks = default_client.webhooks
