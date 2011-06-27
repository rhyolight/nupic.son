/**
 * jQuery Form Builder Plugin
 * Copyright (c) 2009 Mike Botsko, Botsko.net LLC (http://www.botsko.net)
 * http://www.botsko.net/blog/2009/04/jquery-form-builder-plugin/
 * Originally designed for AspenMSM, a CMS product from Trellis Development
 * Licensed under the MIT (http://www.opensource.org/licenses/mit-license.php)
 * Copyright notice and license must remain intact for legal use
 */
(function ($) {
	$.fn.formbuilder = function (options) {
		// Extend the configuration options with user-provided
		var defaults = {
			save_url: false,
			load_url: false,
			control_box_target: false,
			useJson: true, // XML as fallback
			serialize_prefix: 'frmb',
			messages: {
				save				: "Save",
				add_new_field		: "Add New Field...",
				text				: "Text Field",
				title				: "Title",
				paragraph			: "Paragraph",
				checkboxes			: "Checkboxes",
				radio				: "Radio",
				select				: "Select List",
				text_field			: "Text Field",
				label				: "Label",
				paragraph_field		: "Paragraph Field",
				select_options		: "Select Options",
				add					: "Add",
				checkbox_group		: "Checkbox Group",
				remove_message		: "Are you sure you want to remove this element?",
				remove				: "X",
				radio_group			: "Radio Group",
				selections_message	: "Allow Multiple Selections",
				hide				: "Hide",
				required			: "Required",
				show				: "Show"
			}
		};
		var opts = $.extend(defaults, options);
		var frmb_id = 'frmb-' + $('ul[id^=frmb-]').length++;
		return this.each(function () {
			var ul_obj = $(this).append('<ul id="' + frmb_id + '" class="frmb"></ul>').find('ul');
			var field = '';
			var field_type = '';
			var last_id = 1;
			var help;
			// Add a unique class to the current element
			$(ul_obj).addClass(frmb_id);

			// Create form control select box and add into the editor
			var controlBox = function (target) {
					var select = '';
					var box_content = '';
					var save_button = '';
					var box_id = frmb_id + '-control-box';
					var save_id = frmb_id + '-save-button';
					// Add the available options
					select += '<option value="0">' + opts.messages.add_new_field + '</option>';
					select += '<option value="input_text">' + opts.messages.text + '</option>';
					select += '<option value="textarea">' + opts.messages.paragraph + '</option>';
					select += '<option value="checkbox">' + opts.messages.checkboxes + '</option>';
					select += '<option value="radio">' + opts.messages.radio + '</option>';
					select += '<option value="select">' + opts.messages.select + '</option>';
					// Build the control box and search button content
					box_content = '<select id="' + box_id + '" class="frmb-control">' + select + '</select>';
					save_button = '<input type="submit" id="' + save_id + '" class="frmb-submit" value="' + opts.messages.save + '"/>';
					// Insert the control box into page
					if (!target) {
						$(ul_obj).before(box_content);
					} else {
						$(target).append(box_content);
					}
					// Insert the search button
					$(ul_obj).after(save_button);
					// Set the form save action
					$('#' + save_id).click(function () {
					  $('#schema').attr('value', JSON.stringify($(ul_obj).serializeFormList()));
					  $('#form').submit();
					  return true;
					});
					// Add a callback to the select element
					$('#' + box_id).change(function () {
						appendNewField($(this).val());
						$(this).val(0).blur();
						// This solves the scrollTo dependency
						$('body').animate({
							scrollTop: $('#frm-' + (last_id - 1) + '-item').offset().top
						}, 500);
						return false;
					});
				}(opts.control_box_target);
			// XML parser to build the form builder
			var fromXml = function (xml) {
					var values = '';
					var options = false;
					var required = false;
					$(xml).find('field').each(function () {
						// checkbox type
						if ($(this).attr('type') === 'checkbox') {
							options = [$(this).attr('label')];
							values = [];
							$(this).find('checkbox').each(function () {
								values.push([$(this).text(), $(this).attr('checked')]);
							});
						}
						// radio type
						else if ($(this).attr('type') === 'radio') {
							options = [$(this).attr('label')];
							values = [];
							$(this).find('radio').each(function () {
								values.push([$(this).text(), $(this).attr('checked')]);
							});
						}
						// select type
						else if ($(this).attr('type') === 'select') {
							options = [$(this).attr('label'), $(this).attr('multiple')];
							values = [];
							$(this).find('option').each(function () {
								values.push([$(this).text(), $(this).attr('checked')]);
							});
						}
						else {
							values = $(this).text();
						}
						appendNewField($(this).attr('type'), values, options, $(this).attr('required'));
					});
				};
			// Json parser to build the form builder
			var fromJson = function (json) {
					var values = '';
					var options = false;
					var required = false;
					// Parse json
					$(json).each(function () {
					// checkbox type

            if (this.class === 'input_text') {
              options = [this.label];
            }
            if (this.class === 'textarea') {
              options = [this.label];
            }
						// checkbox type
            else if (this.class === 'checkbox') {
							options = [this.label];
							values = [];
							$.each(this.values, function () {
								values.push([this.value, this.default]);
							});
						}
						// radio type
						else if (this.class === 'radio') {
							options = [this.label];
							values = [];
							$.each(this.values, function () {
								values.push([this.value, this.default]);
							});
						}
						// select type
						else if (this.class === 'select') {
							options = [this.label, this.multiple];
							values = [];
							$.each(this.values, function () {
								values.push([this.value, this.default]);
							});
						}
						else {
							values = [this.values];
						}
						appendNewField(this.class, values, options, this.required);
					});
				};
			// Wrapper for adding a new field
			var appendNewField = function (type, values, options, required) {
					field = '';
					field_type = type;
					if (typeof (values) === 'undefined') {
						values = '';
					}
					switch (type) {
					case 'input_text':
						appendTextInput(values, options, required);
						break;
					case 'textarea':
						appendTextarea(values, options, required);
						break;
					case 'checkbox':
						appendCheckboxGroup(values, options, required);
						break;
					case 'radio':
						appendRadioGroup(values, options, required);
						break;
					case 'select':
						appendSelectList(values, options, required);
						break;
					}
				};
			// single line input type="text"
			var appendTextInput = function (values, options, required) {
  			  var label = '';
          if (typeof (options) === 'object') {
            label = options[0];
          }
					field += '<label>' + opts.messages.label + '</label>';
					field += '<input class="fld-label" id="label-' + last_id + '" type="text" value="' + unescape(label) + '" />';
					help = '';
					appendFieldLi(opts.messages.text, field, required, help);
				};
			// multi-line textarea
			var appendTextarea = function (values, options, required) {
			    var label = '';
			    if (typeof (options) === 'object') {
            label = options[0];
          }
					field += '<label>' + opts.messages.label + '</label>';
					field += '<input type="text" value="' + unescape(label) + '" />';
					help = '';
					appendFieldLi(opts.messages.paragraph_field, field, required, help);
				};
			// adds a checkbox element
			var appendCheckboxGroup = function (values, options, required) {
					var label = '';
					if (typeof (options) === 'object') {
						label = options[0];
					}
					field += '<div class="chk_group">';
					field += '<div class="frm-fld"><label>' + opts.messages.label + '</label>';
					field += '<input type="text" name="label" value="' + unescape(label) + '" /></div>';
					field += '<div class="false-label">' + opts.messages.select_options + '</div>';
					field += '<div class="fields">';
					if (typeof (values) === 'object') {
						for (i = 0; i < values.length; i++) {
							field += checkboxFieldHtml(values[i]);
						}
					}
					else {
						field += checkboxFieldHtml('');
					}
					field += '<div class="add-area"><a href="#" class="add add_ck">' + opts.messages.add + '</a></div>';
					field += '</div>';
					field += '</div>';
					help = '';
					appendFieldLi(opts.messages.checkbox_group, field, required, help);
				};
			// Checkbox field html, since there may be multiple
			var checkboxFieldHtml = function (values) {
					var checked = false;
					var value = '';
					if (typeof (values) === 'object') {
						value = values[0];
						checked = values[1] === 'false' ? false : true;
					}
					field = '';
					field += '<div>';
					field += '<input type="checkbox"' + (checked ? ' checked="checked"' : '') + ' />';
					field += '<input type="text" value="' + unescape(value) + '" />';
					field += '<a href="#" class="remove" title="' + opts.messages.remove_message + '">' + opts.messages.remove + '</a>';
					field += '</div>';
					return field;
				};
			// adds a radio element
			var appendRadioGroup = function (values, options, required) {
					var label = '';
					if (typeof (options) === 'object') {
						label = options[0];
					}
					field += '<div class="rd_group">';
					field += '<div class="frm-fld"><label>' + opts.messages.label + '</label>';
					field += '<input type="text" name="label" value="' + unescape(label) + '" /></div>';
					field += '<div class="false-label">' + opts.messages.select_options + '</div>';
					field += '<div class="fields">';
					if (typeof (values) === 'object') {
						for (i = 0; i < values.length; i++) {
							field += radioFieldHtml(values[i], 'frm-' + last_id + '-fld');
						}
					}
					else {
						field += radioFieldHtml('', 'frm-' + last_id + '-fld');
					}
					field += '<div class="add-area"><a href="#" class="add add_rd">' + opts.messages.add + '</a></div>';
					field += '</div>';
					field += '</div>';
					help = '';
					appendFieldLi(opts.messages.radio_group, field, required, help);
				};
			// Radio field html, since there may be multiple
			var radioFieldHtml = function (values, name) {
					var checked = false;
					var value = '';
					if (typeof (values) === 'object') {
						value = values[0];
						checked = values[1] === 'false' ? false : true;
					}
					field = '';
					field += '<div>';
					field += '<input type="radio"' + (checked ? ' checked="checked"' : '') + ' name="radio_' + name + '" />';
					field += '<input type="text" value="' + unescape(value) + '" />';
					field += '<a href="#" class="remove" title="' + opts.messages.remove_message + '">' + opts.messages.remove + '</a>';
					field += '</div>';
					return field;
				};
			// adds a select/option element
			var appendSelectList = function (values, options, required) {
					var multiple = false;
					var label = '';
					if (typeof (options) === 'object') {
						label = options[0];
						multiple = options[1] === 'true' ? true : false;
					}
					field += '<div class="opt_group">';
					field += '<div class="frm-fld"><label>' + opts.messages.label + '</label>';
					field += '<input type="text" name="label" value="' + unescape(label) + '" /></div>';
					field += '';
					field += '<div class="false-label">' + opts.messages.select_options + '</div>';
					field += '<div class="fields">';
					field += '<input type="checkbox" name="multiple"' + (multiple ? 'checked="checked"' : '') + '>';
					field += '<label class="auto">' + opts.messages.selections_message + '</label>';
					if (typeof (values) === 'object') {
						for (i = 0; i < values.length; i++) {
							field += selectFieldHtml(values[i], multiple);
						}
					}
					else {
						field += selectFieldHtml('', multiple);
					}
					field += '<div class="add-area"><a href="#" class="add add_opt">' + opts.messages.add + '</a></div>';
					field += '</div>';
					field += '</div>';
					help = '';
					appendFieldLi(opts.messages.select, field, required, help);
          //initialize_sortable_options();
      };
			// Select field html, since there may be multiple
			var selectFieldHtml = function (values, multiple) {
					if (multiple) {
						return checkboxFieldHtml(values);
					}
					else {
						return radioFieldHtml(values);
					}
				};
			// Appends the new field markup to the editor
			var appendFieldLi = function (label, field_html, required, help) {
					if (required) {
						required = required === true ? true : false;
					}
					var li = '';
					li += '<li id="frm-' + last_id + '-item" class="' + field_type + '">';
					li += '<div class="legend">';
					li += '<a id="frm-' + last_id + '" class="toggle-form" href="#">' + opts.messages.hide + '</a> ';
					li += '<strong id="txt-label-' + last_id + '">' + label + '</strong></div>';
					li += '<div id="frm-' + last_id + '-fld" class="frm-holder">';
					li += '<div class="frm-elements">';
					li += field;
					li += '<div class="frm-fld frm-fld-req"><label for="required-' + last_id + '">' + opts.messages.required + '</label>';
					li += '<input class="required" type="checkbox" value="1" name="required-' + last_id + '" id="required-' + last_id + '"' + (required ? ' checked="checked"' : '') + ' /></div>';
					li += '<a id="del_' + last_id + '" class="del-button delete-confirm" href="#" title="' + opts.messages.remove_message + '"><span>Delete</span></a>';
					li += '</div>';
					li += '</div>';
					li += '</li>';
					$(ul_obj).append(li);
					$('#frm-' + last_id + '-item').hide();
					$('#frm-' + last_id + '-item').animate({
						opacity: 'show',
						height: 'show'
					}, 'slow');
					last_id++;
				};
      // load existing form data
      fromJson(JSON.parse($('#schema').attr('value')));

			// handle field delete links
			$('.remove').live('click', function () {
				$(this).parent('div').animate({
					opacity: 'hide',
					height: 'hide',
					marginBottom: '0px'
				}, 'fast', function () {
					$(this).remove();
				});
				return false;
			});
			// handle field display/hide
			$('.toggle-form').live('click', function () {
				var target = $(this).attr("id");
				if ($(this).html() === opts.messages.hide) {
					$(this).removeClass('open').addClass('closed').html(opts.messages.show);
					$('#' + target + '-fld').animate({
						opacity: 'hide',
						height: 'hide'
					}, 'slow');
					return false;
				}
				if ($(this).html() === opts.messages.show) {
					$(this).removeClass('closed').addClass('open').html(opts.messages.hide);
					$('#' + target + '-fld').animate({
						opacity: 'show',
						height: 'show'
					}, 'slow');
					return false;
				}
				return false;
			});
			// handle delete confirmation
			$('.delete-confirm').live('click', function () {
				var delete_id = $(this).attr("id").replace(/del_/, '');
				if (confirm($(this).attr('label'))) {
					$('#frm-' + delete_id + '-item').animate({
						opacity: 'hide',
						height: 'hide',
						marginBottom: '0px'
					}, 'slow', function () {
						$(this).remove();
					});
				}
				return false;
			});
			// Attach a callback to add new checkboxes
			$('.add_ck').live('click', function () {
				$(this).parent().before(checkboxFieldHtml());
				return false;
			});
			// Attach a callback to add new options
			$('.add_opt').live('click', function () {
				$(this).parent().before(selectFieldHtml('', false));
				return false;
			});
			// Attach a callback to add new radio fields
			$('.add_rd').live('click', function () {
				$(this).parent().before(radioFieldHtml(false, $(this).parents('.frm-holder').attr('id')));
				return false;
			});
			// saves the serialized data to the server 
			var save = function () {
					if (opts.save_url) {
						$.ajax({
							type: "POST",
							url: opts.save_url,
							data: $(ul_obj).serializeFormList({
								prepend: opts.serialize_prefix
							}),
							success: function (xml) {}
						});
					}
				};
		});
	};
})(jQuery);
/**
 * jQuery Form Builder List Serialization Plugin
 * Copyright (c) 2009 Mike Botsko, Botsko.net LLC (http://www.botsko.net)
 * Originally designed for AspenMSM, a CMS product from Trellis Development
 * Licensed under the MIT (http://www.opensource.org/licenses/mit-license.php)
 * Copyright notice and license must remain intact for legal use
 * Modified from the serialize list plugin
 * http://www.botsko.net/blog/2009/01/jquery_serialize_list_plugin/
 */
