(function($) {
	$.fn.listenForChange = function(options) {
		settings = $.extend({
			interval: 200 // in microseconds
		}, options);

		var jquery_object = this;
		var current_focus = null;

		jquery_object.filter(":input").add(":input", jquery_object).focus(
			function() {
				current_focus = this;
			}).blur(function() {
				current_focus = null;
			});

		setInterval(function() {
			// allow
			jquery_object.filter(":input").add(":input", jquery_object).each(function() {
				// set data cache on element to input value if not yet set
				if ($(this).data('change_listener') == undefined) {
					$(this).data('change_listener', $(this).val());
					return;
				}
				// return if the value matches the cache
				if ($(this).data('change_listener') == $(this).val()) {
					return;
				}
				// ignore if element is in focus (since change event will fire on blur)
				if (this == current_focus) {
					return;
				}
				// if we make it here, manually fire the change event and set the new value
				$(this).trigger('change');
				$(this).data('change_listener', $(this).val());
			});
		}, settings.interval);
		return this;
	};
})(jQuery);

(function($) {
	$.fn.fkAutocomplete = function(settings) {
		var input_obj = this;
		var input_obj_id = this.attr('id');
		var input_obj_name = input_obj_id.replace("id_", "");
		var content_type_obj_id = input_obj_id.replace('_object_id', '_content_type');
		var config = {
			is_generic_lookup: false,
			search_url: "",
			max: 50,
			width: 300,
			initialLabel: "none",
			content_type_id: '',
			add_urls: {},
			admin_media_prefix: '/static/admin/'
		}
		if (settings) $.extend(config, settings);
		var autocomplete_config = {
			dataType: "json",
			max: config.max,
			width: config.width,
			matchSubset: false,
			parse: function(data) {
				return $.map(data, function(row) {
					return {
						data: row,
						value: row.name,
						result: row.title
					}
				});
			},
			formatItem: function(item, i, n, search_term) {
				r = '';
				if (item.thumbnail_url) {
					r += '<img class="item_thumbnail" src="' + item.thumbnail_url + '" alt="" />';
				}
				r += '<div class="item_title">' + item.title + '</div>' + '  <div class="item_description">' + item.description + '</div></div>';
				return r;
			},
			extraParams: {
				content_type_id: config.content_type_id
			},
			highlight: function(value, term) {
				return value.replace(new RegExp("(?![^&;]+;)(?!<[^<>]*)(" + term.replace(/([\^\$\(\)\[\]\{\}\*\.\+\?\|\\])/gi, "\\$1").replace(" ", "|") + ")(?![^<>]*>)(?![^&;]+;)", "gi"), "<strong>$1</strong>");
			},
		}
		if (config.is_generic_lookup) {
			autocomplete_config.extraParams.content_type_id = function() {
				return $("#" + content_type_obj_id).val();
			}
		}
		this.each(function(i) {
			var main_input = $(this);
			var name = main_input.attr('name');
			main_input.hide();
			$(this).after(
				'<input size=25 type="text" id="lookup_' + input_obj_name + '" value="' + config.initialLabel + '" />' +
					' <a href="#" id="del_' + input_obj_name + '" style="display: none;"><img width="10" height="10" alt="Remove" src="' + config.admin_media_prefix + 'img/icon_deletelink.gif" /></a>' +
					' <a onclick="return showAddAnotherPopup(this);" id="add_id_' + input_obj_name + '" class="add-another" href="#" style="display: none;"> <img width="10" height="10" alt="Add Another" src="' + config.admin_media_prefix + 'img/icon_addlink.gif"></a>'
			);
			if (main_input.val()) {
				$('#del_' + input_obj_name).show();
			}
			var lookup_input = $("#lookup_" + name);
			lookup_input.autocomplete(config.search_url, autocomplete_config).result(function(event, item) {
				if (item) {
					input_obj.val(item.identifier);
					$('#del_' + input_obj_name).show();
				}
			});
			$('#del_' + input_obj_name).click(function(ele, event) {
				$('#id_' + input_obj_name).val('');
				$('#del_' + input_obj_name).hide();
				$('#lookup_' + input_obj_name).val('');
				return false;
			});
			if (config.is_generic_lookup) {
				$('#' + content_type_obj_id).change(function() {
					$('#id_' + input_obj_name).val('');
					$('#del_' + input_obj_name).hide();
					$('#lookup_' + input_obj_name).val('');
					$('#lookup_' + input_obj_name).flushCache();
					var current_content_type_id = $('#' + content_type_obj_id).val();
                    if (input_obj_id.val) {
                        if (config.add_urls[config.content_type_id].add_url) {
    						$('#add_id_' + input_obj_name).attr('href', config.add_urls[current_content_type_id].add_url);
    						$('#add_id_' + input_obj_name).show();
    					} else {
    						$('#add_id_' + input_obj_name).hide();
    					}
    				}	
				});
				if (config.content_type_id) {
					$('#add_id_' + input_obj_name).attr('href', config.add_urls[config.content_type_id].add_url);
					$('#add_id_' + input_obj_name).show();
				}
			}
		});
		return this;
	};
})(jQuery);