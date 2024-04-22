Module replicate.hardware
=========================

Classes
-------

`Hardware(**data: Any)`
:   Hardware for running a model on Replicate.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * replicate.resource.Resource
    * pydantic.v1.main.BaseModel
    * pydantic.v1.utils.Representation

    ### Class variables

    `name: str`
    :   The name of the hardware.

    `sku: str`
    :   The SKU of the hardware.

    ### Instance variables

    `id: str`
    :   DEPRECATED: Use `sku` instead.

`HardwareNamespace(client: Client)`
:   Namespace for operations related to hardware.

    ### Ancestors (in MRO)

    * replicate.resource.Namespace
    * abc.ABC

    ### Methods

    `async_list(self) ‑> List[replicate.hardware.Hardware]`
    :   List all hardware available for you to run models on Replicate.
        
        Returns:
            List[Hardware]: A list of hardware.

    `list(self) ‑> List[replicate.hardware.Hardware]`
    :   List all hardware available for you to run models on Replicate.
        
        Returns:
            List[Hardware]: A list of hardware.