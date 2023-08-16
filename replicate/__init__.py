import os

from .client import AsyncClient, Client

default_client = Client(api_token=os.environ.get("REPLICATE_API_TOKEN"))
run = default_client.run
collections = default_client.collections
models = default_client.models
predictions = default_client.predictions
trainings = default_client.trainings

default_async_client = AsyncClient(api_token=os.environ.get("REPLICATE_API_TOKEN"))
async_run = default_async_client.run
async_collections = default_async_client.collections
async_models = default_async_client.models
async_predictions = default_async_client.predictions
async_trainings = default_async_client.trainings
