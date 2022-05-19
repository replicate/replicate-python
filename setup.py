# !/usr/bin/env python

from pathlib import Path

from setuptools import setup

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# setup.py cannot safely import files, so read and exec to get the version
__version__ = None
exec(open("replicate/__about__.py").read())

setup(
    name="replicate",
    packages=["replicate"],
    version=__version__,
    description="Python client for Replicate",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Replicate, Inc.",
    license="BSD",
    url="https://github.com/replicate/replicate-python",
    python_requires=">=3.6",
    install_requires=["requests", "pydantic"],
    classifiers=[],
)
