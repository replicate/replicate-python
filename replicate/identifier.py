import re
from typing import NamedTuple


class ModelIdentifier(NamedTuple):
    """
    A reference to a model in the format owner/name:version.
    """

    owner: str
    name: str

    @classmethod
    def parse(cls, ref: str) -> "ModelIdentifier":
        """
        Split a reference in the format owner/name:version into its components.
        """

        match = re.match(r"^(?P<owner>[^/]+)/(?P<name>[^:]+)$", ref)
        if not match:
            raise ValueError(
                f"Invalid reference to model version: {ref}. Expected format: owner/name"
            )

        return cls(match.group("owner"), match.group("name"))


class ModelVersionIdentifier(NamedTuple):
    """
    A reference to a model version in the format owner/name:version.
    """

    owner: str
    name: str
    version: str

    @classmethod
    def parse(cls, ref: str) -> "ModelVersionIdentifier":
        """
        Split a reference in the format owner/name:version into its components.
        """

        match = re.match(r"^(?P<owner>[^/]+)/(?P<name>[^:]+):(?P<version>.+)$", ref)
        if not match:
            raise ValueError(
                f"Invalid reference to model version: {ref}. Expected format: owner/name:version"
            )

        return cls(match.group("owner"), match.group("name"), match.group("version"))
