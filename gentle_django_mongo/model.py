import sys

from django.db.models.base import ModelBase
from django.db.models.options import Options
from django.db.models import FieldDoesNotExist, Field

from .manager import MongoManager
from .utils import mongo_db


class MongoModelMeta(ModelBase):

    def __new__(cls, name, bases, attrs):
        new_class = super(ModelBase, cls).__new__(cls, name, bases, attrs)
        new_class.objects.model = new_class
        new_class._default_manager.model = new_class

        meta = getattr(new_class, 'Meta')
        if getattr(meta, 'app_label', None) is None:
            # Figure out the app_label by looking one level up.
            # For 'django.contrib.sites.models', this would be 'sites'.
            model_module = sys.modules[new_class.__module__]
            kwargs = {"app_label": model_module.__name__.split('.')[-2]}
        else:
            kwargs = {"app_label": meta.app_label}

        new_class._meta = Options(meta, **kwargs)
        new_class._meta.object_name = new_class.__name__
        new_class._meta.module_name = new_class.__name__.lower()
        new_class._meta.concrete_model = new_class

        if not hasattr(new_class.Meta, "verbose_name"):
            new_class._meta.verbose_name = new_class.__name__.lower()
        if not hasattr(new_class.Meta, "verbose_name_plural"):
            new_class._meta.verbose_name_plural = new_class._meta.verbose_name + "s"

        class Pk(Field):
            name = "pk"
            attname = "id"

        new_class._meta.pk = Pk()
        new_class._meta.id = Pk()
        new_class._meta.id.name = "id"
        #new_class._meta.fields.append(new_class._meta.pk)
        #new_class._meta.fields.append(new_class._meta.id)

        for attr, attr_value in attrs.items():
            if hasattr(attr_value, 'contribute_to_class'):
                attr_value.name = attr
                setattr(new_class, attr, None)
                attr_value.name = attr
                new_class._meta.fields.append(attr_value)

        return new_class


class MongoModel(object):
    __metaclass__ = MongoModelMeta

    _default_manager = MongoManager()

    class DoesNotExist(Exception):
        pass

    class Meta(object):
        pass

    fields = []
    objects = MongoManager()
    _meta = None

    def __init__(self, **kwargs):
        self._id = None
        self.__dict__.update(kwargs)

    @property
    def id(self):
        return str(self._id)

    @property
    def pk(self):
        return str(self._id)

    def delete(self):
        if self._id is None:
            return
        self.objects.filter(_id=self._id).delete()

    @property
    def _message(self):
        message = {}
        for field in self._meta.fields:
            message[field.name] = getattr(self, field.name, None)
        return message

    @classmethod
    def collection_name(cls):
        return getattr(cls.Meta, "db_table", cls.__class__.__name__.lower())

    @classmethod
    def collection(cls):
        return mongo_db()[cls.collection_name()]

    def save(self):
        # Set defaults and make everything the right object
        for field in self._meta.fields:
            value = getattr(self, field.name, None)
            if value is None:
                setattr(self, field.name, field.get_default())
            else:
                setattr(self, field.name, field.get_prep_value(value))

        if self._id is None:
            self._id = self.collection().insert(self._message)
        else:
            self.objects.filter(_id=self._id).update(**self._message)

    def serializable_value(self, field_name):
        """
        Returns the value of the field name for this instance. If the field is
        a foreign key, returns the id value, instead of the object. If there's
        no Field object with this name on the model, the model attribute's
        value is returned directly.

        Used to serialize a field's value (in the serializer, or form output,
        for example). Normally, you would just access the attribute directly
        and not use this method.
        """
        try:
            field = self._meta.get_field_by_name(field_name)[0]
        except FieldDoesNotExist:
            return getattr(self, field_name)
        return getattr(self, field.attname)