Module replicate.deployment
===========================

Classes
-------

`Deployment(**data: Any)`
:   A deployment of a model hosted on Replicate.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * replicate.resource.Resource
    * pydantic.v1.main.BaseModel
    * pydantic.v1.utils.Representation

    ### Class variables

    `Release`
    :   A release of a deployment.

    `current_release: Optional[replicate.deployment.Deployment.Release]`
    :   The current release of the deployment.

    `name: str`
    :   The name of the deployment.

    `owner: str`
    :   The name of the user or organization that owns the deployment.

    ### Instance variables

    `id: str`
    :   Return the qualified deployment name, in the format `owner/name`.

    `predictions: replicate.deployment.DeploymentPredictions`
    :   Get the predictions for this deployment.

    `username: str`
    :   The name of the user or organization that owns the deployment.
        This attribute is deprecated and will be removed in future versions.

`DeploymentPredictions(client: Client, deployment: replicate.deployment.Deployment)`
:   Namespace for operations related to predictions in a deployment.

    ### Ancestors (in MRO)

    * replicate.resource.Namespace
    * abc.ABC

    ### Methods

    `async_create(self, input: Dict[str, Any], **params: Unpack[ForwardRef('Predictions.CreatePredictionParams')]) ‑> replicate.prediction.Prediction`
    :   Create a new prediction with the deployment.

    `create(self, input: Dict[str, Any], **params: Unpack[ForwardRef('Predictions.CreatePredictionParams')]) ‑> replicate.prediction.Prediction`
    :   Create a new prediction with the deployment.

`Deployments(client: Client)`
:   Namespace for operations related to deployments.

    ### Ancestors (in MRO)

    * replicate.resource.Namespace
    * abc.ABC

    ### Class variables

    `CreateDeploymentParams`
    :   Parameters for creating a new deployment.

    `UpdateDeploymentParams`
    :   Parameters for updating an existing deployment.

    ### Instance variables

    `predictions: replicate.deployment.DeploymentsPredictions`
    :   Get predictions for deployments.

    ### Methods

    `async_create(self, **params: Unpack[replicate.deployment.Deployments.CreateDeploymentParams]) ‑> replicate.deployment.Deployment`
    :   Create a new deployment.
        
        Args:
            params: Configuration for the new deployment.
        Returns:
            The newly created Deployment.

    `async_get(self, name: str) ‑> replicate.deployment.Deployment`
    :   Get a deployment by name.
        
        Args:
            name: The name of the deployment, in the format `owner/model-name`.
        Returns:
            The model.

    `async_list(self, cursor: Union[str, ForwardRef('ellipsis'), ForwardRef(None)] = Ellipsis) ‑> replicate.pagination.Page[replicate.deployment.Deployment]`
    :   List all deployments.
        
        Returns:
            A page of Deployments.

    `async_update(self, deployment_owner: str, deployment_name: str, **params: Unpack[replicate.deployment.Deployments.UpdateDeploymentParams]) ‑> replicate.deployment.Deployment`
    :   Update an existing deployment.
        
        Args:
            deployment_owner: The owner of the deployment.
            deployment_name: The name of the deployment.
            params: Configuration updates for the deployment.
        Returns:
            The updated Deployment.

    `create(self, **params: Unpack[replicate.deployment.Deployments.CreateDeploymentParams]) ‑> replicate.deployment.Deployment`
    :   Create a new deployment.
        
        Args:
            params: Configuration for the new deployment.
        Returns:
            The newly created Deployment.

    `get(self, name: str) ‑> replicate.deployment.Deployment`
    :   Get a deployment by name.
        
        Args:
            name: The name of the deployment, in the format `owner/model-name`.
        Returns:
            The model.

    `list(self, cursor: Union[str, ForwardRef('ellipsis'), ForwardRef(None)] = Ellipsis) ‑> replicate.pagination.Page[replicate.deployment.Deployment]`
    :   List all deployments.
        
        Returns:
            A page of Deployments.

    `update(self, deployment_owner: str, deployment_name: str, **params: Unpack[replicate.deployment.Deployments.UpdateDeploymentParams]) ‑> replicate.deployment.Deployment`
    :   Update an existing deployment.
        
        Args:
            deployment_owner: The owner of the deployment.
            deployment_name: The name of the deployment.
            params: Configuration updates for the deployment.
        Returns:
            The updated Deployment.

`DeploymentsPredictions(client: Client)`
:   Namespace for operations related to predictions in deployments.

    ### Ancestors (in MRO)

    * replicate.resource.Namespace
    * abc.ABC

    ### Methods

    `async_create(self, deployment: Union[str, Tuple[str, str], replicate.deployment.Deployment], input: Dict[str, Any], **params: Unpack[ForwardRef('Predictions.CreatePredictionParams')]) ‑> replicate.prediction.Prediction`
    :   Create a new prediction with the deployment.

    `create(self, deployment: Union[str, Tuple[str, str], replicate.deployment.Deployment], input: Dict[str, Any], **params: Unpack[ForwardRef('Predictions.CreatePredictionParams')]) ‑> replicate.prediction.Prediction`
    :   Create a new prediction with the deployment.