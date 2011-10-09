#-*- coding: utf-8 -*-
from django.utils import simplejson
from django.forms import widgets
from django.core.urlresolvers import reverse
from django.utils.text import truncate_words

from django.contrib.contenttypes.models import ContentType
from widgetry.views import search
from django.template import loader, Template, Context
from django.conf import settings
from widgetry.config import JQUERY_URLS, STATICMEDIA_PREFIX

class FkLookup(widgets.Widget):
    """
    A Widget for displaying ForeignKey with a autocomplete input instead of
    a ``select`` box.
    Searchable Models must be registered in the search view:
        widgetry.views.search.register()
    """
    def __init__(self, destination_model, attrs=None, show_edit=False):        
        if type(destination_model) == ContentType:
            destination_model = destination_model.model_class()
        
        if destination_model is None:
            self.content_type = None
            self.destination_model = None
            self.wrapper = None
        elif isinstance(destination_model, str):
            # convert to model if it is a string
            app_label, model_name = destination_model.split('.')
            self.content_type = ContentType.objects.get(app_label=app_label, model=model_name)
            self.destination_model = self.content_type.model_class()
            self.wrapper = search.get_wrapper(self.destination_model)
        else:
            self.destination_model = destination_model
            self.content_type = ContentType.objects.get_for_model(destination_model)
            self.wrapper = search.get_wrapper(self.destination_model)
            #app_label = self.content_type.app_label
            #model_name = self.content_type.model
        self.content_type_info = {}
        for model_class, wrapper in search.wrappers.items():
            #new_q = Q(app_label = model_class._meta.app_name, )
            content_type = ContentType.objects.get_for_model(model_class)
            # TODO: check for add permissions. hard to do without the request :-(
            self.content_type_info[content_type.id] = {'add_url': reverse('admin:%s_%s_add' % (content_type.app_label, content_type.model))}
        self.show_edit = show_edit
        super(FkLookup, self).__init__(attrs)
    
    def label_for_value(self, value):
        """
        Given a value (the id of the ForeignKey field) evaluate the correct representation
        text for inside the input field.
        """
        #print "    the destination model to label %s (%s) with %s" % (self.destination_model, type(self.destination_model), value)
        if not self.destination_model or not self.wrapper:
            return ""
        try:
            #print "   GET OBJ of type %s (%s)" % ( self.destination_model, type(self.destination_model) )
            obj = self.destination_model.objects.get(pk=value)
        except Exception, e:
            #print "EVIL EXCEPTION %s" % e
            return "object missing!"
        #print "   MAKE WRAP"
        wrapped_obj = self.wrapper(obj)
        text = wrapped_obj.title()
        return truncate_words(text, 14)
        
    
    def render(self, name, value, attrs=None, extra_context={}):
        #print "BEGIN RENDER %s: %s" % (name, value)
        template = loader.select_template(['widgetry/fk_lookup/widget.html'])
        search_url =  reverse('widgetry-search')
        admin_media_prefix = settings.ADMIN_MEDIA_PREFIX
        # the label
        if value:
            label = self.label_for_value(value)
        else:
            label = u''
        # allow the object browsing popup 
        if (self.show_edit):
            enable_edit = u'true'
        else:
            enable_edit = u'false'
        if self.content_type:
            content_type_id = self.content_type.pk
        if value is None:
            value = ''
        else:
            value = str(value)
        content_type_info = self.content_type_info
        content_type_info_json = simplejson.dumps(content_type_info)
        context = Context(locals())
        context.update(extra_context)
        r = template.render(context)
        return r        
        
        
    class Media:
        css = {
            'all': (STATICMEDIA_PREFIX + 'css/jquery.fkautocomplete.css',)
        }
        js = (
            JQUERY_URLS['admincompat'],
            JQUERY_URLS['core'],
            JQUERY_URLS['plugins.fkautocomplete'],
            JQUERY_URLS['plugins.autocomplete'],
        )

class GenericFkLookup(FkLookup):
    def __init__(self, content_type_field_name, initial_destination_model=None, attrs=None, show_edit=False):
        self.content_type_field_name = content_type_field_name
        super(GenericFkLookup, self).__init__(initial_destination_model, attrs, show_edit)
    def render(self, name, value, attrs=None, extra_context={}):
        extra_context['is_generic_lookup'] = True
        extra_context['content_type_field_name'] = self.content_type_field_name
        return super(GenericFkLookup, self).render(name, value, attrs, extra_context)