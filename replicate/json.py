import io
from pathlib import Path
from types import GeneratorType
from typing import Any, Callable

try:
    import numpy as np  # type: ignore

    has_numpy = True
except ImportError:
    has_numpy = False


def encode_json(
    obj: Any, upload_file: Callable[[io.IOBase], str]  # noqa: ANN401
) -> Any:  # noqa: ANN401
    """
    Returns a JSON-compatible version of the object. Effectively the same thing as cog.json.encode_json.
    """
    if isinstance(obj, dict):
        return {key: encode_json(value, upload_file) for key, value in obj.items()}
    if isinstance(obj, (list, set, frozenset, GeneratorType, tuple)):
        return [encode_json(value, upload_file) for value in obj]
    if isinstance(obj, Path):
        with obj.open("rb") as f:
            return upload_file(f)
    if isinstance(obj, io.IOBase):
        return upload_file(obj)
    if has_numpy:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    return obj
