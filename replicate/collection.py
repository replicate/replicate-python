from replicate.base_model import BaseModel


class Collection:
    """
    A base class for representing all objects of a particular type on the
    server.
    """

    model: BaseModel = None

    def __init__(self, client=None):
        self._client = client

    def list(self):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def create(self, attrs=None):
        raise NotImplementedError

    def prepare_model(self, attrs):
        """
        Create a model from a set of attributes.
        """
        if isinstance(attrs, BaseModel):
            attrs._client = self._client
            attrs._collection = self
            return attrs
        elif isinstance(attrs, dict):
            model = self.model(**attrs)
            model._client = self._client
            model._collection = self
            return model
        else:
            raise Exception("Can't create %s from %s" % (self.model.__name__, attrs))
