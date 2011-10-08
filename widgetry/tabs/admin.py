from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.options import csrf_protect_m
from django.contrib.admin.util import unquote
from django.core.exceptions import PermissionDenied
from django.db import transaction, models
from django.forms.formsets import all_valid
from django.http import Http404
from django.utils.encoding import force_unicode
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect

try:
    set
except NameError:
    from sets import Set as set     # Python 2.3 fallback

"""

tabs = (
    ('Tab name', {'classes': ('specialCssClass',),
                  'fieldsets': (
                      ('Fieldset Name', {
                                      'fields': ('user', 'name', 'title',),
                                      'classes': ('collapse',)
                                  }),
                      ('Fieldset Name 2', {
                                      'fields': ('user', 'name', 'title',),
                                      'classes': ('collapse',)
                                  }),
                        ),
                 'inlines': (InlineThingy, OtherInlineThingy,)
                 }),
                    
    ('Other Tab Name', {'classes'
)

"""



class Tabset(object):
    '''
    Like AdminForm in a normal setup, but provides Tab instances instead of formsets.
   
    '''
    has_tabs = True
    def __init__(self, form, tabs, prepopulated_fields, readonly_fields, model_admin):
        self.form = form
        self.tabs = []
        for name, options in tabs:
            tab_fieldsets = options.pop('fieldsets', ())
            tab_inlines = options.pop('inlines', ())
            self.tabs.append(Tab(self.form, name=name, 
                                 fieldsets=tab_fieldsets,
                                 inlines=tab_inlines,
                                 readonly_fields=readonly_fields,
                                 model_admin=model_admin,
                                 **options))
        
        self.prepopulated_fields = [{
            'field': form[field_name],
            'dependencies': [form[f] for f in dependencies]
        } for field_name, dependencies in prepopulated_fields.items()]
        self.readonly_fields = readonly_fields
        self.model_admin = model_admin

    def __iter__(self):
        for tab in self.tabs:
            yield tab
    
    def first_field(self):
        return None
    
    def _media(self):
        media = self.form.media
        for tab in self:
            media = media + tab.media
        return media
    media = property(_media)
    
    def get_tab_that_has_inline(self, inline_class_name):
        for tab in self:
            if inline_class_name in tab.inline_names:
                return tab
        return None
        
class Tab(helpers.AdminForm):
    '''
    A subclass of AdminForm. It adds a name and a description and additionally
    also contains the InlineFormsets
    '''
    def __init__(self, form, name=None, fieldsets=(), inlines=(), 
                 prepopulated_fields={}, readonly_fields=None, model_admin=None,
                 classes=(), description=None):
        self.form = form
        self.name = name
        # TODO: fieldsets should also be able to contain InlineFormsets
        self.fieldsets = helpers.normalize_fieldsets(fieldsets)
        self.prepopulated_fields = [{
            'field': form[field_name],
            'dependencies': [form[f] for f in dependencies]
        } for field_name, dependencies in prepopulated_fields.items()]
        self.model_admin = model_admin
        self.readonly_fields = readonly_fields
        self.inline_names = inlines
        self.inlines = [] # they are added in change_view()
        
        self.classes = u' '.join(classes)
        self.description = description
    
    def has_errors(self):
        if not hasattr(self,'_has_errors'):
            self._has_errors = False
            for inline in self.inlines:
                if inline.formset.is_bound and not inline.formset.is_valid():
                    self._has_errors = True
                    break
            for fieldset in self:
                for fieldline in fieldset:
                    for field in fieldline.fields:
                        if field in self.form.fields.keys() and self.form[field].errors:
                            self._has_errors = True
                            break
        return self._has_errors
            
    def _media(self):
        # formset media is already handled in the view
        return super(Tab, self)._media()
    media = property(_media)
            
                      
        

class ModelAdminWithTabs(admin.ModelAdmin):
    tabs = []

    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        """
        Like the original add_view from ModelAdmin. Alterations are marked
        with 
        # ----start
        # ----end
        """
        
        "The 'add' admin view for this model."
        model = self.model
        opts = model._meta

        if not self.has_add_permission(request):
            raise PermissionDenied

        ModelForm = self.get_form(request)
        formsets = []
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES)
            if form.is_valid():
                new_object = self.save_form(request, form, change=False)
                form_validated = True
            else:
                form_validated = False
                new_object = self.model()
            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request), self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(data=request.POST, files=request.FILES,
                                  instance=new_object,
                                  save_as_new=request.POST.has_key("_saveasnew"),
                                  prefix=prefix, queryset=inline.queryset(request))
                formsets.append(formset)
            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, change=False)
                form.save_m2m()
                for formset in formsets:
                    self.save_formset(request, form, formset, change=False)

                self.log_addition(request, new_object)
                return self.response_add(request, new_object)
        else:
            # Prepare the dict of initial data from the request.
            # We have to special-case M2Ms as a list of comma-separated PKs.
            initial = dict(request.GET.items())
            for k in initial:
                try:
                    f = opts.get_field(k)
                except models.FieldDoesNotExist:
                    continue
                if isinstance(f, models.ManyToManyField):
                    initial[k] = initial[k].split(",")
            form = ModelForm(initial=initial)
            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request),
                                       self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(instance=self.model(), prefix=prefix,
                                  queryset=inline.queryset(request))
                formsets.append(formset)
        
        # --start--
        adminForm = Tabset(form, self.tabs,
            self.prepopulated_fields, self.get_readonly_fields(request),
            model_admin=self)
        # --original--
