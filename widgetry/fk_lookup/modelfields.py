from django.contrib.contenttypes import generic
from django.db import models


class AutoLookupGenericForeignKey(generic.GenericForeignKey):
    def get_internal_type(self):
        return "PositiveIntegerField"

    def formfield(self, **kwargs):
        defaults = {'min_value': 0}
        defaults.update(kwargs)
        return super(PositiveIntegerField, self).formfield(**defaults)