# Replicate Python client

This is a Python client for Replicate. It lets you run models from your Python code or Jupyter notebook, and do various other things on Replicate.

You can run a model and get its output:

```python
>>> import replicate

>>> model = replicate.models.get("bfirsh/resnet")
>>> model.predict(input=open("mystery.jpg"))
[('n02123597', 'Siamese_cat', 0.88293666), ('n02123394', 'Persian_cat', 0.09810519), ('n02123045', 'tabby', 0.0057580653)]
```

You can run a model and feed the output into another model:

```python
>>> image = replicate.models.get("afiaka87/clip-guided-diffusion".predict(prompt="avocado armchair")
>>> upscaled_image = replicate.models.get("jingyunliang/swinir").predict(image=image)
```

Run a model and get its output while it's running:

```python
model = replicate.models.get("pixray/text2image")
for image in model.predict(prompt="san francisco sunset"):
    display(image)
```

You can start a model and run it in the background:

```python
>>> prediction = replicate.predictions.create(
...    version="kvfrans/clipdraw",
...    input={"prompt":"Watercolor painting of an underwater submarine"})

>>> prediction
<Prediction 38a73e57ddb9 on kvfrans/clipdraw:8b0ba5ab4d85>

>>> prediction.status
Prediction.STATUS_RUNNING

>>> prediction.logs
["something happened"]

>>> dict(prediction)
{"id": "...", "status": "running", ...}

>>> prediction.reload()
>>> prediction.logs
["something happened", "another thing happened"]

>>> prediction.wait()

>>> prediction.status
Prediction.STATUS_SUCCESSFUL

>>> prediction.output
<file: output.png>
```

You can list all the predictions you've run:

```
>>> replicate.predictions.list()
[<Prediction: 8b0ba5ab4d85>, <Prediction: 494900564e8c>]
```

## Install

```bash
pip install -e .
```

## Authentication

Set the `REPLICATE_API_TOKEN` environment variable to your API token.
