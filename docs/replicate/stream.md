Module replicate.stream
=======================

Classes
-------

`ServerSentEvent(**data: Any)`
:   A server-sent event.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * pydantic.v1.main.BaseModel
    * pydantic.v1.utils.Representation

    ### Class variables

    `EventType`
    :   A server-sent event type.

    `data: str`
    :

    `event: replicate.stream.ServerSentEvent.EventType`
    :

    `id: str`
    :

    `retry: Optional[int]`
    :