Module replicate.exceptions
===========================

Classes
-------

`ModelError(*args, **kwargs)`
:   An error from user's code in a model.

    ### Ancestors (in MRO)

    * replicate.exceptions.ReplicateException
    * builtins.Exception
    * builtins.BaseException

`ReplicateError(type: Optional[str] = None, title: Optional[str] = None, status: Optional[int] = None, detail: Optional[str] = None, instance: Optional[str] = None)`
:   An error from Replicate's API.
    
    This class represents a problem details response as defined in RFC 7807.

    ### Ancestors (in MRO)

    * replicate.exceptions.ReplicateException
    * builtins.Exception
    * builtins.BaseException

    ### Class variables

    `detail: Optional[str]`
    :   A human-readable explanation specific to this occurrence of the error.

    `instance: Optional[str]`
    :   A URI that identifies the specific occurrence of the error.

    `status: Optional[int]`
    :   The HTTP status code.

    `title: Optional[str]`
    :   A short, human-readable summary of the error.

    `type: Optional[str]`
    :   A URI that identifies the error type.

    ### Static methods

    `from_response(response: httpx.Response) ‑> replicate.exceptions.ReplicateError`
    :   Create a ReplicateError from an HTTP response.

    ### Methods

    `to_dict(self) ‑> dict`
    :   Get a dictionary representation of the error.

`ReplicateException(*args, **kwargs)`
:   A base class for all Replicate exceptions.

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException

    ### Descendants

    * replicate.exceptions.ModelError
    * replicate.exceptions.ReplicateError