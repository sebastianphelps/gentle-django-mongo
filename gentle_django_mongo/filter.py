from copy import deepcopy
import re

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

    def __init__(self, query_terms, order_by=[]):
        self.query_terms = query_terms
        self.order_by = order_by
        self.where = None

    def clone(self):
        return MongoFilter(deepcopy(self.query_terms))

    def add_filters(self, extra_filters):
        for name, value in extra_filters.items():
            # If you re-filter on the same column this will replace what you filtered before
            self.query_terms[name] = value

    @property
    def is_empty(self):
        return len(self.query_terms) == 0

    def as_mongo_filter(self):
        # Convert this to a mongo filter
        mongo_filter = {}
        for name, value in self.query_terms.items():
            fields = name.split("__")
            op = None
            if len(fields) > 1 and fields[-1] in OPERATORS_MAP.keys():
                op = fields[-1]

                if fields[0] == ["id", "pk"] and op in ["exact", "iexact"]:
                    value = ObjectId(value)
                elif fields[0] == ["id", "pk"] and op in ["in"]:
                    value = map(lambda x: ObjectId(x), value)

                value = OPERATORS_MAP[op](value)
                fields = fields[:-1]

            if fields[0] in ["id", "pk"]:
                fields[0] = "_id"
                if op is None:
                    value = ObjectId(value)

            mongo_filter[".".join(fields)] = value

        return mongo_filter
