#-*- coding: utf-8 -*-

from django.conf import settings

STATICMEDIA_PREFIX = getattr(settings, 'WIDGETRY_STATICMEDIA_PREFIX', None)
if not STATICMEDIA_PREFIX:
    STATICMEDIA_PREFIX = (getattr(settings,'STATIC_URL', None) or settings.MEDIA_URL) + 'widgetry/'

JQUERY_URLS = getattr(settings, 'WIDGETRY_JQUERY_URLS', getattr(settings, 'JQUERY_URLS', None))
if not JQUERY_URLS:
    JQUERY_URLS = {
            'core': STATICMEDIA_PREFIX + 'js/jquery-1.3.2.js',
            'admincompat': STATICMEDIA_PREFIX + 'js/admincompat.js',
            'ui.core': STATICMEDIA_PREFIX + 'js/ui/ui.core.js',
            'ui.tabs': STATICMEDIA_PREFIX + 'js/ui/ui.tabs.js',
            'plugins.fkautocomplete': STATICMEDIA_PREFIX + 'js/plugins/jquery.fkautocomplete.js',
            'plugins.autocomplete': STATICMEDIA_PREFIX + 'js/plugins/jquery.autocomplete.js',
        }
    if 'cms' in settings.INSTALLED_APPS:
        # use whatever js is provided by the cms, to avoid loading the same js twice.
        from cms.utils import cms_static_url
        JQUERY_URLS['core'] = cms_static_url('js/libs/jquery.query.js')
        JQUERY_URLS['admincompat'] = cms_static_url('js/plugins/admincompat.js')
        JQUERY_URLS['ui.core'] = cms_static_url('js/libs/jquery.ui.core.js')
