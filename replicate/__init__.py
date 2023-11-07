from replicate.client import Client

default_client = Client()
run = default_client.run
collections = default_client.collections
hardware = default_client.hardware
deployments = default_client.deployments
models = default_client.models
predictions = default_client.predictions
trainings = default_client.trainings