(function($){
  $.fn.serializeFormList = function(options) {
    // Extend the configuration options with user-provided
    var defaults = {
      prepend: 'ul',
      is_child: false,
      attributes: ['class']
    };
    var opts = $.extend(defaults, options);
    var formJSON = [];
    
    if(!opts.is_child){ opts.prepend = '&'+opts.prepend; }
    
    // Begin the core plugin
    this.each(function() {
      var ul_obj = this;

      $(this).children().each(function(){
        for(att in opts.attributes){
          var fieldDict = {};
          fieldDict[opts.attributes[att]] = escape($(this).attr(opts.attributes[att]));

          // append the form field values
          if(opts.attributes[att] == 'class'){
            fieldDict.required = $('#'+$(this).attr('id')+' input.required').attr('checked');

            switch($(this).attr(opts.attributes[att])){
              case 'input_text':
                fieldDict.label = escape($('#'+$(this).attr('id')+' input[type=text]').val());
                break;
              case 'textarea':
                fieldDict.label = escape($('#'+$(this).attr('id')+' input[type=text]').val());
                break;
              case 'checkbox':
                fieldDict.values = [];
                $('#'+$(this).attr('id')+' input[type=text]').each(function(){
                  
                  if($(this).attr('name') == 'label'){
                    fieldDict.label = escape($(this).val());
                  } else {
                    var valueDict = {};
                    valueDict.value = escape($(this).val());
                    valueDict.checked = $(this).prev().attr('checked');
                    fieldDict.values.push(valueDict);
                  }
                });
                break;
              case 'radio':
                fieldDict.values = [];
                $('#'+$(this).attr('id')+' input[type=text]').each(function(){
                  if($(this).attr('name') == 'label'){
                    fieldDict.label = escape($(this).val());
                  } else {
                    var valueDict = {};
                    valueDict.value = escape($(this).val());
                    valueDict.checked = $(this).prev().attr('checked');
                    fieldDict.values.push(valueDict);
                  }
                });
                break;
              case 'select':
                fieldDict.multiple = $('#'+$(this).attr('id')+' input[name=multiple]').attr('checked');
                
                $('#'+$(this).attr('id')+' input[type=text]').each(function(){
                  
                  if($(this).attr('name') == 'label'){
                    fieldDict.label = escape($(this).val());
                  } else {
                    var valueDict = {};
                    valueDict.value = escape($(this).val());
                    valueDict.checked = $(this).prev().attr('checked');
                    fieldDict.values.push(valueDict);
                  }
                });
              break;
            }
          }
          formJSON.push(fieldDict);
        }
      });
    });
    return(formJSON);
  };
})(jQuery);