#         adminForm = helpers.AdminForm(form, list(self.get_fieldsets(request)), self.prepopulated_fields)
        # --end--
        media = self.media + adminForm.media
        
        # --start-- (identical to the one in change_view, except for not passing obj in get_fieldsets)
        inline_admin_formsets = []
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request))
            readonly = list(inline.get_readonly_fields(request))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                fieldsets, readonly, model_admin=self)
            
            tab = adminForm.get_tab_that_has_inline(inline.__class__.__name__)
            if not tab==None:
                tab.inlines.append(inline_admin_formset)
            else:
                inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media
        # --original--
#        inline_admin_formsets = []
#        for inline, formset in zip(self.inline_instances, formsets):
#            fieldsets = list(inline.get_fieldsets(request))
#            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset, fieldsets)
#            inline_admin_formsets.append(inline_admin_formset)
#            media = media + inline_admin_formset.media
        # --end--
        
        context = {
            'title': _('Add %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'is_popup': request.REQUEST.has_key('_popup'),
            'show_delete': False,
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, form_url=form_url, add=True)

    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, extra_context=None):
        """
        Like the original change_view from ModelAdmin. Alterations are marked
        with 
        # ----start
        # ----end
        """
        if not self.tabs:
            return super(ModelAdminWithTabs, self).change_view(request, 
                                object_id, extra_context=extra_context)
        
        "The 'change' admin view for this model."
        model = self.model
        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        if request.method == 'POST' and request.POST.has_key("_saveasnew"):
            return self.add_view(request, form_url='../add/')

        ModelForm = self.get_form(request, obj)
        formsets = []
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=True)
            else:
                form_validated = False
                new_object = obj
            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request, new_object),
                                       self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(request.POST, request.FILES,
                                  instance=new_object, prefix=prefix,
                                  queryset=inline.queryset(request))

                formsets.append(formset)

            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, change=True)
                form.save_m2m()
                for formset in formsets:
                    self.save_formset(request, form, formset, change=True)

                change_message = self.construct_change_message(request, form, formsets)
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)

        else:
            form = ModelForm(instance=obj)
            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request, obj), self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(instance=obj, prefix=prefix,
                                  queryset=inline.queryset(request))
                formsets.append(formset)

        adminForm = Tabset(form, self.tabs,
            self.prepopulated_fields, self.get_readonly_fields(request, obj), model_admin=self)
        # --original--
#         adminForm = helpers.AdminForm(form, self.get_fieldsets(request, obj),
#            self.prepopulated_fields, self.get_readonly_fields(request, obj),
#            model_admin=self)
        # --end--
        # --old original--
#         adminForm = helpers.AdminForm(form, self.get_fieldsets(request, obj), self.prepopulated_fields)
        # --end--
        media = self.media + adminForm.media
        
        # --start--
        inline_admin_formsets = []
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            readonly = list(inline.get_readonly_fields(request, obj))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                fieldsets, readonly, model_admin=self)
            
            tab = adminForm.get_tab_that_has_inline(inline.__class__.__name__)
            if not tab==None:
                tab.inlines.append(inline_admin_formset)
            else:
                inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media
        # --original--
#        inline_admin_formsets = []
#        for inline, formset in zip(self.inline_instances, formsets):
#            fieldsets = list(inline.get_fieldsets(request, obj))
#            readonly = list(inline.get_readonly_fields(request, obj))
#            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
#                fieldsets, readonly, model_admin=self)
#            inline_admin_formsets.append(inline_admin_formset)
#            media = media + inline_admin_formset.media
        # --old original--
#        inline_admin_formsets = []
#        for inline, formset in zip(self.inline_instances, formsets):
#            fieldsets = list(inline.get_fieldsets(request, obj))
#            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset, fieldsets)
#            inline_admin_formsets.append(inline_admin_formset)
#            
#            media = media + inline_admin_formset.media
        # --end--   
        
        context = {
            'title': _('Change %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': request.REQUEST.has_key('_popup'),
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, change=True, obj=obj)
    
    @property
    def change_form_template(self):
        opts = self.model._meta
        app_label = opts.app_label
        return [
            "admin/%s/%s/tabbed_change_form.html" % (app_label, opts.object_name.lower()),
            "admin/%s/tabbed_change_form.html" % app_label,
            "admin/tabbed_change_form.html",
        ]
    
    def _declared_fieldsets(self):
        if self.tabs:
            fieldsets = []
            for name, tab in self.tabs:
                fieldsets += list(tab.get('fieldsets', []))
            return fieldsets
        elif self.fieldsets:
            return self.fieldsets
        elif self.fields:
            return [(None, {'fields': self.fields})]
        return None
    declared_fieldsets = property(_declared_fieldsets)
    
    class Media:
        css = {
            "all": ("widgetry/tabs/css/jquery-ui-1.8.10.custom.css",)
        }
        js = (
              "widgetry/tabs/js/jquery-1.4.4.min.js",
              "widgetry/tabs/js/jquery-ui-1.8.10.custom.min.js",
        )
