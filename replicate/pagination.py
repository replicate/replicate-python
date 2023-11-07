from typing import (
    TYPE_CHECKING,
    Dict,
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

from replicate.resource import Namespace, Resource

T = TypeVar("T", bound=Resource)

if TYPE_CHECKING:
    from .client import Client


class Page(pydantic.BaseModel, Generic[T]):
    """
    A page of results from the API.
    """

    _client: "Client" = pydantic.PrivateAttr()
    _namespace: Namespace = pydantic.PrivateAttr()

    previous: Optional[str] = None
    """A pointer to the previous page of results"""

    next: Optional[str] = None
    """A pointer to the next page of results"""

    results: List[T]
    """The results on this page"""

    def __init__(
        self,
        client: "Client",
        namespace: Namespace[T],
        *,
        results: Optional[List[Union[T, Dict]]] = None,
        **kwargs,
    ) -> None:
        self._client = client
        self._namespace = namespace

        super().__init__(
            results=[self._namespace._prepare_model(r) for r in results]
            if results
            else None,
            **kwargs,
        )

    def __iter__(self):  # noqa: ANN204
        return iter(self.results)

    def __getitem__(self, index: int) -> T:
        return self.results[index]

    def __len__(self) -> int:
        return len(self.results)
