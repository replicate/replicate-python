# !/usr/bin/env python

from setuptools import setup

from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


setup(
    name="replicate",
    packages=["replicate"],
    version="0.0.1a7",
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
