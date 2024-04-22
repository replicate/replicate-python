Module replicate.prediction
===========================

Classes
-------

`Prediction(**data: Any)`
:   A prediction made by a model hosted on Replicate.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * replicate.resource.Resource
    * pydantic.v1.main.BaseModel
    * pydantic.v1.utils.Representation

    ### Class variables

    `Progress`
    :   The progress of a prediction.

    `completed_at: Optional[str]`
    :   When the prediction was completed, if finished.

    `created_at: Optional[str]`
    :   When the prediction was created.

    `error: Optional[str]`
    :   The error encountered during the prediction, if any.

    `id: str`
    :   The unique ID of the prediction.

    `input: Optional[Dict[str, Any]]`
    :   The input to the prediction.

    `logs: Optional[str]`
    :   The logs of the prediction.

    `metrics: Optional[Dict[str, Any]]`
    :   Metrics for the prediction.

    `model: str`
    :   An identifier for the model used to create the prediction, in the form `owner/name`.

    `output: Optional[Any]`
    :   The output of the prediction.

    `started_at: Optional[str]`
    :   When the prediction was started.

    `status: Literal['starting', 'processing', 'succeeded', 'failed', 'canceled']`
    :   The status of the prediction.

    `urls: Optional[Dict[str, str]]`
    :   URLs associated with the prediction.
        
        The following keys are available:
        - `get`: A URL to fetch the prediction.
        - `cancel`: A URL to cancel the prediction.

    `version: str`
    :   An identifier for the version of the model used to create the prediction.

    ### Instance variables

    `progress: Optional[replicate.prediction.Prediction.Progress]`
    :   The progress of the prediction, if available.

    ### Methods

    `async_cancel(self) ‑> None`
    :   Cancels a running prediction asynchronously.

    `async_output_iterator(self) ‑> AsyncIterator[Any]`
    :   Return an asynchronous iterator of the prediction output.

    `async_reload(self) ‑> None`
    :   Load this prediction from the server asynchronously.

    `async_stream(self) ‑> AsyncIterator[ServerSentEvent]`
    :   Stream the prediction output asynchronously.
        
        Raises:
            ReplicateError: If the model does not support streaming.

    `async_wait(self) ‑> None`
    :   Wait for prediction to finish asynchronously.

    `cancel(self) ‑> None`
    :   Cancels a running prediction.

    `output_iterator(self) ‑> Iterator[Any]`
    :   Return an iterator of the prediction output.

    `reload(self) ‑> None`
    :   Load this prediction from the server.

    `stream(self) ‑> Iterator[ServerSentEvent]`
    :   Stream the prediction output.
        
        Raises:
            ReplicateError: If the model does not support streaming.

    `wait(self) ‑> None`
    :   Wait for prediction to finish.

`Predictions(client: Client)`
:   Namespace for operations related to predictions.

    ### Ancestors (in MRO)

    * replicate.resource.Namespace
    * abc.ABC

    ### Class variables

    `CreatePredictionParams`
    :   Parameters for creating a prediction.

    ### Methods

    `async_cancel(self, id: str) ‑> replicate.prediction.Prediction`
    :   Cancel a prediction.
        
        Args:
            id: The ID of the prediction to cancel.
        Returns:
            Prediction: The canceled prediction object.

    `async_create(self, version: Union[replicate.version.Version, str], input: Optional[Dict[str, Any]], **params: Unpack[ForwardRef('Predictions.CreatePredictionParams')]) ‑> replicate.prediction.Prediction`
    :   Create a new prediction for the specified model version.

    `async_get(self, id: str) ‑> replicate.prediction.Prediction`
    :   Get a prediction by ID.
        
        Args:
            id: The ID of the prediction.
        Returns:
            Prediction: The prediction object.

    `async_list(self, cursor: Union[str, ForwardRef('ellipsis'), ForwardRef(None)] = Ellipsis) ‑> replicate.pagination.Page[replicate.prediction.Prediction]`
    :   List your predictions.
        
        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Prediction]: A page of of predictions.
        Raises:
            ValueError: If `cursor` is `None`.

    `cancel(self, id: str) ‑> replicate.prediction.Prediction`
    :   Cancel a prediction.
        
        Args:
            id: The ID of the prediction to cancel.
        Returns:
            Prediction: The canceled prediction object.

    `create(self, version: Union[replicate.version.Version, str], input: Optional[Dict[str, Any]], **params: Unpack[ForwardRef('Predictions.CreatePredictionParams')]) ‑> replicate.prediction.Prediction`
    :   Create a new prediction for the specified model version.

    `get(self, id: str) ‑> replicate.prediction.Prediction`
    :   Get a prediction by ID.
        
        Args:
            id: The ID of the prediction.
        Returns:
            Prediction: The prediction object.

    `list(self, cursor: Union[str, ForwardRef('ellipsis'), ForwardRef(None)] = Ellipsis) ‑> replicate.pagination.Page[replicate.prediction.Prediction]`
    :   List your predictions.
        
        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Prediction]: A page of of predictions.
        Raises:
            ValueError: If `cursor` is `None`.