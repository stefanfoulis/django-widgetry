#-*- coding: utf-8 -*-
from django.db import models
from django.contrib import admin
from django.contrib.admin.options import TabularInline, StackedInline
from widgetry.fk_lookup.widgets import FkLookup
from widgetry_example.models import SimpleModel, SimpleInlineModel, AnotherSimpleInlineModel, Foo
from widgetry.tabs.admin import ModelAdminWithTabs


class SimpleModelAdmin(admin.ModelAdmin):
    pass
admin.site.register(SimpleModel, SimpleModelAdmin)


class SimpleModel2(SimpleModel):
    class Meta:
        proxy = True


class SimpleModelInlineAdmin(TabularInline):
    model = SimpleInlineModel


class AnotherSimpleModelInlineAdmin(StackedInline):
    model = AnotherSimpleInlineModel


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
    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Overrides the default widget for Foreignkey fields if they are
        specified in the related_search_fields class attribute.
        """
        if isinstance(db_field, models.ForeignKey):
            kwargs['widget'] = FkLookup(db_field.rel.to)
        return super(SimpleModelAdmin, self).formfield_for_dbfield(db_field, **kwargs)


admin.site.register(SimpleModel2, SimpleModelAdmin)

admin.site.register(Foo)