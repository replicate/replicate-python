from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

from .resource import Resource

T = TypeVar("T", bound=Resource)


class Page(BaseModel, Generic[T]):
    previous: Optional[str] = None
    """A pointer to the previous page of results"""

    next: Optional[str] = None
    """A pointer to the next page of results"""

    results: list[T]
    """The results on this page"""
