Module replicate.model
======================

Classes
-------

`Model(**data: Any)`
:   A machine learning model hosted on Replicate.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * replicate.resource.Resource
    * pydantic.v1.main.BaseModel
    * pydantic.v1.utils.Representation

    ### Class variables

    `cover_image_url: Optional[str]`
    :   The URL of the cover image for the model.

    `default_example: Optional[replicate.prediction.Prediction]`
    :   The default example of the model.

    `description: Optional[str]`
    :   The description of the model.

    `github_url: Optional[str]`
    :   The GitHub URL of the model.

    `latest_version: Optional[replicate.version.Version]`
    :   The latest version of the model.

    `license_url: Optional[str]`
    :   The URL of the license for the model.

    `name: str`
    :   The name of the model.

    `owner: str`
    :   The owner of the model.

    `paper_url: Optional[str]`
    :   The URL of the paper related to the model.

    `run_count: int`
    :   The number of runs of the model.

    `url: str`
    :   The URL of the model.

    `visibility: Literal['public', 'private']`
    :   The visibility of the model. Can be 'public' or 'private'.

    ### Instance variables

    `id: str`
    :   Return the qualified model name, in the format `owner/name`.

    `username: str`
    :   The name of the user or organization that owns the model.
        This attribute is deprecated and will be removed in future versions.

    `versions: replicate.version.Versions`
    :   Get the versions of this model.

    ### Methods

    `predict(self, *args, **kwargs) ‑> None`
    :   DEPRECATED: Use `replicate.run()` instead.

    `reload(self) ‑> None`
    :   Load this object from the server.

`Models(client: Client)`
:   Namespace for operations related to models.

    ### Ancestors (in MRO)

    * replicate.resource.Namespace
    * abc.ABC

    ### Class variables

    `CreateModelParams`
    :   Parameters for creating a model.

    `model`
    :   A machine learning model hosted on Replicate.

    ### Instance variables

    `predictions: replicate.model.ModelsPredictions`
    :   Get a namespace for operations related to predictions on a model.

    ### Methods

    `async_create(self, owner: str, name: str, **params: Unpack[ForwardRef('Models.CreateModelParams')]) ‑> replicate.model.Model`
    :   Create a model.

    `async_get(self, key: str) ‑> replicate.model.Model`
    :   Get a model by name.
        
        Args:
            key: The qualified name of the model, in the format `owner/model-name`.
        Returns:
            The model.

    `async_list(self, cursor: Union[str, ForwardRef('ellipsis'), ForwardRef(None)] = Ellipsis) ‑> replicate.pagination.Page[replicate.model.Model]`
    :   List all public models.
        
        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Model]: A page of of models.
        Raises:
            ValueError: If `cursor` is `None`.

    `create(self, owner: str, name: str, **params: Unpack[ForwardRef('Models.CreateModelParams')]) ‑> replicate.model.Model`
    :   Create a model.

    `get(self, key: str) ‑> replicate.model.Model`
    :   Get a model by name.
        
        Args:
            key: The qualified name of the model, in the format `owner/model-name`.
        Returns:
            The model.

    `list(self, cursor: Union[str, ForwardRef('ellipsis'), ForwardRef(None)] = Ellipsis) ‑> replicate.pagination.Page[replicate.model.Model]`
    :   List all public models.
        
        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Model]: A page of of models.
        Raises:
            ValueError: If `cursor` is `None`.

`ModelsPredictions(client: Client)`
:   Namespace for operations related to predictions in a deployment.

    ### Ancestors (in MRO)

    * replicate.resource.Namespace
    * abc.ABC

    ### Methods

    `async_create(self, model: Union[str, Tuple[str, str], ForwardRef('Model')], input: Dict[str, Any], **params: Unpack[ForwardRef('Predictions.CreatePredictionParams')]) ‑> replicate.prediction.Prediction`
    :   Create a new prediction with the deployment.

    `create(self, model: Union[str, Tuple[str, str], ForwardRef('Model')], input: Dict[str, Any], **params: Unpack[ForwardRef('Predictions.CreatePredictionParams')]) ‑> replicate.prediction.Prediction`
    :   Create a new prediction with the deployment.