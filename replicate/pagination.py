from typing import (
    TYPE_CHECKING,
    Generic,
    List,
    Optional,
    TypeVar,
)

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore

from replicate.resource import Resource

T = TypeVar("T", bound=Resource)

if TYPE_CHECKING:
    pass


class Page(pydantic.BaseModel, Generic[T]):
    """
    A page of results from the API.
    """

    previous: Optional[str] = None
    """A pointer to the previous page of results"""

    next: Optional[str] = None
    """A pointer to the next page of results"""

    results: List[T]
    """The results on this page"""

    def __iter__(self):  # noqa: ANN204
        return iter(self.results)

    def __getitem__(self, index: int) -> T:
        return self.results[index]

    def __len__(self) -> int:
        return len(self.results)
