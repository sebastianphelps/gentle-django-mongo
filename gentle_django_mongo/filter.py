from copy import deepcopy
import re

from django.db.models.sql.constants import QUERY_TERMS
from bson.objectid import ObjectId

OPERATORS_MAP = {
    'exact': lambda val: val,
    'gt': lambda val: {'$gt': val},
    'gte': lambda val: {'$gte': val},
    'lt': lambda val: {'$lt': val},
    'lte': lambda val: {'$lte': val},
    'in': lambda val: {'$in': val},
    'range': lambda val: {'$gte': val[0], '$lte': val[1]},
    'isnull': lambda val: None if val else {'$ne': None},
    'iexact': lambda val: re.compile('^%s$' % re.escape(val), re.IGNORECASE),
    'startswith': lambda val: re.compile('^%s' % re.escape(val)),
    'istartswith': lambda val: re.compile('^%s' % re.escape(val), re.IGNORECASE),
    'endswith': lambda val: re.compile('%s$' % re.escape(val)),
    'iendswith': lambda val: re.compile('%s$' % re.escape(val), re.IGNORECASE),
    'contains': lambda val: re.compile('%s' % re.escape(val)),
    'icontains': lambda val: re.compile('%s' % re.escape(val), re.IGNORECASE),
    'regex': lambda val: re.compile(val),
    'iregex': lambda val: re.compile(val, re.IGNORECASE)
}


class MongoFilter(object):
    select_related = False
    query_terms = QUERY_TERMS

    def __init__(self, filter_terms, order_by=None, model=None):
        self.filter_terms = filter_terms
        if order_by is None:
            order_by = []
        self.order_by = order_by
        self.where = None
        self.model = model

    def clone(self):
        return MongoFilter(deepcopy(self.filter_terms), order_by=deepcopy(self.order_by),
                           model=self.model)

    def add_filters(self, extra_filters):
        for name, value in extra_filters.items():
            # If you re-filter on the same column this will replace what you filtered before
            self.filter_terms[name] = value

    @property
    def is_empty(self):
        return len(self.filter_terms) == 0

    def as_mongo_filter(self):
        # Convert this to a mongo filter
        mongo_filter = {}
        for name, value in self.filter_terms.items():
            fields = name.split("__")
            op = None
            if len(fields) > 1 and fields[-1] in OPERATORS_MAP.keys():
                op = fields[-1]

                if fields[0] == ["id", "pk"] and op in ["exact", "iexact"]:
                    value = ObjectId(value)
                elif fields[0] == ["id", "pk"] and op in ["in"]:
                    value = map(lambda x: ObjectId(x), value)
                fields = fields[:-1]

            if fields[0] in ["id", "pk"]:
                fields[0] = "_id"
                if op is None:
                    value = ObjectId(value)
            elif len(fields) == 1:
                if isinstance(value, (list, tuple)):
                    value = map(
                         lambda x: self.model._meta.get_field(fields[0]).get_prep_value(x),
                         value
                     )
                else:
                    value = self.model._meta.get_field(fields[0]).get_prep_value(value)

            if op:
                value = OPERATORS_MAP[op](value)

            mongo_filter[".".join(fields)] = value

        return mongo_filter
