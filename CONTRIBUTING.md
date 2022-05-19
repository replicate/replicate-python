# Contributing guide

## Development

To run the tests:

```sh
pip install -r requirements-dev.txt
pytest
```

To install the package in development:

```sh
pip install -e .
```

## Publishing a release

This project has a [GitHub Actions workflow](https://github.com/replicate/replicate-python/blob/ab4439ee02d1f157cd3b904f5e0232b69bbae707/.github/workflows/ci.yaml#L37-L63) that publishes the `replicate` package to PyPI. The release process is triggered by manually creating and pushing a new git tag.

First, set the version number in [setup.py](setup.py) and commit it to the `main` branch:

```
version="0.0.1a7"
```

Then run the following in your local checkout:

```sh
git checkout main
git fetch --all --tags
git tag 0.0.1a7 
git push --tags
```

Then visit [github.com/replicate/replicate-python/actions](https://github.com/replicate/replicate-python/actions) to monitor the release process.