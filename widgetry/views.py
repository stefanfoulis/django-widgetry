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
from pprint import pprint

class SearchItemWrapper(object):
    search_fields = []
    def __init__(self, obj):
        self.obj = obj
    def identifier(self):
        return getattr(self.obj, 'pk', None)
    def title(self):
        return getattr(self.obj, 'title', smart_unicode(self.obj))
    def description(self):
        return getattr(self.obj, 'description', '')
    def thumbnail_url(self):
        return '/media/images/document_icon_pdf.gif'

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
        query_string = request.REQUEST.get(query_param, '')
        limit = int(request.REQUEST.get('limit', '50'))
        timestamp = request.REQUEST.get('timestamp', '')
        print u"QUERY: %s (limit: %s timestamp: %s)" % (query_string, limit, timestamp)
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
        print u"CONTENT TYPE: %s" % content_type
        Model = content_type.model_class()
        Wrapper = self.wrappers[Model]
        qs = Model._default_manager.all()
        for bit in query_string.split():
            or_queries = []
            for field_name in Wrapper.search_fields:
                field_qs = {}
                if not '__' in field_name:
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
            qs = qs.filter(reduce(operator.or_, or_queries))
            
        qs = qs#[:limit]
        print "QUERY:"
        print qs
        data = []
        structured_data = []
        for item in qs:
            print u'handling: %s' % item
            wrapped_item = Wrapper(item)
            data.append(u'%s|%s|%s|%s' % (
                        wrapped_item.identifier(), 
                        wrapped_item.title(), 
                        wrapped_item.description(), 
                        wrapped_item.thumbnail_url()
                        )
                    )
            structured_data.append({
                        'identifier': wrapped_item.identifier(),
                        'title':wrapped_item.title(),
                        'description':wrapped_item.description(),
                        'thumbnail_url': wrapped_item.thumbnail_url(),
                    })
        data_str = '\n'.join(data)
        #print data
        pprint(structured_data)
        if len(data)>0:
            #return HttpResponse(data_str)
            return HttpResponse(simplejson.dumps(structured_data),mimetype='application/json')
        else:
            return self.not_found(request)
        
    def register(self, klasses, wrapper):
        if not isinstance(klasses, list):
            klasses = [klasses]
        for klass in klasses:
            self.wrappers[klass] = wrapper
    
    def get_wrapper(self, model_or_string):
        print "get wrapper %s" % model_or_string
        if isinstance(model_or_string, str):
            app_label, model_name = model_or_string.split('.')
            content_type = ContentType.objects.get(app_label=app_label, model=model_name)
            model = content_type.model_class()
        else:
            model = model_or_string
        print "return wrapper for %s" % model
        print self.wrappers
        if model in self.wrappers:
            wrapper = self.wrappers[model]
        else:
            wrapper = SearchItemWrapper
        print "    wrapper: %s" % wrapper
        return wrapper
        
    def not_found(self, request):
        #return HttpResponse(status=404)
        # autocomplete fucks up if we return a 404 (it gets handled like
        # a failure)
        return HttpResponse(simplejson.dumps([]),mimetype='application/json')

    def forbidden(self, request):
        return HttpResponse(status=403)


search = Search()
        