Module replicate.pagination
===========================

Functions
---------

    
`async_paginate(list_method: Callable[[Union[str, ForwardRef('ellipsis'), ForwardRef(None)]], Awaitable[replicate.pagination.Page[~T]]]) ‑> AsyncGenerator[replicate.pagination.Page[~T], None]`
:   Asynchronously iterate over all items using the provided list method.
    
    Args:
        list_method: An async method that takes a cursor argument and returns a Page of items.

    
`paginate(list_method: Callable[[Union[str, ForwardRef('ellipsis'), ForwardRef(None)]], replicate.pagination.Page[~T]]) ‑> Generator[replicate.pagination.Page[~T], None, None]`
:   Iterate over all items using the provided list method.
    
    Args:
        list_method: A method that takes a cursor argument and returns a Page of items.

Classes
-------

`Page(**data: Any)`
:   A page of results from the API.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * pydantic.v1.main.BaseModel
    * pydantic.v1.utils.Representation
    * typing.Generic

    ### Class variables

    `next: Optional[str]`
    :   A pointer to the next page of results

    `previous: Optional[str]`
    :   A pointer to the previous page of results

    `results: List[~T]`
    :   The results on this page