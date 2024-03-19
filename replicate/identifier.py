import re
from typing import TYPE_CHECKING, NamedTuple, Optional, Tuple, Union

if TYPE_CHECKING:
    from replicate.model import Model
    from replicate.version import Version


class ModelVersionIdentifier(NamedTuple):
    """
    A reference to a model version in the format owner/name or owner/name:version.
    """

    owner: str
    name: str
    version: Optional[str] = None

    @classmethod
    def parse(cls, ref: str) -> "ModelVersionIdentifier":
        """
        Split a reference in the format owner/name:version into its components.
        """

        match = re.match(r"^(?P<owner>[^/]+)/(?P<name>[^/:]+)(:(?P<version>.+))?$", ref)
        if not match:
            raise ValueError(
                f"Invalid reference to model version: {ref}. Expected format: owner/name:version"
            )

        return cls(match.group("owner"), match.group("name"), match.group("version"))


def _resolve(
    ref: Union["Model", "Version", "ModelVersionIdentifier", str],
) -> Tuple[Optional["Version"], Optional[str], Optional[str], Optional[str]]:
    from replicate.model import Model  # pylint: disable=import-outside-toplevel
    from replicate.version import Version  # pylint: disable=import-outside-toplevel

    version = None
    owner, name, version_id = None, None, None
    if isinstance(ref, Model):
        owner, name = ref.owner, ref.name
    elif isinstance(ref, Version):
        version = ref
        version_id = ref.id
    elif isinstance(ref, ModelVersionIdentifier):
        owner, name, version_id = ref
    elif isinstance(ref, str):
        owner, name, version_id = ModelVersionIdentifier.parse(ref)
    return version, owner, name, version_id
