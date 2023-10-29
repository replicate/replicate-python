import io
from pathlib import Path
from types import GeneratorType
from typing import Any, Callable

try:
    import numpy as np  # type: ignore

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# pylint: disable=too-many-return-statements
def encode_json(
    obj: Any,  # noqa: ANN401
    upload_file: Callable[[io.IOBase], str],
) -> Any:  # noqa: ANN401
    """
    Return a JSON-compatible version of the object.
    """
    # Effectively the same thing as cog.json.encode_json.

    if isinstance(obj, dict):
        return {key: encode_json(value, upload_file) for key, value in obj.items()}
    if isinstance(obj, (list, set, frozenset, GeneratorType, tuple)):
        return [encode_json(value, upload_file) for value in obj]
    if isinstance(obj, Path):
        with obj.open("rb") as file:
            return upload_file(file)
    if isinstance(obj, io.IOBase):
        return upload_file(obj)
    if HAS_NUMPY:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    return obj
