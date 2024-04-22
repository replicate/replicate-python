Module replicate.client
=======================

Classes
-------

`Client(api_token: Optional[str] = None, *, base_url: Optional[str] = None, timeout: Optional[httpx.Timeout] = None, **kwargs)`
:   A Replicate API client library

    ### Instance variables

    `accounts: replicate.account.Accounts`
    :   Namespace for operations related to accounts.

    `collections: replicate.collection.Collections`
    :   Namespace for operations related to collections of models.

    `deployments: replicate.deployment.Deployments`
    :   Namespace for operations related to deployments.

    `hardware: replicate.hardware.HardwareNamespace`
    :   Namespace for operations related to hardware.

    `models: replicate.model.Models`
    :   Namespace for operations related to models.

    `predictions: replicate.prediction.Predictions`
    :   Namespace for operations related to predictions.

    `trainings: replicate.training.Trainings`
    :   Namespace for operations related to trainings.

    ### Methods

    `async_run(self, ref: str, input: Optional[Dict[str, Any]] = None, **params: Unpack[ForwardRef('Predictions.CreatePredictionParams')]) ‑> Union[Any, AsyncIterator[Any]]`
    :   Run a model and wait for its output asynchronously.

    `async_stream(self, ref: str, input: Optional[Dict[str, Any]] = None, **params: Unpack[ForwardRef('Predictions.CreatePredictionParams')]) ‑> AsyncIterator[ServerSentEvent]`
    :   Stream a model's output asynchronously.

    `run(self, ref: str, input: Optional[Dict[str, Any]] = None, **params: Unpack[ForwardRef('Predictions.CreatePredictionParams')]) ‑> Union[Any, Iterator[Any]]`
    :   Run a model and wait for its output.

    `stream(self, ref: str, input: Optional[Dict[str, Any]] = None, **params: Unpack[ForwardRef('Predictions.CreatePredictionParams')]) ‑> Iterator[ServerSentEvent]`
    :   Stream a model's output.

`RetryTransport(wrapped_transport: Union[httpx.BaseTransport, httpx.AsyncBaseTransport], *, max_attempts: int = 10, max_backoff_wait: float = 60, backoff_factor: float = 0.1, jitter_ratio: float = 0.1, retryable_methods: Optional[Iterable[str]] = None, retry_status_codes: Optional[Iterable[int]] = None)`
:   A custom HTTP transport that automatically retries requests using an exponential backoff strategy
    for specific HTTP status codes and request methods.

    ### Ancestors (in MRO)

    * httpx.AsyncBaseTransport
    * httpx.BaseTransport

    ### Class variables

    `MAX_BACKOFF_WAIT`
    :

    `RETRYABLE_METHODS`
    :

    `RETRYABLE_STATUS_CODES`
    :

    ### Methods

    `aclose(self) ‑> None`
    :

    `close(self) ‑> None`
    :

    `handle_async_request(self, request: httpx.Request) ‑> httpx.Response`
    :

    `handle_request(self, request: httpx.Request) ‑> httpx.Response`
    :   Send a single HTTP request and return a response.
        
        Developers shouldn't typically ever need to call into this API directly,
        since the Client class provides all the higher level user-facing API
        niceties.
        
        In order to properly release any network resources, the response
        stream should *either* be consumed immediately, with a call to
        `response.stream.read()`, or else the `handle_request` call should
        be followed with a try/finally block to ensuring the stream is
        always closed.
        
        Example usage:
        
            with httpx.HTTPTransport() as transport:
                req = httpx.Request(
                    method=b"GET",
                    url=(b"https", b"www.example.com", 443, b"/"),
                    headers=[(b"Host", b"www.example.com")],
                )
                resp = transport.handle_request(req)
                body = resp.stream.read()
                print(resp.status_code, resp.headers, body)
        
        
        Takes a `Request` instance as the only argument.
        
        Returns a `Response` instance.