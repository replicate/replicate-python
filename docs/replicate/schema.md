Module replicate.schema
=======================

Functions
---------

    
`make_schema_backwards_compatible(schema: dict, cog_version: str) ‑> dict`
:   A place to add backwards compatibility logic for our openapi schema

    
`version_has_no_array_type(cog_version: str) ‑> Optional[bool]`
:   Iterators have x-cog-array-type=iterator in the schema from 0.3.9 onward