#-*- coding: utf-8 -*-
import datetime
from django.db import models
from cms.models.fields import PlaceholderField

class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    lead = models.TextField(blank=True, default='')
    order = models.IntegerField(default=0)
    posted_at = models.DateTimeField(default=datetime.datetime.now)
    is_interesting = models.BooleanField(default=False)
    external_url = models.URLField(blank=True, default='', verify_exists=False)
    body = PlaceholderField('blog_post_body')

    def __unicode__(self):
        return self.title

