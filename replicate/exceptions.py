class ReplicateException(Exception):
    """A base class for all Replicate exceptions."""


class ModelError(ReplicateException):
    """An error from user's code in a model."""


class ReplicateError(ReplicateException):
    """An error from Replicate."""
