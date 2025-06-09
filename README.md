# Replicate Python client

This is a Python client for [Replicate](https://replicate.com). It lets you run models from your Python code or Jupyter notebook, and do various other things on Replicate.

## Breaking Changes in 1.0.0

The 1.0.0 release contains breaking changes:

- The `replicate.run()` method now returns `FileOutput`s instead of URL strings by default for models that output files. `FileOutput` implements an iterable interface similar to `httpx.Response`, making it easier to work with files efficiently.

To revert to the previous behavior, you can opt out of `FileOutput` by passing `use_file_output=False` to `replicate.run()`:

```python
output = replicate.run("acmecorp/acme-model", use_file_output=False)
```

In most cases, updating existing applications to call `output.url` should resolve any issues. But we recommend using the `FileOutput` objects directly as we have further improvements planned to this API and this approach is guaranteed to give the fastest results.

> [!TIP]
> **👋** Check out an interactive version of this tutorial on [Google Colab](https://colab.research.google.com/drive/1K91q4p-OhL96FHBAVLsv9FlwFdu6Pn3c).
>
> [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1K91q4p-OhL96FHBAVLsv9FlwFdu6Pn3c)

## Requirements

- Python 3.8+

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

<details>

<summary>Alternative authentication</summary>

As of [replicate 1.0.7](https://github.com/replicate/replicate-python/releases/tag/1.0.7) and [cog 0.14.11](https://github.com/replicate/cog/releases/tag/v0.14.11) it is possible to pass a `REPLICATE_API_TOKEN` via the `context` as part of a prediction request.

The `Replicate()` constructor will now use this context when available. This grants cog models the ability to use the Replicate client libraries, scoped to a user on a per request basis.

</details>

## Run a model

Create a new Python file and add the following code, replacing the model identifier and input with your own:

```python
>>> import replicate
>>> outputs = replicate.run(
        "black-forest-labs/flux-schnell",
        input={"prompt": "astronaut riding a rocket like a horse"}
    )
[<replicate.helpers.FileOutput object at 0x107179b50>]
>>> for index, output in enumerate(outputs):
        with open(f"output_{index}.webp", "wb") as file:
            file.write(output.read())
```

`replicate.run` raises `ModelError` if the prediction fails.
You can access the exception's `prediction` property 
to get more information about the failure.

```python
import replicate
from replicate.exceptions import ModelError

try:
  output = replicate.run("stability-ai/stable-diffusion-3", { "prompt": "An astronaut riding a rainbow unicorn" })
except ModelError as e
  if "(some known issue)" in e.prediction.logs:
    pass

  print("Failed prediction: " + e.prediction.id)
```

> [!NOTE]
> By default the Replicate client will hold the connection open for up to 60 seconds while waiting
> for the prediction to complete. This is designed to optimize getting the model output back to the
> client as quickly as possible.
>
> The timeout can be configured by passing `wait=x` to `replicate.run()` where `x` is a timeout
> in seconds between 1 and 60. To disable the sync mode you can pass `wait=False`.

## AsyncIO support

You can also use the Replicate client asynchronously by prepending `async_` to the method name. 

Here's an example of how to run several predictions concurrently and wait for them all to complete:

```python
import asyncio
import replicate
 
# https://replicate.com/stability-ai/sdxl
model_version = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
prompts = [
    f"A chariot pulled by a team of {count} rainbow unicorns"
    for count in ["two", "four", "six", "eight"]
]

async with asyncio.TaskGroup() as tg:
    tasks = [
        tg.create_task(replicate.async_run(model_version, input={"prompt": prompt}))
        for prompt in prompts
    ]

results = await asyncio.gather(*tasks)
print(results)
```

To run a model that takes a file input you can pass either
a URL to a publicly accessible file on the Internet
or a handle to a file on your local device.

```python
>>> output = replicate.run(
        "andreasjansson/blip-2:f677695e5e89f8b236e52ecd1d3f01beb44c34606419bcc19345e046d8f786f9",
        input={ "image": open("path/to/mystery.jpg") }
    )

"an astronaut riding a horse"
```

## Run a model and stream its output

Replicate’s API supports server-sent event streams (SSEs) for language models. 
Use the `stream` method to consume tokens as they're produced by the model.

```python
import replicate

for event in replicate.stream(
    "meta/meta-llama-3-70b-instruct",
    input={
        "prompt": "Please write a haiku about llamas.",
    },
):
    print(str(event), end="")
```

> [!TIP]
> Some models, like [meta/meta-llama-3-70b-instruct](https://replicate.com/meta/meta-llama-3-70b-instruct), 
> don't require a version string. 
> You can always refer to the API documentation on the model page for specifics.

You can also stream the output of a prediction you create.
This is helpful when you want the ID of the prediction separate from its output.

```python
prediction = replicate.predictions.create(
    model="meta/meta-llama-3-70b-instruct",
    input={"prompt": "Please write a haiku about llamas."},
    stream=True,
)

for event in prediction.stream():
    print(str(event), end="")
```

For more information, see
["Streaming output"](https://replicate.com/docs/streaming) in Replicate's docs.


## Run a model in the background

You can start a model and run it in the background using async mode:

```python
>>> model = replicate.models.get("kvfrans/clipdraw")
>>> version = model.versions.get("5797a99edc939ea0e9242d5e8c9cb3bc7d125b1eac21bda852e5cb79ede2cd9b")
>>> prediction = replicate.predictions.create(
    version=version,
    input={"prompt":"Watercolor painting of an underwater submarine"})

>>> prediction
Prediction(...)

>>> prediction.status
'starting'

>>> dict(prediction)
{"id": "...", "status": "starting", ...}

>>> prediction.reload()
>>> prediction.status
'processing'

>>> print(prediction.logs)
iteration: 0, render:loss: -0.6171875
iteration: 10, render:loss: -0.92236328125
iteration: 20, render:loss: -1.197265625
iteration: 30, render:loss: -1.3994140625

>>> prediction.wait()

>>> prediction.status
'succeeded'

>>> prediction.output
<replicate.helpers.FileOutput object at 0x107179b50>

>>> with open("output.png", "wb") as file:
        file.write(prediction.output.read())
```

## Run a model in the background and get a webhook

You can run a model and get a webhook when it completes, instead of waiting for it to finish:

```python
model = replicate.models.get("ai-forever/kandinsky-2.2")
version = model.versions.get("ea1addaab376f4dc227f5368bbd8eff901820fd1cc14ed8cad63b29249e9d463")
prediction = replicate.predictions.create(
    version=version,
    input={"prompt":"Watercolor painting of an underwater submarine"},
    webhook="https://example.com/your-webhook",
    webhook_events_filter=["completed"]
)
```

For details on receiving webhooks, see [replicate.com/docs/webhooks](https://replicate.com/docs/webhooks).

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
iterator = replicate.run(
    "pixray/text2image:5c347a4bfa1d4523a58ae614c2194e15f2ae682b57e3797a5bb468920aa70ebf",
    input={"prompts": "san francisco sunset"}
)

for index, image in enumerate(iterator):
    with open(f"file_{index}.png", "wb") as file:
        file.write(image.read())
```

## Cancel a prediction

You can cancel a running prediction:

```python
>>> model = replicate.models.get("kvfrans/clipdraw")
>>> version = model.versions.get("5797a99edc939ea0e9242d5e8c9cb3bc7d125b1eac21bda852e5cb79ede2cd9b")
>>> prediction = replicate.predictions.create(
        version=version,
        input={"prompt":"Watercolor painting of an underwater submarine"}
    )

>>> prediction.status
'starting'

>>> prediction.cancel()

>>> prediction.reload()
>>> prediction.status
'canceled'
```

## List predictions

You can list all the predictions you've run:

```python
replicate.predictions.list()
# [<Prediction: 8b0ba5ab4d85>, <Prediction: 494900564e8c>]
```

Lists of predictions are paginated. You can get the next page of predictions by passing the `next` property as an argument to the `list` method:

```python
page1 = replicate.predictions.list()

if page1.next:
    page2 = replicate.predictions.list(page1.next)
```

## Load output files

Output files are returned as `FileOutput` objects:

```python
import replicate
from PIL import Image # pip install pillow

output = replicate.run(
    "stability-ai/stable-diffusion:27b93a2413e7f36cd83da926f3656280b2931564ff050bf9575f1fdf9bcd7478",
    input={"prompt": "wavy colorful abstract patterns, oceans"}
    )

# This has a .read() method that returns the binary data.
with open("my_output.png", "wb") as file:
  file.write(output[0].read())
  
# It also implements the iterator protocol to stream the data.
background = Image.open(output[0])
```

### FileOutput

Is a [file-like](https://docs.python.org/3/glossary.html#term-file-object) object returned from the `replicate.run()` method that makes it easier to work with models that output files. It implements `Iterator` and `AsyncIterator` for reading the file data in chunks as well as `read()` and `aread()` to read the entire file into memory.

> [!NOTE]
> It is worth noting that at this time `read()` and `aread()` do not currently accept a `size` argument to read up to `size` bytes.

Lastly, the URL of the underlying data source is available on the `url` attribute though we recommend you use the object as an iterator or use its `read()` or `aread()` methods, as the `url` property may not always return HTTP URLs in future.

```python
print(output.url) #=> "data:image/png;base64,xyz123..." or "https://delivery.replicate.com/..."
```

To consume the file directly:

```python
with open('output.bin', 'wb') as file:
    file.write(output.read())
```

Or for very large files they can be streamed:

```python
with open(file_path, 'wb') as file:
    for chunk in output:
        file.write(chunk)
```

Each of these methods has an equivalent `asyncio` API.

```python
async with aiofiles.open(filename, 'w') as file:
    await file.write(await output.aread())

async with aiofiles.open(filename, 'w') as file:
    await for chunk in output:
        await file.write(chunk)
```

For streaming responses from common frameworks, all support taking `Iterator` types:

**Django**

```python
@condition(etag_func=None)
def stream_response(request):
    output = replicate.run("black-forest-labs/flux-schnell", input={...}, use_file_output =True)
    return HttpResponse(output, content_type='image/webp')
```
  
**FastAPI**

```python
@app.get("/")
async def main():
    output = replicate.run("black-forest-labs/flux-schnell", input={...}, use_file_output =True)
    return StreamingResponse(output)
```

**Flask**

```python
@app.route('/stream')
def streamed_response():
    output = replicate.run("black-forest-labs/flux-schnell", input={...}, use_file_output =True)
    return app.response_class(stream_with_context(output))
```

You can opt out of `FileOutput` by passing `use_file_output=False` to the `replicate.run()` method.

```python
const replicate = replicate.run("acmecorp/acme-model", use_file_output=False);
```

## List models

You can list the models you've created:

```python
replicate.models.list()
```

Lists of models are paginated. You can get the next page of models by passing the `next` property as an argument to the `list` method, or you can use the `paginate` method to fetch pages automatically.

```python
# Automatic pagination using `replicate.paginate` (recommended)
models = []
for page in replicate.paginate(replicate.models.list):
    models.extend(page.results)
    if len(models) > 100:
        break

# Manual pagination using `next` cursors
page = replicate.models.list()
while page:
    models.extend(page.results)
    if len(models) > 100:
          break
    page = replicate.models.list(page.next) if page.next else None
```

You can also find collections of featured models on Replicate:

```python
>>> collections = [collection for page in replicate.paginate(replicate.collections.list) for collection in page]
>>> collections[0].slug
"vision-models"
>>> collections[0].description
"Multimodal large language models with vision capabilities like object detection and optical character recognition (OCR)"

>>> replicate.collections.get("text-to-image").models
[<Model: stability-ai/sdxl>, ...]
```

## Create a model

You can create a model for a user or organization
with a given name, visibility, and hardware SKU:

```python
import replicate

model = replicate.models.create(
    owner="your-username",
    name="my-model",
    visibility="public",
    hardware="gpu-a40-large"
)
```

Here's how to list of all the available hardware for running models on Replicate:

```python
>>> [hw.sku for hw in replicate.hardware.list()]
['cpu', 'gpu-t4', 'gpu-a40-small', 'gpu-a40-large']
```

## Fine-tune a model

Use the [training API](https://replicate.com/docs/fine-tuning) to fine-tune models to make them better at a particular task.  To see what **language models** currently support fine-tuning,  check out Replicate's [collection of trainable language models](https://replicate.com/collections/trainable-language-models).

If you're looking to fine-tune **image models**, check out Replicate's [guide to fine-tuning image models](https://replicate.com/docs/guides/fine-tune-an-image-model).

Here's how to fine-tune a model on Replicate:

```python
training = replicate.trainings.create(
    model="stability-ai/sdxl",
    version="39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    input={
      "input_images": "https://my-domain/training-images.zip",
      "token_string": "TOK",
      "caption_prefix": "a photo of TOK",
      "max_train_steps": 1000,
      "use_face_detection_instead": False
    },
    # You need to create a model on Replicate that will be the destination for the trained version.
    destination="your-username/model-name"
)
```

## Customize client behavior

The `replicate` package exports a default shared client. This client is initialized with an API token set by the `REPLICATE_API_TOKEN` environment variable.

You can create your own client instance to pass a different API token value, add custom headers to requests, or control the behavior of the underlying [HTTPX client](https://www.python-httpx.org/api/#client):

```python
import os
from replicate.client import Client

replicate = Client(
    api_token=os.environ["SOME_OTHER_REPLICATE_API_TOKEN"]
    headers={
        "User-Agent": "my-app/1.0"
    }
)
```

> [!WARNING]
> Never hardcode authentication credentials like API tokens into your code.
> Instead, pass them as environment variables when running your program.

## Experimental `use()` interface

The latest versions of `replicate >= 1.1.0b1` include a new experimental `use()` function that is intended to make running a model closer to calling a function rather than an API request.

Some key differences to `replicate.run()`.

 1. You "import" the model using the `use()` syntax, after that you call the model like a function.
 2. The output type matches the model definition.
 3. Baked in support for streaming for all models.
 4. File outputs will be represented as `PathLike` objects and downloaded to disk when used*.

> [!NOTE]
> \* We've replaced the `FileOutput` implementation with `Path` objects. However to avoid unnecessary downloading of files until they are needed we've implemented a `PathProxy` class that will defer the download until the first time the object is used. If you need the underlying URL of the `Path` object you can use the `get_path_url(path: Path) -> str` helper.

### Examples

To use a model:

> [!IMPORTANT]
> For now `use()` MUST be called in the top level module scope. We may relax this in future.

```py
import replicate

flux_dev = replicate.use("black-forest-labs/flux-dev")
outputs = flux_dev(prompt="a cat wearing an amusing hat")

for output in outputs:
    print(output) # Path(/tmp/output.webp)
```

Models that implement iterators will return the output of the completed run as a list unless explicitly streaming (see Streaming section below). Language models that define `x-cog-iterator-display: concatenate` will return strings:

```py
claude = replicate.use("anthropic/claude-4-sonnet")

output = claude(prompt="Give me a recipe for tasty smashed avocado on sourdough toast that could feed all of California.")

print(output) # "Here's a recipe to feed all of California (about 39 million people)! ..."
```

You can pass the results of one model directly into another:

```py
import replicate

flux_dev = replicate.use("black-forest-labs/flux-dev")
claude = replicate.use("anthropic/claude-4-sonnet")

images = flux_dev(prompt="a cat wearing an amusing hat")

result = claude(prompt="describe this image for me", image=images[0])

print(str(result)) # "This shows an image of a cat wearing a hat ..."
```

To create an individual prediction that has not yet resolved, use the `create()` method:

```
claude = replicate.use("anthropic/claude-4-sonnet")

prediction = claude.create(prompt="Give me a recipe for tasty smashed avocado on sourdough toast that could feed all of California.")

prediction.logs() # get current logs (WIP)

prediction.output() # get the output
```

### Streaming

Many models, particularly large language models (LLMs), will yield partial results as the model is running. To consume outputs from these models as they run you can pass the `streaming` argument to `use()`:

```py
claude = replicate.use("anthropic/claude-4-sonnet", streaming=True)

output = claude(prompt="Give me a recipe for tasty smashed avocado on sourdough toast that could feed all of California.")

for chunk in output:
    print(chunk) # "Here's a recipe ", "to feed all", " of California"
```

### Downloading file outputs

Output files are provided as Python [os.PathLike](https://docs.python.org/3.12/library/os.html#os.PathLike) objects. These are supported by most of the Python standard library like `open()` and `Path`, as well as third-party libraries like `pillow` and `ffmpeg-python`.

The first time the file is accessed it will be downloaded to a temporary directory on disk ready for use.

Here's an example of how to use the `pillow` package to convert file outputs:

```py
import replicate
from PIL import Image

flux_dev = replicate.use("black-forest-labs/flux-dev")

images = flux_dev(prompt="a cat wearing an amusing hat")
for i, path in enumerate(images):
    with Image.open(path) as img:
        img.save(f"./output_{i}.png", format="PNG")
```

For libraries that do not support `Path` or `PathLike` instances you can use `open()` as you would with any other file. For example to use `requests` to upload the file to a different location:

```py
import replicate
import requests

flux_dev = replicate.use("black-forest-labs/flux-dev")

images = flux_dev(prompt="a cat wearing an amusing hat")
for path in images:
    with open(path, "rb") as f:
        r = requests.post("https://api.example.com/upload", files={"file": f})
```

### Accessing outputs as HTTPS URLs

If you do not need to download the output to disk. You can access the underlying URL for a Path object returned from a model call by using the `get_path_url()` helper.

```py
import replicate
from replicate import get_url_path

flux_dev = replicate.use("black-forest-labs/flux-dev")
outputs = flux_dev(prompt="a cat wearing an amusing hat")

for output in outputs:
    print(get_url_path(output)) # "https://replicate.delivery/xyz"
```

### Async Mode

By default `use()` will return a function instance with a sync interface. You can pass `use_async=True` to have it return an `AsyncFunction` that provides an async interface.

```py
import asyncio
import replicate

async def main():
    flux_dev = replicate.use("black-forest-labs/flux-dev", use_async=True)
    outputs = await flux_dev(prompt="a cat wearing an amusing hat")

    for output in outputs:
        print(Path(output))

asyncio.run(main())
```

When used in streaming mode then an `AsyncIterator` will be returned.

```py
import asyncio
import replicate

async def main():
    claude = replicate.use("anthropic/claude-3.5-haiku", streaming=True, use_async=True)
    output = await claude(prompt="say hello")

    # Stream the response as it comes in.
    async for token in output:
        print(token)

    # Wait until model has completed. This will return either a `list` or a `str` depending
    # on whether the model uses AsyncIterator or ConcatenateAsyncIterator. You can check this
    # on the model schema by looking for `x-cog-display: concatenate`.
    print(await output)

asyncio.run(main())
```

### Typing

By default `use()` knows nothing about the interface of the model. To provide a better developer experience we provide two methods to add type annotations to the function returned by the `use()` helper.

**1. Provide a function signature**

The use method accepts a function signature as an additional `hint` keyword argument. When provided it will use this signature for the `model()` and `model.create()` functions.

```py
# Flux takes a required prompt string and optional image and seed.
def hint(*, prompt: str, image: Path | None = None, seed: int | None = None) -> str: ...

flux_dev = use("black-forest-labs/flux-dev", hint=hint)
output1 = flux_dev() # will warn that `prompt` is missing
output2 = flux_dev(prompt="str") # output2 will be typed as `str`
```

**2. Provide a class**

The second method requires creating a callable class with a `name` field. The name will be used as the function reference when passed to `use()`.

```py
class FluxDev:
    name = "black-forest-labs/flux-dev"

    def __call__( self, *, prompt: str, image: Path | None = None, seed: int | None = None ) -> str: ...

flux_dev = use(FluxDev)
output1 = flux_dev() # will warn that `prompt` is missing
output2 = flux_dev(prompt="str") # output2 will be typed as `str`
```

> [!WARNING]
> Currently the typing system doesn't correctly support the `streaming` flag for models that return lists or use iterators. We're working on improvements here.

In future we hope to provide tooling to generate and provide these models as packages to make working with them easier. For now you may wish to create your own.

### API Reference

The Replicate Python Library provides several key classes and functions for working with models in pipelines:

#### `use()` Function

Creates a callable function wrapper for a Replicate model.

```py
def use(
    ref: FunctionRef,
    *,
    streaming: bool = False,
    use_async: bool = False
) -> Function | AsyncFunction

def use(
    ref: str,
    *,
    hint: Callable | None = None,
    streaming: bool = False,
    use_async: bool = False
) -> Function | AsyncFunction
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ref` | `str \| FunctionRef` | Required | Model reference (e.g., "owner/model" or "owner/model:version") |
| `hint` | `Callable \| None` | `None` | Function signature for type hints |
| `streaming` | `bool` | `False` | Return OutputIterator for streaming results |
| `use_async` | `bool` | `False` | Return AsyncFunction instead of Function |

**Returns:**
- `Function` - Synchronous model wrapper (default)
- `AsyncFunction` - Asynchronous model wrapper (when `use_async=True`)

#### `Function` Class

A synchronous wrapper for calling Replicate models.

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `__call__()` | `(*args, **inputs) -> Output` | Execute the model and return final output |
| `create()` | `(*args, **inputs) -> Run` | Start a prediction and return Run object |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `openapi_schema` | `dict` | Model's OpenAPI schema for inputs/outputs |
| `default_example` | `dict \| None` | Default example inputs (not yet implemented) |

#### `AsyncFunction` Class

An asynchronous wrapper for calling Replicate models.

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `__call__()` | `async (*args, **inputs) -> Output` | Execute the model and return final output |
| `create()` | `async (*args, **inputs) -> AsyncRun` | Start a prediction and return AsyncRun object |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `openapi_schema()` | `async () -> dict` | Model's OpenAPI schema for inputs/outputs |
| `default_example` | `dict \| None` | Default example inputs (not yet implemented) |

#### `Run` Class

Represents a running prediction with access to output and logs.

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `output()` | `() -> Output` | Get prediction output (blocks until complete) |
| `logs()` | `() -> str \| None` | Get current prediction logs |

**Behavior:**
- When `streaming=True`: Returns `OutputIterator` immediately
- When `streaming=False`: Waits for completion and returns final result

#### `AsyncRun` Class

Asynchronous version of Run for async model calls.

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `output()` | `async () -> Output` | Get prediction output (awaits completion) |
| `logs()` | `async () -> str \| None` | Get current prediction logs |

#### `OutputIterator` Class

Iterator wrapper for streaming model outputs.

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `__iter__()` | `() -> Iterator[T]` | Synchronous iteration over output chunks |
| `__aiter__()` | `() -> AsyncIterator[T]` | Asynchronous iteration over output chunks |
| `__str__()` | `() -> str` | Convert to string (concatenated or list representation) |
| `__await__()` | `() -> List[T] \| str` | Await all results (string for concatenate, list otherwise) |

#### `URLPath` Class

A path-like object that downloads files on first access.

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `__fspath__()` | `() -> str` | Get local file path (downloads if needed) |
| `__str__()` | `() -> str` | String representation of local path |

**Usage:**
- Compatible with `open()`, `pathlib.Path()`, and most file operations
- Downloads file automatically on first filesystem access
- Cached locally in temporary directory

#### `get_path_url()` Function

Helper function to extract original URLs from `URLPath` objects.

```py
def get_path_url(path: Any) -> str | None
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `Any` | Path object (typically `URLPath`) |

**Returns:**
- `str` - Original URL if path is a `URLPath`
- `None` - If path is not a `URLPath` or has no URL

### TODO

There are several key things still outstanding:

 1. Support for streaming text when available (rather than polling)
 2. Support for streaming files when available (rather than polling)
 3. Support for cleaning up downloaded files.
 4. Support for streaming logs using `OutputIterator`.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md)
