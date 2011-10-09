#-*- coding: utf-8 -*-
from django.db import models
from django.contrib import admin
from django.contrib.admin.options import TabularInline
from widgetry.fk_lookup.widgets import FkLookup
from widgetry_example.models import SimpleModel, SimpleInlineModel, AnotherSimpleInlineModel, Foo
from widgetry.tabs.admin import ModelAdminWithTabs


class SimpleModelDefault(SimpleModel):
    class Meta:
        proxy = True
admin.site.register(SimpleModelDefault)


class SimpleModelInlineAdmin(TabularInline):
    model = SimpleInlineModel
    extra = 0


class AnotherSimpleModelInlineAdmin(TabularInline):
    model = AnotherSimpleInlineModel
    extra = 0


class SimpleModelAdmin(ModelAdminWithTabs):
    tabs = (
        ('First', {
            'fieldsets': [
                ('', {'fields': (('name', 'order',), ('bol1', 'foo'),)}),
                ('', {'fields': ('description',)}),
            ],
            'inlines': [SimpleModelInlineAdmin],
        }),
        ('Second', {
            'fieldsets': [
                ('', {'fields': ('char1', 'url', 'char2', 'bol2')}),
            ],
            'inlines': [AnotherSimpleModelInlineAdmin],
        }),
        ('Third', {
            'fieldsets': [
                ('', {'fields': ('char3', ('char4', 'bol3',))}),
            ]
        }),
    )
admin.site.register(SimpleModel, SimpleModelAdmin)


class SimpleModelWithFKLookup(SimpleModel):
    class Meta:
        proxy = True

class TabsWithFkLookupModelAdmin(SimpleModelAdmin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Overrides the default widget for Foreignkey fields if they are
        specified in the related_search_fields class attribute.
        """
        if isinstance(db_field, models.ForeignKey):
            kwargs['widget'] = FkLookup(db_field.rel.to)
        return super(SimpleModelAdmin, self).formfield_for_dbfield(db_field, **kwargs)
admin.site.register(SimpleModelWithFKLookup, TabsWithFkLookupModelAdmin)

admin.site.register(Foo)