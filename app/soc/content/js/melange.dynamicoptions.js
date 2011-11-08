/* Copyright 2011 the Melange authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Melange jQuery plugin to add options to select type HTML widgets on the fly
 *
 * Inspired by (and some portions of code taken from) Mike Botsko's jQuery
 * form builder plugin available at
 * http://www.botsko.net/blog/2009/04/jquery-form-builder-plugin/
 */

(function($){
  $.fn.dynamicoptions = function(options) {
 // Extend the configuration options with user-provided
    var defaults = {};
    var opts = $.extend(defaults, options);

    return this.each(function () {
      var addFieldHtml = function (values) {
        field = '';
        field += '<div>';
        field += '<a href="#" class="remove" title="X">X</a>';
        var j = 0;
        for (var i in opts.fields) {
          if (!values) {
            value = ''
          }
          else {
            value = values[j]
          }
          field += '<input type="text" name=' + i + ' class="tagfield" value="' + unescape(value) + '" />';
          j += 1;
        }
        field += '</div>';
        return field;
      };

      field = '<label class="form-label">' + opts.label + '</label>';

      var initial = JSON.parse(opts.initial);

      for (var i in initial) {
        field += addFieldHtml(initial[i]);
      }

      field += '<div class="add-area clearfix"><a id=add-' + opts.id + ' href="#" class="add">Add</a></div>';

      $(this).append(field);

      $('#add-' + opts.id).live('click', function () {
        $(this).parent().before(addFieldHtml());
        return false;
      });

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

    });
  };
})(jQuery);
