from django.contrib import admin
from django.contrib.admin import helpers
from django.core.exceptions import ImproperlyConfigured
from widgetry.config import JQUERY_URLS, STATICMEDIA_PREFIX

try:
    set
except NameError:
    from sets import Set as set     # Python 2.3 fallback


class Tabset(object):
    '''
    Like AdminForm in a normal setup, but provides Tab instances instead of formsets.
    '''
    has_tabs = True
    def __init__(self, form, tabs, prepopulated_fields, readonly_fields, model_admin):
        self.form = form
        self.tabs = []
        for name, options in tabs:
            self.tabs.append(Tab(self.form, name=name,
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
    
    def get_tab_for_inline(self, inline):
        for tab in self:
            if inline in tab.inlines:
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
        self.inlines = inlines
        self.inline_admin_formsets = []  # will be populated in ModelAdminWithTabs.render_change_form
        
        self.classes = u' '.join(classes)
        self.description = description
    
    def has_errors(self):
        if not hasattr(self,'_has_errors'):
            self._has_errors = False
            for inline_admin_formset in self.inline_admin_formsets:
                if inline_admin_formset.formset.is_bound and not inline_admin_formset.formset.is_valid():
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
    """
    ModelAdmin that supports `tabs` instead of `fieldsets` for pretty form layout.
    """
    tabs = []

    def __init__(self, model, admin_site):
        if not self.tabs:
            raise ImproperlyConfigured('%s.tabs must be defined' % self.__class__.__name__)
        if self.inlines:
            raise ImproperlyConfigured('inlines must be defined inside %s.tabs' % self.__class__.__name__)
        super(ModelAdminWithTabs, self).__init__(model, admin_site)

        # populate self.inline_instances with all inlines defined inside tabs.

        # We provide two different ways of doing this here.
        # The original way populates them in Django < 1.4.
        # In Django 1.4, a different method is required. 
        #
        # Since
        # https://github.com/django/django/commit/b1b1da1eac93297503c04b8394fb98e38f552f5f
        # django.contrib.admin.options.ModelAdmin.__init__() no longer takes responsibility 
        # for inlines.
        #
        # Instead, a get_inline_instances() method takes care of it.
        
        # the original, for backwards compatibility
        self.inline_instances = []        
        for inline_class in self._extract_inlines_from_tabs():
            inline_instance = inline_class(self.model, self.admin_site)
            self.inline_instances.append(inline_instance)

        # the way for Django 1.4
        self.inlines = self._extract_inlines_from_tabs()

    def _extract_inlines_from_tabs(self):
        inlines = []
        for name, opts in self.tabs:
            inlines += opts.get('inlines', [])
        return inlines

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """
        injects the variables needed for tab rendering and calls the regular `render_change_form`.

        Notes:
          * there is no need to calculate Media stuff here, that has already happened in `change_view` and `add_view`.
        """
        form = context['adminform'].form
        inline_admin_formsets = context['inline_admin_formsets']

        adminForm = Tabset(
            form, self.tabs, self.prepopulated_fields, self.get_readonly_fields(request), model_admin=self)

        for inline_admin_formset in inline_admin_formsets:
            tab = adminForm.get_tab_for_inline(inline_admin_formset.opts.__class__)
            if not tab==None:
                tab.inline_admin_formsets.append(inline_admin_formset)
        context.update({
            'adminform': adminForm,
            'inline_admin_formsets': []
        })
        return super(ModelAdminWithTabs, self).render_change_form(
            request, context, add=add, change=change, form_url=form_url, obj=obj)

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
        fieldsets = []
        for name, tab in self.tabs:
            fieldsets += list(tab.get('fieldsets', []))
        return fieldsets
    declared_fieldsets = property(_declared_fieldsets)

    class Media:
        css = {
            "all": (STATICMEDIA_PREFIX + "css/smoothness/jquery-ui-1.7.3.custom.css",)
        }
        js = (
              JQUERY_URLS['admincompat'],
              JQUERY_URLS['core'],
              JQUERY_URLS['ui.core'],
              JQUERY_URLS['ui.tabs'],
        )
