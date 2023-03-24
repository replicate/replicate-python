# Replicate Python client

This is a Python client for [Replicate](https://replicate.com). It lets you run models from your Python code or Jupyter notebook, and do various other things on Replicate.

## Install

```sh
pip install replicate
```

## Authenticate

Before running any Python scripts that use the API, you need to set your Replicate API token in your environment.

Grab your token from [replicate.com/account](https://replicate.com/account) and set it as an environment variable:

```
export REPLICATE_API_TOKEN=<your token>
```

We recommend not adding the token directly to your source code, because you don't want to put your credentials in source control. If anyone used your API key, their usage would be charged to your account.

## Run a model

Create a new Python file and add the following code:

```python
import replicate
model = replicate.models.get("stability-ai/stable-diffusion")
version = model.versions.get("27b93a2413e7f36cd83da926f3656280b2931564ff050bf9575f1fdf9bcd7478")
version.predict(prompt="a 19th century portrait of a wombat gentleman")

# ['https://replicate.com/api/models/stability-ai/stable-diffusion/files/50fcac81-865d-499e-81ac-49de0cb79264/out-0.png']
```

Some models, like [methexis-inc/img2prompt](https://replicate.com/methexis-inc/img2prompt), receive images as inputs. To pass a file as an input, use a file handle or URL:

```python
model = replicate.models.get("methexis-inc/img2prompt")
version = model.versions.get("50adaf2d3ad20a6f911a8a9e3ccf777b263b8596fbd2c8fc26e8888f8a0edbb5")
inputs = {
    "image": open("path/to/mystery.jpg", "rb"),
}
output = version.predict(**inputs)

# [['n02123597', 'Siamese_cat', 0.8829364776611328],
#  ['n02123394', 'Persian_cat', 0.09810526669025421],
#  ['n02123045', 'tabby', 0.005758069921284914]]
```

## Compose models into a pipeline

You can run a model and feed the output into another model:

```python
laionide = replicate.models.get("afiaka87/laionide-v4").versions.get("b21cbe271e65c1718f2999b038c18b45e21e4fba961181fbfae9342fc53b9e05")
swinir = replicate.models.get("jingyunliang/swinir").versions.get("660d922d33153019e8c263a3bba265de882e7f4f70396546b6c9c8f9d47a021a")
image = laionide.predict(prompt="avocado armchair")
upscaled_image = swinir.predict(image=image)
```

## Get output from a running model

Run a model and get its output while it's running:

```python
model = replicate.models.get("pixray/text2image")
version = model.versions.get("5c347a4bfa1d4523a58ae614c2194e15f2ae682b57e3797a5bb468920aa70ebf")
for image in version.predict(prompts="san francisco sunset"):
    display(image)
```

## Run a model in the background

You can start a model and run it in the background:

```python
model = replicate.models.get("kvfrans/clipdraw")
version = model.versions.get("5797a99edc939ea0e9242d5e8c9cb3bc7d125b1eac21bda852e5cb79ede2cd9b")
prediction = replicate.predictions.create(
    version=version,
    input={"prompt":"Watercolor painting of an underwater submarine"})

# >>> prediction
# Prediction(...)

# >>> prediction.status
# 'starting'

# >>> dict(prediction)
# {"id": "...", "status": "starting", ...}

# >>> prediction.reload()
# >>> prediction.status
# 'processing'

# >>> print(prediction.logs)
# iteration: 0, render:loss: -0.6171875
# iteration: 10, render:loss: -0.92236328125
# iteration: 20, render:loss: -1.197265625
# iteration: 30, render:loss: -1.3994140625

# >>> prediction.wait()

# >>> prediction.status
# 'succeeded'

# >>> prediction.output
# 'https://.../output.png'
```

## Cancel a prediction

You can cancel a running prediction:

```python
model = replicate.models.get("kvfrans/clipdraw")
version = model.versions.get("5797a99edc939ea0e9242d5e8c9cb3bc7d125b1eac21bda852e5cb79ede2cd9b")
prediction = replicate.predictions.create(
    version=version,
    input={"prompt":"Watercolor painting of an underwater submarine"})

# >>> prediction.status
# 'starting'

# >>> prediction.cancel()

# >>> prediction.reload()
# >>> prediction.status
# 'canceled'
```

## List predictions

You can list all the predictions you've run:

```python
replicate.predictions.list()
# [<Prediction: 8b0ba5ab4d85>, <Prediction: 494900564e8c>]
```

## Load output files

Output files are returned as HTTPS URLs. You can load an output file as a buffer:

```python
import replicate
from urllib.request import urlretrieve

model = replicate.models.get("stability-ai/stable-diffusion")
version = model.versions.get("27b93a2413e7f36cd83da926f3656280b2931564ff050bf9575f1fdf9bcd7478")
out = version.predict(prompt="wavy colorful abstract patterns, cgsociety"
urlretrieve(out[0], "/tmp/out.png")
background = Image.open("/tmp/out.png")
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md)
