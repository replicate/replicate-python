from typing import Optional

from packaging import version

# TODO: this code is shared with replicate's backend. Maybe we should put it in the Cog Python package as the source of truth?


def version_has_no_array_type(cog_version: str) -> Optional[bool]:
    """Iterators have x-cog-array-type=iterator in the schema from 0.3.9 onward"""
    try:
        return version.parse(cog_version) < version.parse("0.3.9")
    except version.InvalidVersion:
        return None


def make_schema_backwards_compatible(
    schema: dict,
    cog_version: str,
) -> dict:
    """A place to add backwards compatibility logic for our openapi schema"""

    # If the top-level output is an array, assume it is an iterator in old versions which didn't have an array type
    if version_has_no_array_type(cog_version):
        output = schema["components"]["schemas"]["Output"]
        if output.get("type") == "array":
            output["x-cog-array-type"] = "iterator"
    return schema
