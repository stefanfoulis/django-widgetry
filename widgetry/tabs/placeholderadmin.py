#-*- coding: utf-8 -*-
from cms.admin.placeholderadmin import PlaceholderAdmin
from widgetry.tabs.admin import ModelAdminWithTabs

class ModelAdminWithTabsAndCMSPlaceholder(ModelAdminWithTabs, PlaceholderAdmin):
    def _media(self):
        return super(ModelAdminWithTabs, self).media + super(PlaceholderAdmin, self).media
    media = property(_media)
