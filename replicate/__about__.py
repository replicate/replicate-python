from importlib.metadata import version

__version__ = version(__package__ if __package__ is not None else "replicate")
