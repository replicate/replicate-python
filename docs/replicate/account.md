Module replicate.account
========================

Classes
-------

`Account(**data: Any)`
:   A user or organization account on Replicate.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * replicate.resource.Resource
    * pydantic.v1.main.BaseModel
    * pydantic.v1.utils.Representation

    ### Class variables

    `github_url: Optional[str]`
    :   The GitHub URL of the account.

    `name: str`
    :   The name of the account.

    `type: Literal['user', 'organization']`
    :   The type of account.

    `username: str`
    :   The username of the account.

`Accounts(client: Client)`
:   Namespace for operations related to accounts.

    ### Ancestors (in MRO)

    * replicate.resource.Namespace
    * abc.ABC

    ### Methods

    `async_current(self) ‑> replicate.account.Account`
    :   Get the current account.
        
        Returns:
            Account: The current account.

    `current(self) ‑> replicate.account.Account`
    :   Get the current account.
        
        Returns:
            Account: The current account.