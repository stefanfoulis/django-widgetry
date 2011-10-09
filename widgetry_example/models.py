#-*- coding: utf-8 -*-
from django.db import models
from widgetry.views import search
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class Avatar(models.Model):
    user = models.ForeignKey(User)
    image = models.ImageField(upload_to='avatars')


class Link(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.name


class SimpleModel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    order = models.IntegerField(default=0)
    char1 = models.CharField(max_length=255)
    char2 = models.CharField(max_length=255, blank=True, default='')
    char3 = models.CharField(max_length=255, blank=True, default='')
    char4 = models.CharField(max_length=255, blank=True, default='')
    bol1 = models.BooleanField(default=False)
    bol2 = models.BooleanField(default=False)
    bol3 = models.BooleanField(default=False)
    url = models.URLField(blank=True, default='', verify_exists=False)
    foo = models.ForeignKey('Foo')

    def __unicode__(self):
        return self.name


class SimpleInlineModel(models.Model):
    simple_model = models.ForeignKey(SimpleModel)
    order = models.IntegerField(default=0)
    field1 = models.BooleanField(default=False)
    field2 = models.CharField(max_length=10)
    foo = models.ForeignKey('Foo')


class AnotherSimpleInlineModel(models.Model):
    simple_model = models.ForeignKey(SimpleModel)
    order = models.IntegerField(default=0)
    field1 = models.BooleanField(default=False)
    field2 = models.CharField(max_length=10)


class Foo(models.Model):
    name = models.CharField(max_length=255)
    value = models.IntegerField()

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.value)

search.register(Foo, search_fields=['name', 'value'])


class Bar(models.Model):
    name = models.CharField(max_length=255)
    value = models.IntegerField()


    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.value)

search.register(Foo, search_fields=['name', 'value'])