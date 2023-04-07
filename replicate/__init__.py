from .client import Client

default_client = Client()
run = default_client.run
models = default_client.models
predictions = default_client.predictions
trainings = default_client.trainings
