#-*- coding: utf-8 -*-

from django.conf import settings

STATICMEDIA_PREFIX = getattr(settings, 'WIDGETRY_STATICMEDIA_PREFIX', None)
if not STATICMEDIA_PREFIX:
    STATICMEDIA_PREFIX = (getattr(settings,'STATIC_URL', None) or settings.MEDIA_URL) + 'widgetry/'