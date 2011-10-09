#-*- coding: utf-8 -*-

from django.conf import settings

STATICMEDIA_PREFIX = getattr(settings, 'WIDGETRY_STATICMEDIA_PREFIX', None)
if not STATICMEDIA_PREFIX:
    STATICMEDIA_PREFIX = (getattr(settings,'STATIC_URL', None) or settings.MEDIA_URL) + 'widgetry/'

JQUERY_URLS = getattr(settings, 'WIDGETRY_JQUERY_URLS', getattr(settings, 'JQUERY_URLS', None))
if not JQUERY_URLS:
    if 'cms' in settings.INSTALLED_APPS:
        from cms.utils import cms_static_url
        JQUERY_URLS = {
            'core': cms_static_url('js/libs/jquery.query.js'),
            'admincompat': cms_static_url('js/plugins/admincompat.js'),
            'ui.core': cms_static_url('js/libs/jquery.ui.core.js'),
            'ui.tabs': STATICMEDIA_PREFIX + 'js/ui/ui.tabs.js',
        }
    else:
        JQUERY_URLS = {
            'core': STATICMEDIA_PREFIX + 'js/jquery-1.3.2.js',
            'admincompat': STATICMEDIA_PREFIX + 'js/admincompat.js',
            'ui.core': STATICMEDIA_PREFIX + 'js/ui/ui.core.js',
            'ui.tabs': STATICMEDIA_PREFIX + 'js/ui/ui.tabs.js',
        }