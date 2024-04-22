Module replicate.collection
===========================

Classes
-------

`Collection(**data: Any)`
:   A collection of models on Replicate.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * replicate.resource.Resource
    * pydantic.v1.main.BaseModel
    * pydantic.v1.utils.Representation

    ### Class variables

    `description: str`
    :   A description of the collection.

    `models: Optional[List[replicate.model.Model]]`
    :   The models in the collection.

    `name: str`
    :   The name of the collection.

    `slug: str`
    :   The slug used to identify the collection.

    ### Instance variables

    `id: str`
    :   DEPRECATED: Use `slug` instead.

`Collections(client: Client)`
:   A namespace for operations related to collections of models.

    ### Ancestors (in MRO)

    * replicate.resource.Namespace
    * abc.ABC

    ### Methods

    `async_get(self, slug: str) ‑> replicate.collection.Collection`
    :   Get a model by name.
        
        Args:
            name: The name of the model, in the format `owner/model-name`.
        Returns:
            The model.

    `async_list(self, cursor: Union[str, ForwardRef('ellipsis'), ForwardRef(None)] = Ellipsis) ‑> replicate.pagination.Page[replicate.collection.Collection]`
    :   List collections of models.
        
        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Collection]: A page of of model collections.
        Raises:
            ValueError: If `cursor` is `None`.

    `get(self, slug: str) ‑> replicate.collection.Collection`
    :   Get a model by name.
        
        Args:
            name: The name of the model, in the format `owner/model-name`.
        Returns:
            The model.

    `list(self, cursor: Union[str, ForwardRef('ellipsis'), ForwardRef(None)] = Ellipsis) ‑> replicate.pagination.Page[replicate.collection.Collection]`
    :   List collections of models.
        
        Parameters:
            cursor: The cursor to use for pagination. Use the value of `Page.next` or `Page.previous`.
        Returns:
            Page[Collection]: A page of of model collections.
        Raises:
            ValueError: If `cursor` is `None`.