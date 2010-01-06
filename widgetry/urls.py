from django.conf.urls.defaults import *

from django.contrib.auth.models import User
from search import search

urlpatterns = patterns('',
    url('^autocomplete/(\w+)/$', autocomplete, name='autocomplete'),
)
