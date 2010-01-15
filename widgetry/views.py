from django.http import HttpResponse
from django.utils import simplejson
from django.db.models import get_model
from django.db.models import Q
from django.db.models.query import QuerySet
from django.db.models import ForeignKey
from django.utils.safestring import mark_safe 
from django.utils.encoding import smart_str, smart_unicode
import operator
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentTypeManager, ContentType
from django.conf import settings

from widgetry.utils import traverse_object
from widgetry import signals

def call_if_callable(fnc):
    if callable(fnc):
        return fnc()
    else:
        return fnc

class SearchItemWrapper(object):
    THUMBNAIL_SIZE=int( getattr(settings,'WIDGETRY_FKLOOKUP_THUMBNAIL_SIZE',48) )
    def __init__(self, obj):
        self.obj = obj
    def identifier(self):
        return call_if_callable( getattr( self.obj, 'pk', None ) )
    def title(self):
        return call_if_callable( getattr( self.obj, 'title', smart_unicode(self.obj) ) )
    def description(self):
        return call_if_callable( getattr( self.obj, 'description', '' ) )
    def thumbnail_full_file(self):
        return None
    def thumbnail_url(self):
        file = self.thumbnail_full_file()
        if file:
            # resize the image
            return None
        else:
            return None#'/media/images/document_icon_pdf.gif'

ATTRIBUTES = [
    'identifier',
    'title',
    'description',
    'thumbnail_url',
]

class WrapperFactory(object):
    '''
    Can build custom classes based on a superclass and a list of attributes.
    The attribute list is parsed before it assigns the methods to the new class.
    my_factory = WrapperFactory(SomeSuperclass, ['foo','bar'])
    
    MyWrapperClass = my_factory.build('DynamicClassName', ...)
    '''
    
    def __init__(self, product_superclass, product_attributes):
        self.product_superclass = product_superclass
        self.product_attributes = product_attributes
    def build(self, model_name, search_fields, custom_attributes):
        methods = {}
        for name, value in custom_attributes.items():
            if not name in self.product_attributes:
                # the attribute in kwargs is not listed in the allowed attributes
                raise Exception('No such attribute allowed "%s"' % name)
            if callable(value):
                # use the method as is, just add wrap it in to add self
                # and pass in the obj
                method = lambda slf, v=value: v(obj=slf.obj)
            elif isinstance(value, basestring):
                value = u"%s" % value
                if len(value)>2 and value[0]==value[-1] and value[0] in ["'",'"'] and value[-1] in ["'",'"']:
                    # it is a static string (a string including ' or " )
                    value = u"%s" % value[1:-1]
                    method = lambda slf, v=value: v
                else:
                    # the value is the name of a field on obj (or other related objects)
                    method = lambda slf, v=value: smart_unicode(traverse_object(slf.obj, v))
            else:
                raise Exception('%s must be either a string (dot notation), a string with quotes for static strings or a callable that takes obj as its first argument' % name)
            if method: methods[name] = method
        methods['search_fields'] = search_fields
        WrapperClass = type(model_name + self.product_superclass.__name__, (self.product_superclass,), methods)
        return WrapperClass

wrapper_factory = WrapperFactory(SearchItemWrapper, ATTRIBUTES)

