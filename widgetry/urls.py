from django.conf.urls.defaults import *
from search import search

urlpatterns = patterns('',
    url('^autocomplete/(\w+)/$', autocomplete, name='autocomplete'),
)
