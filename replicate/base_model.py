from typing import ForwardRef
import pydantic


Client = ForwardRef("Client")
Collection = ForwardRef("Collection")


class BaseModel(pydantic.BaseModel):
    """
    A base class for representing a single object on the server.
    """

    _client: Client = pydantic.PrivateAttr()
    _collection: Collection = pydantic.PrivateAttr()

    def __init__(self, attrs=None, client=None, collection=None):
        super().__init__(**attrs)

        #: A client pointing at the server that this object is on.
        self._client = client

        #: The collection that this model is part of.
        self._collection = collection

    def reload(self):
        """
        Load this object from the server again.
        """
        new_model = self._collection.get(self.id)
        for k, v in new_model.dict().items():
            setattr(self, k, v)
