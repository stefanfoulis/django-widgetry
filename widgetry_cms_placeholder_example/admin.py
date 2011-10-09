#-*- coding: utf-8 -*-
from django.contrib import admin
from widgetry_cms_placeholder_example.models import BlogPost
from widgetry.tabs.placeholderadmin import ModelAdminWithTabsAndCMSPlaceholder
from cms.admin.placeholderadmin import PlaceholderAdmin

class BlogPostNormal(BlogPost):
    class Meta:
        proxy = True


class BlogPostNormalAdmin(PlaceholderAdmin):
    pass
admin.site.register(BlogPostNormal, BlogPostNormalAdmin)


class BlogPostAdmin(ModelAdminWithTabsAndCMSPlaceholder):
    tabs = (
        ('First', {
            'fieldsets': [
                ('', {'fields': (('title', 'posted_at',), 'lead')}),
                ('', {'fields': ('is_interesting',)}),
            ],
        }),
        ('Second', {
            'fieldsets': [
                ('', {'fields': ('order', 'external_url',)}),
                ('', {'fields': ('body',), 'classes': ['plugin-holder', 'plugin-holder-nopage']}),
            ],
        }),
    )
admin.site.register(BlogPost, BlogPostAdmin)