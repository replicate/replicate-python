Module replicate.version
========================

Classes
-------

`Version(**data: Any)`
:   A version of a model.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * replicate.resource.Resource
    * pydantic.v1.main.BaseModel
    * pydantic.v1.utils.Representation

    ### Class variables

    `cog_version: str`
    :   The version of the Cog used to create the version.

    `created_at: datetime.datetime`
    :   When the version was created.

    `id: str`
    :   The unique ID of the version.

    `openapi_schema: dict`
    :   An OpenAPI description of the model inputs and outputs.

`Versions(client: Client, model: Union[str, Tuple[str, str], ForwardRef('Model')])`
:   Namespace for operations related to model versions.

    ### Ancestors (in MRO)

    * replicate.resource.Namespace
    * abc.ABC

    ### Class variables

    `model: Tuple[str, str]`
    :

    ### Methods

    `async_delete(self, id: str) ‑> bool`
    :   Delete a model version and all associated predictions, including all output files.
        
        Model version deletion has some restrictions:
        
        * You can only delete versions from models you own.
        * You can only delete versions from private models.
        * You cannot delete a version if someone other than you
          has run predictions with it.
        
        Args:
            id: The version ID.

    `async_get(self, id: str) ‑> replicate.version.Version`
    :   Get a specific model version.
        
        Args:
            id: The version ID.
        Returns:
            The model version.

    `async_list(self) ‑> replicate.pagination.Page[replicate.version.Version]`
    :   Return a list of all versions for a model.
        
        Returns:
            List[Version]: A list of version objects.

    `delete(self, id: str) ‑> bool`
    :   Delete a model version and all associated predictions, including all output files.
        
        Model version deletion has some restrictions:
        
        * You can only delete versions from models you own.
        * You can only delete versions from private models.
        * You cannot delete a version if someone other than you
          has run predictions with it.
        
        Args:
            id: The version ID.

    `get(self, id: str) ‑> replicate.version.Version`
    :   Get a specific model version.
        
        Args:
            id: The version ID.
        Returns:
            The model version.

    `list(self) ‑> replicate.pagination.Page[replicate.version.Version]`
    :   Return a list of all versions for a model.
        
        Returns:
            List[Version]: A list of version objects.