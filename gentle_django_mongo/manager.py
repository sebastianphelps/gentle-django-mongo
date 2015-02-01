from .queryset import MongoQuerySet


class MongoManager(object):

    def __init__(self, model=None):
        self.model = model

    def filter(self, *args, **kwargs):
        return MongoQuerySet(model=self.model).filter(*args, **kwargs)

    def all(self):
        return MongoQuerySet(model=self.model).all()

    def get(self, **kwargs):
        return MongoQuerySet(model=self.model).get(**kwargs)

    def create(self, **kwargs):
        instance = self.model(**kwargs)
        instance.save()
        return instance

    def count(self):
        return self.model.collection().count()

    def get_query_set(self):
        return MongoQuerySet(model=self.model)
