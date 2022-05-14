# !/usr/bin/env python

from distutils.core import setup

setup(
    name="replicate",
    packages=["replicate"],
    version="0.1.0",
    description="Python client for Replicate",
    author="Replicate, Inc.",
    license="BSD",
    url="https://github.com/replicate/replicate-python",
    python_requires=">=3.6",
    install_requires=["requests", "pydantic"],
    classifiers=[],
)
