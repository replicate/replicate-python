Module replicate.identifier
===========================

Classes
-------

`ModelVersionIdentifier(owner: str, name: str, version: Optional[str] = None)`
:   A reference to a model version in the format owner/name or owner/name:version.

    ### Ancestors (in MRO)

    * builtins.tuple

    ### Static methods

    `parse(ref: str) ‑> replicate.identifier.ModelVersionIdentifier`
    :   Split a reference in the format owner/name:version into its components.

    ### Instance variables

    `name: str`
    :   Alias for field number 1

    `owner: str`
    :   Alias for field number 0

    `version: Optional[str]`
    :   Alias for field number 2