class Search(object):
    """
    Object search view and object type registry
    """
    def __init__(self):
        self.wrappers = dict()
        self.settings = dict()
    
    def __call__(self, request, query_param='q'):
        """
        Searches in the fields of the given related model and returns the 
        result as a simple string to be used by the jQuery Autocomplete plugin
        """
        signals.search_request.send(sender=self, request=request)
        query_string = request.REQUEST.get(query_param, '')
        limit = int(request.REQUEST.get('limit', '50'))
        timestamp = request.REQUEST.get('timestamp', '')
        #print u"QUERY: %s (limit: %s timestamp: %s)" % (query_string, limit, timestamp)
        
        # find the model to search on
        content_type_id = request.REQUEST.get('content_type_id', None) # an integer
        content_type_str = request.REQUEST.get('content_type', None) # a string 'myapp.mymodel'
        if content_type_id:
            content_type = ContentType.objects.get_for_id(content_type_id)
        elif content_type_str:
            app_label, model_name = content_type_str.split('.')
            content_type = ContentType.objects.get(app_label=app_label, model=model_name)
        else:
            return self.not_found(request)
        #print u"CONTENT TYPE: %s" % content_type
        Model = content_type.model_class()
        #print Model
        Wrapper = self.get_wrapper(Model)
        #print Wrapper
        qs = Model._default_manager.all()
        #print qs
        for bit in query_string.split():
            or_queries = []
            #print bit
            for field_name in Wrapper.search_fields:
                #print u"   %s" % field_name
                field_qs = {}
                if not field_name.endswith('__icontains'):
                    field_qs['%s__icontains' % field_name] = smart_str(bit)
                else:
                    field_qs[field_name] = smart_str(bit)
                or_queries.append(Q(**field_qs))
                #print field_qs
            #other_qs = QuerySet(Model)
            #other_qs.dup_select_related(qs)
            #other_qs = other_qs.filter(reduce(operator.or_, or_queries))
            #qs = qs & other_qs
            # other approach
            #print or_queries
            qs = qs.filter(reduce(operator.or_, or_queries))
            
        qs = qs[:limit]
        #print "QS:", qs
        structured_data = []
        added_ids = []
        for item in qs:
            #print u'handling: %s' % item
            wrapped_item = Wrapper(item)
            try:
                if not wrapped_item.identifier() in added_ids:
                    structured_data.append({
                                'identifier': wrapped_item.identifier(),
                                'title':wrapped_item.title(),
                                'description':wrapped_item.description(),
                                'thumbnail_url': wrapped_item.thumbnail_url(),
                            })
                    added_ids.append(wrapped_item.identifier())
            except Exception, e:
                print u"Something went wrong while handling a search wrapper: %s" % e
        ##print data
        #pprint(structured_data)
        if len(structured_data)>0:
            return HttpResponse(simplejson.dumps(structured_data),mimetype='application/json')
        else:
            return self.not_found(request)
    
    def register(self, klasses, search_fields=None, **kwargs):
        if not isinstance(klasses, list):
            klasses = [klasses]
        if not search_fields:
            raise Exception("widgetry search registration: search_fields are missing")
        for klass in klasses:
            wrapper = wrapper_factory.build('%sAutoGenerated' % klass.__name__, search_fields, kwargs)
            self.register_wrapper(klass, wrapper)
            
    def register_wrapper(self, klasses, wrapper):
        if not isinstance(klasses, list):
            klasses = [klasses]
        for klass in klasses:
            #print "NOW REGISTERING %s (%s)" % (klass, type(klass) )
            signals.wrapper_registration.send(sender=self, klass=klass, wrapper=wrapper)
            self.wrappers[klass] = wrapper
    
    def get_wrapper(self, model_or_string):
        #print "get wrapper %s" % model_or_string
        if isinstance(model_or_string, str):
            app_label, model_name = model_or_string.split('.')
            content_type = ContentType.objects.get(app_label=app_label, model=model_name)
            model = content_type.model_class()
        else:
            model = model_or_string
        signals.get_wrapper.send(sender=self, model=model)
        #print "return wrapper for %s" % model
        #print self.wrappers
        if model in self.wrappers:
            wrapper = self.wrappers[model]
        else:
            wrapper = SearchItemWrapper
        #print "    wrapper: %s" % wrapper
        return wrapper
    
    def is_registered(self, model):
        return model in self.wrappers
        
    def not_found(self, request):
        #return HttpResponse(status=404)
        # autocomplete fucks up if we return a 404 (it gets handled like
        # a failure)
        return HttpResponse(simplejson.dumps([]),mimetype='application/json')

    def forbidden(self, request):
        return HttpResponse(status=403)
    
    def content_type_choices(self):
        choices = []
        #q_obj = None
        for model_class, wrapper in self.wrappers.items():
            #new_q = Q(app_label = model_class._meta.app_name, )
            content_type = ContentType.objects.get_for_model(model_class)
            choices.append((content_type.pk, u"%s: %s" % (content_type.app_label.replace('_', ' '), content_type.name)))
        return choices #((1,'hello'),(2,'there'),) 


search = Search()
