"""Minimal respx-compatible mock router for httpx2-based tests.

The test suite only uses a small subset of respx's API: Router with
route()/mock()/pass_through(), router.handler plugged into
httpx2.MockTransport, and call assertions. This module provides exactly
that surface, natively typed against httpx2.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx2


@dataclass
class Call:
    request: httpx2.Request


class Route:
    def __init__(
        self,
        router: "Router",
        method: Optional[str] = None,
        path: Optional[str] = None,
        host: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        name: Optional[str] = None,
        path__regex: Optional[str] = None,
        url: Optional[str] = None,
    ) -> None:
        self.router = router
        self.method = method.upper() if method else None
        if url is not None:
            u = httpx2.URL(url)
            host = host or u.host
            path = u.path
        self.path = path
        self.path_regex = re.compile(path__regex) if path__regex else None
        self.host = host
        self.headers = headers or {}
        self.name = name
        self.calls: List[Call] = []
        self._return_value: Optional[httpx2.Response] = None
        self._side_effect: Optional[List[Any]] = None
        self._pass_through = False

    def mock(
        self,
        return_value: Optional[httpx2.Response] = None,
        side_effect: Optional[List[Any]] = None,
    ) -> "Route":
        self._return_value = return_value
        self._side_effect = list(side_effect) if side_effect is not None else None
        return self

    @staticmethod
    def _clone(response: httpx2.Response, request: httpx2.Request) -> httpx2.Response:
        # Rebuild a fresh Response per call: httpx2 rebinds .stream to a
        # sync/async wrapper after each send, so reusing one instance breaks
        # the sync/async isinstance checks on subsequent calls.
        return httpx2.Response(
            status_code=response.status_code,
            headers=list(response.headers.raw),
            content=response.content,
            extensions=dict(response.extensions),
            request=request,
        )

    def pass_through(self) -> "Route":
        self._pass_through = True
        return self

    @property
    def called(self) -> bool:
        return bool(self.calls)

    def matches(self, request: httpx2.Request) -> bool:
        if self.method and request.method != self.method:
            return False
        if self.host and request.url.host != self.host:
            return False
        if self.path_regex is not None:
            # respx applies regex lookups relative to the router's base_url
            path = request.url.path
            if self.router.base_path and path.startswith(self.router.base_path):
                path = path[len(self.router.base_path):]
            if not self.path_regex.match(path):
                return False
        elif self.path is not None:
            expected = (self.router.base_path or "") + self.path
            if request.url.path != expected:
                return False
        elif self.host is None and self.router.base_url is not None:
            # base_url-only router with a path-less route never matches
            return False
        for key, value in self.headers.items():
            if request.headers.get(key) != value:
                return False
        return True

    def respond(self, request: httpx2.Request) -> httpx2.Response:
        self.calls.append(Call(request=request))
        if self._side_effect:
            result = self._side_effect.pop(0)
            if isinstance(result, type) and issubclass(result, Exception):
                raise result()
            if isinstance(result, Exception):
                raise result
            response = result
        else:
            response = self._return_value
        if response is None:
            raise ValueError(f"Route {self.name or self.path} has no mocked response")
        return self._clone(response, request)


class Router:
    def __init__(self, base_url: Optional[str] = None, **_: Any) -> None:
        self.base_url = base_url
        if base_url:
            self.base_path = httpx2.URL(base_url).path.rstrip("/")
            self.base_host = httpx2.URL(base_url).host
        else:
            self.base_path = None
            self.base_host = None
        self.routes: List[Route] = []
        self.calls: List[Call] = []

    def route(self, **kwargs: Any) -> Route:
        route = Route(self, **kwargs)
        self.routes.append(route)
        return route

    def get(self, path: str, **kwargs: Any) -> Route:
        return self.route(method="GET", path=path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Route:
        return self.route(method="POST", path=path, **kwargs)

    def __getitem__(self, name: str) -> Route:
        for route in self.routes:
            if route.name == name:
                return route
        raise KeyError(name)

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        self.calls.append(Call(request=request))
        for route in self.routes:
            if route.matches(request):
                if route._pass_through:
                    with httpx2.Client() as client:
                        return client.send(request)
                return route.respond(request)
        raise ValueError(f"No mocked route matches {request.method} {request.url}")


# Module-level default router, mirroring respx.get(...)/respx.request(...) usage.
default_router = Router()


def get(url: str, **kwargs: Any) -> Route:
    u = httpx2.URL(url)
    return default_router.route(method="GET", host=u.host, path=u.path, **kwargs)
