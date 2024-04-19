from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Optional,
    Union,
)

from typing_extensions import Unpack

from replicate import identifier
from replicate.exceptions import ReplicateError

try:
    from pydantic import v1 as pydantic  # type: ignore
except ImportError:
    import pydantic  # type: ignore


if TYPE_CHECKING:
    import httpx

    from replicate.client import Client
    from replicate.identifier import ModelVersionIdentifier
    from replicate.model import Model
    from replicate.prediction import Predictions
    from replicate.version import Version


class ServerSentEvent(pydantic.BaseModel):  # type: ignore
    """
    A server-sent event.
    """

    class EventType(Enum):
        """
        A server-sent event type.
        """

        OUTPUT = "output"
        LOGS = "logs"
        ERROR = "error"
        DONE = "done"

    event: EventType
    data: str
    id: str
    retry: Optional[int]

    def __str__(self) -> str:
        if self.event == ServerSentEvent.EventType.OUTPUT:
            return self.data

        return ""


class EventSource:
    """
    A server-sent event source.
    """

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
        """
        A decoder for server-sent events.
        """

        event: Optional["ServerSentEvent.EventType"]
        data: List[str]
        last_event_id: Optional[str]
        retry: Optional[int]

        def __init__(self) -> None:
            self.event = None
            self.data = []
            self.last_event_id = None
            self.retry = None

        def decode(self, line: str) -> Optional[ServerSentEvent]:
            """
            Decode a line and return a server-sent event if applicable.
            """

            if not line:
                if (
                    not any([self.event, self.data, self.last_event_id, self.retry])
                    or self.event is None
                    or self.last_event_id is None
                ):
                    return None

                sse = ServerSentEvent(
                    event=self.event,
                    data="\n".join(self.data),
                    id=self.last_event_id,
                    retry=self.retry,
                )

                self.event = None
                self.data = []
                self.retry = None

                return sse

            if line.startswith(":"):
                return None

            fieldname, _, value = line.partition(":")
            value = value[1:] if value.startswith(" ") else value

            if fieldname == "event":
                if event := ServerSentEvent.EventType(value):
                    self.event = event
            elif fieldname == "data":
                self.data.append(value)
            elif fieldname == "id":
                if "\0" not in value:
                    self.last_event_id = value
            elif fieldname == "retry":
                try:
                    self.retry = int(value)
                except (TypeError, ValueError):
                    pass

            return None

    def __iter__(self) -> Iterator[ServerSentEvent]:
        decoder = EventSource.Decoder()

        for line in self.response.iter_lines():
            line = line.rstrip("\n")
            sse = decoder.decode(line)
            if sse is not None:
                if sse.event == ServerSentEvent.EventType.ERROR:
                    raise RuntimeError(sse.data)

                yield sse

                if sse.event == ServerSentEvent.EventType.DONE:
                    return

    async def __aiter__(self) -> AsyncIterator[ServerSentEvent]:
        decoder = EventSource.Decoder()
        async for line in self.response.aiter_lines():
            line = line.rstrip("\n")
            sse = decoder.decode(line)
            if sse is not None:
                if sse.event == ServerSentEvent.EventType.ERROR:
                    raise RuntimeError(sse.data)

                yield sse

                if sse.event == ServerSentEvent.EventType.DONE:
                    return


def stream(
    client: "Client",
    ref: Union["Model", "Version", "ModelVersionIdentifier", str],
    input: Optional[Dict[str, Any]] = None,
    **params: Unpack["Predictions.CreatePredictionParams"],
) -> Iterator[ServerSentEvent]:
    """
    Run a model and stream its output.
    """

    params = params or {}
    params["stream"] = True

    version, owner, name, version_id = identifier._resolve(ref)

    if version or version_id:
        prediction = client.predictions.create(
            version=(version or version_id), input=input or {}, **params
        )
    elif owner and name:
        prediction = client.models.predictions.create(
            model=(owner, name), input=input or {}, **params
        )
    else:
        raise ValueError(
            f"Invalid argument: {ref}. Expected model, version, or reference in the format owner/name or owner/name:version"
        )

    url = prediction.urls and prediction.urls.get("stream", None)
    if not url or not isinstance(url, str):
        raise ReplicateError("Model does not support streaming")

    headers = {}
    headers["Accept"] = "text/event-stream"
    headers["Cache-Control"] = "no-store"

    with client._client.stream("GET", url, headers=headers) as response:
        yield from EventSource(response)


async def async_stream(
    client: "Client",
    ref: Union["Model", "Version", "ModelVersionIdentifier", str],
    input: Optional[Dict[str, Any]] = None,
    **params: Unpack["Predictions.CreatePredictionParams"],
) -> AsyncIterator[ServerSentEvent]:
    """
    Run a model and stream its output asynchronously.
    """

    params = params or {}
    params["stream"] = True

    version, owner, name, version_id = identifier._resolve(ref)

    if version or version_id:
        prediction = await client.predictions.async_create(
            version=(version or version_id), input=input or {}, **params
        )
    elif owner and name:
        prediction = await client.models.predictions.async_create(
            model=(owner, name), input=input or {}, **params
        )
    else:
        raise ValueError(
            f"Invalid argument: {ref}. Expected model, version, or reference in the format owner/name or owner/name:version"
        )

    url = prediction.urls and prediction.urls.get("stream", None)
    if not url or not isinstance(url, str):
        raise ReplicateError("Model does not support streaming")

    headers = {}
    headers["Accept"] = "text/event-stream"
    headers["Cache-Control"] = "no-store"

    async with client._async_client.stream("GET", url, headers=headers) as response:
        async for event in EventSource(response):
            yield event


__all__ = ["ServerSentEvent"]
