#-*- coding: utf-8 -*-
from cms.admin.placeholderadmin import PlaceholderAdmin
from copy import deepcopy
from widgetry.tabs.admin import ModelAdminWithTabs

class ModelAdminWithTabsAndCMSPlaceholder(ModelAdminWithTabs, PlaceholderAdmin):
    def get_fieldsets(self, request, obj=None):
        """
        Get fieldsets to enforce correct fieldsetting of placeholder fields
        This is a copy of the get_fieldsets() from PlaceholderAdmin with the
        added forloop for the tabs. (copied from django-cms 
        """
        form = self.get_form(request, obj)
        placeholder_fields = self._get_placeholder_fields(form)
        if self.declared_fieldsets:
            # check those declared fieldsets
            tabsets = list(deepcopy(self.declared_fieldsets))
            for fieldsets in tabsets:
                for label, fieldset in fieldsets:
                    fields = list(fieldset['fields'])
                    for field in fieldset['fields']:
                        if field in placeholder_fields:
                            if (len(fieldset['fields']) == 1 and
                                'classes' in fieldset and
                                'plugin-holder' in fieldset['classes'] and
                                'plugin-holder-nopage' in fieldset['classes']):
                                placeholder_fields.remove(field)
                            else:
                                fields.remove(field)
                    if fields:
                        fieldset['fields'] = fields
                    else:
                        # no fields in the fieldset anymore, delete the fieldset
                        fieldsets.remove((label, fieldset))
            for placeholder in placeholder_fields:
                # it does not matter where the widget is added: it's all js
                tabsets[0].append((self.get_label_for_placeholder(placeholder), {
                        'fields': (placeholder,),
                        'classes': ('plugin-holder', 'plugin-holder-nopage',),
                    },))
            return fieldsets
        fieldsets = []
        fieldsets.append((None, {'fields': [f for f in form.base_fields.keys() if not f in placeholder_fields]}))
        for placeholder in placeholder_fields:
            fieldsets.append((self.get_label_for_placeholder(placeholder), {
                'fields': (placeholder,),
                'classes': ('plugin-holder', 'plugin-holder-nopage',),
            }))
        readonly_fields = self.get_readonly_fields(request, obj)
        if readonly_fields:
            fieldsets.append((None, {'fields': list(readonly_fields)}))
        return fieldsets