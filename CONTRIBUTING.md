# Contributing guide

- [Making a contribution](#making-a-contribution)
  - [Signing your work](#signing-your-work)
  - [How to sign off your commits](#how-to-sign-off-your-commits)
- [Development](#development)
  - [Environment variables](#environment-variables)
- [Publishing a release](#publishing-a-release)

## Making a contribution

### Signing your work

Each commit you contribute to this repo must be signed off (not to be confused with **[signing](https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work)**). It certifies that you wrote the patch, or have the right to contribute it. It is called the [Developer Certificate of Origin](https://developercertificate.org/) and was originally developed for the Linux kernel.

If you can certify the following:

```
By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

Then add this line to each of your Git commit messages, with your name and email:

```
Signed-off-by: Sam Smith <sam.smith@example.com>
```

### How to sign off your commits

If you're using the `git` CLI, you can sign a commit by passing the `-s` option: `git commit -s -m "Reticulate splines"`

You can also create a git hook which will sign off all your commits automatically. Using hooks also allows you to sign off commits when using non-command-line tools like GitHub Desktop or VS Code.

First, create the hook file and make it executable:

```sh
cd your/checkout/of/replicate-python
touch .git/hooks/prepare-commit-msg
chmod +x .git/hooks/prepare-commit-msg
```

Then paste the following into the file:

```
#!/bin/sh

NAME=$(git config user.name)
EMAIL=$(git config user.email)

if [ -z "$NAME" ]; then
    echo "empty git config user.name"
    exit 1
fi

if [ -z "$EMAIL" ]; then
    echo "empty git config user.email"
    exit 1
fi

git interpret-trailers --if-exists doNothing --trailer \
    "Signed-off-by: $NAME <$EMAIL>" \
    --in-place "$1"
```

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

### Environment variables

- `REPLICATE_API_BASE_URL`: Defaults to `https://api.replicate.com` but can be overriden to point the client at a development host.
- `REPLICATE_API_TOKEN`: Required. Find your token at https://replicate.com/#token

## Publishing a release

This project has a [GitHub Actions workflow](/.github/workflows/ci.yaml) that publishes the `replicate` package to PyPI. The release process is triggered by manually creating and pushing a new git tag.

First, set the version number in [pyproject.toml](pyproject.toml) and commit it to the `main` branch:

```
version = "0.7.0"
```

Then run the following in your local checkout:

```sh
git checkout main
git fetch --all --tags
git tag 0.7.0
git push --tags
```

Then visit [github.com/replicate/replicate-python/actions](https://github.com/replicate/replicate-python/actions) to monitor the release process.
