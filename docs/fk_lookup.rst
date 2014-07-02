.. _fk_lookup:

fk_lookup
=========

.. danger:: currently there are no permission checks on the lookups. So any data item that is registered for autocomplete
            will be visible to the world!

Include the search lookup urls (``urls.py``)::

	url('^autocomplete/$', 'widgetry.views.search', name='widgetry-search'),


Register models that should be searchable (preferrable in ``models.py`` of your app)::

	from widgetry.views import search
	search.register(MyModel, search_fields=['name', 'value'])

``search_fields`` is a list of fieldnames that should be used to search for
matches. By default the ``__unicode__`` representation of the model will be
used to display the matches. This can be overridden (to be documented). It is
even possible to add a thumbnail image to each matched item (to be documented).

The widget can be defined on forms just like any other widget. If you'd like to override all `ForeignKey` s on a
ModelAdmin, you can use this trick::

	class MyModelAdmin(admin.ModelAdmin):
	    def formfield_for_dbfield(self, db_field, **kwargs):
	        if isinstance(db_field, models.ForeignKey):
	            kwargs['widget'] = FkLookup(db_field.rel.to)
	        return super(MyModelAdmin, self).formfield_for_dbfield(db_field, **kwargs)


generic fk_lookup
-----------------

to be documented.


displaying thumbnails
---------------------

to be documented.