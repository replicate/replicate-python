from typing import (
    TYPE_CHECKING,
    AsyncGenerator,
    Awaitable,
    Callable,
    Generator,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
)

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore

from replicate.resource import Resource

T = TypeVar("T", bound=Resource)

if TYPE_CHECKING:
    pass


class Page(pydantic.BaseModel, Generic[T]):  # type: ignore
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


def paginate(
    list_method: Callable[[Union[str, "ellipsis", None]], Page[T]],  # noqa: F821
) -> Generator[Page[T], None, None]:
    """
    Iterate over all items using the provided list method.

    Args:
        list_method: A method that takes a cursor argument and returns a Page of items.
    """
    cursor: Union[str, "ellipsis", None] = ...  # noqa: F821
    while cursor is not None:
        page = list_method(cursor)
        yield page
        cursor = page.next


async def async_paginate(
    list_method: Callable[[Union[str, "ellipsis", None]], Awaitable[Page[T]]],  # noqa: F821
) -> AsyncGenerator[Page[T], None]:
    """
    Asynchronously iterate over all items using the provided list method.

    Args:
        list_method: An async method that takes a cursor argument and returns a Page of items.
    """
    cursor: Union[str, "ellipsis", None] = ...  # noqa: F821
    while cursor is not None:
        page = await list_method(cursor)
        yield page
        cursor = page.next
