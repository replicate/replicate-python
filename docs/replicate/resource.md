Module replicate.resource
=========================

Classes
-------

`Namespace(client: Client)`
:   A base class for representing objects of a particular type on the server.

    ### Ancestors (in MRO)

    * abc.ABC

    ### Descendants

    * replicate.account.Accounts
    * replicate.collection.Collections
    * replicate.deployment.DeploymentPredictions
    * replicate.deployment.Deployments
    * replicate.deployment.DeploymentsPredictions
    * replicate.hardware.HardwareNamespace
    * replicate.model.Models
    * replicate.model.ModelsPredictions
    * replicate.prediction.Predictions
    * replicate.training.Trainings
    * replicate.version.Versions

`Resource(**data: Any)`
:   A base class for representing a single object on the server.
    
    Create a new model by parsing and validating input data from keyword arguments.
    
    Raises ValidationError if the input data cannot be parsed to form a valid model.

    ### Ancestors (in MRO)

    * pydantic.v1.main.BaseModel
    * pydantic.v1.utils.Representation

    ### Descendants

    * replicate.account.Account
    * replicate.collection.Collection
    * replicate.deployment.Deployment
    * replicate.deployment.Deployment.Release
    * replicate.deployment.Deployment.Release.Configuration
    * replicate.hardware.Hardware
    * replicate.model.Model
    * replicate.prediction.Prediction
    * replicate.training.Training
    * replicate.version.Version