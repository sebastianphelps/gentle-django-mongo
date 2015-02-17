from pymongo import ASCENDING, DESCENDING

from .filter import MongoFilter


class MongoQuerySet(object):

    def __init__(self, model=None, cursor=None):
        self.model = model
        self.cursor = cursor
        self.query = MongoFilter({}, model=model)

    def get_cursor(self):
        if self.cursor is None:
            raise Exception("No cursor - Query set wasn't run against anything")
        return self.cursor

    def __iter__(self):
        return self

    def next(self):
		# Needed when mocking mongo
        if isinstance(self.cursor, list):
            self.cursor = iter(self.cursor)
        return self.doc_to_instance(self.cursor.next())

    def filter(self, *args, **kwargs):
        # Convert filter to mongo format
        self.query.add_filters(kwargs)
        self.cursor = self.model.collection().find(self.query.as_mongo_filter())
        return self

    def get(self, **kwargs):
        try:
            return self.filter(**kwargs)[0]
        except IndexError:
            raise self.model.DoesNotExist()

    def delete(self, delete_all=False):
        if self.query.is_empty and not delete_all:
            raise Exception("If you want to delete everything in collection() pass delete_all=True")
        self.model.collection().find(self.query.as_mongo_filter())

    def count(self):
        return self.get_cursor().count()

    def clone(self):
        return self._clone()

    def _clone(self):
        """This method seems pointless but is called by libraries like tastypie"""
        cloned_cursor = None
        if self.cursor:
            cloned_cursor = self.cursor.clone()
        cloned_queryset = MongoQuerySet(model=self.model, cursor=cloned_cursor)
        cloned_queryset.query = self.query.clone()
        return cloned_queryset

    def doc_to_instance(self, doc):
        instance = self.model()
        for name, value in doc.items():
            setattr(instance, name, value)
        return instance

    def update(self, **kwargs):
        # Todo: handle timezone aware datetime fields
        updated_fields = {}
        for name, value in kwargs.items():
            updated_fields[".".join(name.split("__"))] = value
        self.model.collection().update(
            self.query.as_mongo_filter(),
            {"$set": updated_fields}
        )

    def __getitem__(self, index):
        clone = self.clone()

        if isinstance(index, slice):
            clone.cursor = clone.cursor.__getitem__(index)
            return clone

        if isinstance(index, (int, long)):
            return self.doc_to_instance(clone.cursor.__getitem__(index))

        raise TypeError("index %r cannot be applied to Cursor instances" % index)

    def order_by(self, *args):
        self.query.order_by = args
        sort_list = []
        for arg in args:
            direction = ASCENDING
            if arg.startswith("-"):
                direction = DESCENDING
                arg = arg[1:]  # Strip the -
            sort_list.append((arg, direction))
        if len(sort_list) == 0:
            return self
        self.cursor = self.get_cursor().sort(sort_list)
        return self

    def all(self):
        self.cursor = self.model.collection().find()
        return self

    def __len__(self):
        return self.count()
