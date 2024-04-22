Module replicate.training
=========================

Classes
-------

`Training(**data: Any)`
:   A training made for a model hosted on Replicate.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * replicate.resource.Resource
    * pydantic.v1.main.BaseModel
    * pydantic.v1.utils.Representation

    ### Class variables

    `completed_at: Optional[str]`
    :   When the training was completed, if finished.

    `created_at: Optional[str]`
    :   When the training was created.

    `destination: Optional[str]`
    :   The model destination of the training.

    `error: Optional[str]`
    :   The error encountered during the training, if any.

    `id: str`
    :   The unique ID of the training.

    `input: Optional[Dict[str, Any]]`
    :   The input to the training.

    `logs: Optional[str]`
    :   The logs of the training.

    `model: str`
    :   An identifier for the model used to create the prediction, in the form `owner/name`.

    `output: Optional[Any]`
    :   The output of the training.

    `started_at: Optional[str]`
    :   When the training was started.

    `status: Literal['starting', 'processing', 'succeeded', 'failed', 'canceled']`
    :   The status of the training.

    `urls: Optional[Dict[str, str]]`
    :   URLs associated with the training.
        
        The following keys are available:
        - `get`: A URL to fetch the training.
        - `cancel`: A URL to cancel the training.

    `version: Union[replicate.version.Version, str]`
    :   The version of the model used to create the training.

    ### Methods

    `async_cancel(self) ‑> None`
    :   Cancel a running training asynchronously.

    `async_reload(self) ‑> None`
    :   Load the training from the server asynchronously.

    `cancel(self) ‑> None`
    :   Cancel a running training.

    `reload(self) ‑> None`
    :   Load the training from the server.

`Trainings(client: Client)`
:   Namespace for operations related to trainings.

    ### Ancestors (in MRO)

    * replicate.resource.Namespace
    * abc.ABC

    ### Class variables

    `CreateTrainingParams`
    :   Parameters for creating a training.

    ### Methods

    `async_cancel(self, id: str) ‑> replicate.training.Training`
    :   Cancel a training.
        
        Args:
            id: The ID of the training to cancel.
        Returns:
            Training: The canceled training object.

    `async_create(self, model: Union[str, Tuple[str, str], ForwardRef('Model')], version: Union[replicate.version.Version, str], input: Dict[str, Any], **params: Unpack[ForwardRef('Trainings.CreateTrainingParams')]) ‑> replicate.training.Training`
    :   Create a new training using the specified model version as a base.
        
        Args:
            version: The ID of the base model version that you're using to train a new model version.
            input: The input to the training.
            destination: The desired model to push to in the format `{owner}/{model_name}`. This should be an existing model owned by the user or organization making the API request.
            webhook: The URL to send a POST request to when the training is completed. Defaults to None.
            webhook_completed: The URL to receive a POST request when the prediction is completed.
            webhook_events_filter: The events to send to the webhook. Defaults to None.
        Returns:
            The training object.

    `async_get(self, id: str) ‑> replicate.training.Training`
    :   Get a training by ID.
        
        Args:
            id: The ID of the training.
        Returns:
            Training: The training object.

    `async_list(self, cursor: Union[str, ForwardRef('ellipsis'), ForwardRef(None)] = Ellipsis) ‑> replicate.pagination.Page[replicate.training.Training]`
    :   List your trainings.
        
        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Training]: A page of trainings.
        Raises:
            ValueError: If `cursor` is `None`.

    `cancel(self, id: str) ‑> replicate.training.Training`
    :   Cancel a training.
        
        Args:
            id: The ID of the training to cancel.
        Returns:
            Training: The canceled training object.

    `create(self, *args, model: Union[str, Tuple[str, str], ForwardRef('Model'), ForwardRef(None)] = None, version: Union[replicate.version.Version, str, ForwardRef(None)] = None, input: Optional[Dict[str, Any]] = None, **params: Unpack[ForwardRef('Trainings.CreateTrainingParams')]) ‑> replicate.training.Training`
    :   Create a new training using the specified model version as a base.

    `get(self, id: str) ‑> replicate.training.Training`
    :   Get a training by ID.
        
        Args:
            id: The ID of the training.
        Returns:
            Training: The training object.

    `list(self, cursor: Union[str, ForwardRef('ellipsis'), ForwardRef(None)] = Ellipsis) ‑> replicate.pagination.Page[replicate.training.Training]`
    :   List your trainings.
        
        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Training]: A page of trainings.
        Raises:
            ValueError: If `cursor` is `None`.