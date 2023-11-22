from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Literal,
    Optional,
)

from typing_extensions import Unpack

from replicate.identifier import ModelVersionIdentifier
from replicate.exceptions import ReplicateError

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore


if TYPE_CHECKING:
    import httpx

    from replicate.client import Client
    from replicate.prediction import Predictions


class ServerSentEvent(pydantic.BaseModel):
    """
    A server-sent event.
    """

    event: Literal["message", "output", "logs", "error", "done"] = "message"
    data: str = ""
    id: str = ""
    retry: Optional[int] = None

    def __str__(self) -> str:
        if self.event == "output":
            return self.data

        return ""


class EventSource:
    response: "httpx.Response"

    def __init__(self, response: "httpx.Response") -> None:
        self.response = response
        content_type, _, _ = response.headers["content-type"].partition(";")
        if content_type != "text/event-stream":
            raise ValueError(
                "Expected response Content-Type to be 'text/event-stream', "
                f"got {content_type!r}"
            )

    class Decoder:
        event: Optional[str] = None
        data: List[str] = []
        last_event_id: Optional[str] = None
        retry: Optional[int] = None

        def decode(self, line: str) -> Optional[ServerSentEvent]:
            if not line:
                if not any([self.event, self.data, self.last_event_id, self.retry]):
                    return None

                try:
                    sse = ServerSentEvent(
                        event=self.event,
                        data="\n".join(self.data),
                        id=self.last_event_id,
                        retry=self.retry,
                    )
                except pydantic.ValidationError:
                    return None

                self.event = ""
                self.data = []
                self.retry = None

                return sse

            if line.startswith(":"):
                return None

            fieldname, _, value = line.partition(":")
            value = value.lstrip()

            match fieldname:
                case "event":
                    self.event = value
                case "data":
                    self.data.append(value)
                case "id":
                    if "\0" not in value:
                        self.last_event_id = value
                case "retry":
                    try:
                        self.retry = int(value)
                    except (TypeError, ValueError):
                        pass
                case _:
                    pass

            return None

    def __iter__(self) -> Iterator[ServerSentEvent]:
        decoder = EventSource.Decoder()
        for line in self.response.iter_lines():
            line = line.rstrip("\n")
            sse = decoder.decode(line)
            if sse is not None:
                match sse.event:
                    case "done":
                        return
                    case "error":
                        raise RuntimeError(sse.data)
                    case _:
                        yield sse

    async def __aiter__(self) -> AsyncIterator[ServerSentEvent]:
        decoder = EventSource.Decoder()
        async for line in self.response.aiter_lines():
            line = line.rstrip("\n")
            sse = decoder.decode(line)
            if sse is not None:
                match sse.event:
                    case "done":
                        return
                    case "error":
                        raise RuntimeError(sse.data)
                    case _:
                        yield sse


def stream(
    client: "Client",
    ref: str,
    input: Optional[Dict[str, Any]] = None,
    **params: Unpack["Predictions.CreatePredictionParams"],
) -> Iterator[ServerSentEvent]:
    """
    Run a model and stream its output.
    """

    params = params or {}
    params["stream"] = True

    _, _, version_id = ModelVersionIdentifier.parse(ref)
    prediction = client.predictions.create(
        version=version_id, input=input or {}, **params
    )

    url = prediction.urls and prediction.urls.get("stream", None)
    if not url:
        raise ReplicateError("Model does not support streaming")

    headers = {}
    headers["Accept"] = "text/event-stream"
    headers["Cache-Control"] = "no-store"

    with client._client.stream("GET", url, headers=headers) as response:
        yield from EventSource(response)


async def async_stream(
    client: "Client",
    ref: str,
    input: Optional[Dict[str, Any]] = None,
    **params: Unpack["Predictions.CreatePredictionParams"],
) -> AsyncIterator[ServerSentEvent]:
    """
    Run a model and stream its output asynchronously.
    """

    params = params or {}
    params["stream"] = True

    _, _, version_id = ModelVersionIdentifier.parse(ref)
    prediction = await client.predictions.async_create(
        version=version_id, input=input or {}, **params
    )

    url = prediction.urls and prediction.urls.get("stream", None)
    if not url:
        raise ReplicateError("Model does not support streaming")

    headers = {}
    headers["Accept"] = "text/event-stream"
    headers["Cache-Control"] = "no-store"

    async with client._async_client.stream("GET", url, headers=headers) as response:
        async for event in EventSource(response):
            yield event
