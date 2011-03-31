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
 */
/**
 * @author <a href="mailto:fadinlight@gmail.com">Mario Ferraro</a>
 */
(function () {
  /** @lends melange.datetimepicker */

  if (window.melange === undefined) {
    throw new Error("Melange not loaded");
  }

  var melange = window.melange;

  /** Package that handles a datetimepicker that enriches jQuery UI datepicker
    * @name melange.datetimepicker
    * @namespace melange.datetimepicker
    * @borrows melange.logging.debugDecorator.log as log
    */
  melange.datetimepicker = window.melange.datetimepicker = function () {
    return new melange.datetimepicker();
  };

  /** Shortcut to current package.
    * @private
    */
  var $m = melange.logging.debugDecorator(melange.datetimepicker);

  melange.error.createErrors([
  ]);

  jQuery.fn.datetimepicker = function (config) {
    return this.each(function (config) {
      return function () {
       var _self = jQuery(this);

       var regular_expression = /^(\d{4}-\d{2}-\d{2}) (\d{2}):(\d{2}):(\d{2})$/;
       var tokens = _self.val().match(regular_expression);
 
       if (tokens !== null) {
          _self.val(tokens[1]);
        }

        _self = _self.datepicker(config);

        var selects = {
          "hour": {
            "label": "H:",
            "max": 23,
            "current": tokens !== null ? tokens[2] || "0" : "0"
          },
          "minute": {
            "label": "M:",
            "max": 59,
            "current": tokens !== null ? tokens[3] || "0" : "0"
          },
          "second": {
            "label": "S:",
            "max": 59,
            "current": tokens !== null ? tokens[4] || "0" : "0"
          }
        };

        function create_selects(select) {

          var new_select_id = [
            _self.attr("id"),'_',select
          ].join("");

          var html = [
            '<label for = "',
            new_select_id,
            '" style="display:inline;">',
            selects[select]["label"],
            '</label>',
            '<select id = "',
            new_select_id,
            '" style="margin-top: 3px;">'
          ].join("");
        
          var iterations = selects[select]["max"];
      
          for (var i = 0; i <= iterations; i++) {
            var selected = "";

            if (i === parseInt(selects[select]["current"], 10)) {
              selected = 'selected = "selected"';
            }
            var value = i
            if (i < 10) {
              value = "0" + ("" + i);
            }
            value = "" + value;
            html += [
              '<option value = "', value, '" ',selected,'>',
              value,
              '</option>'
            ].join('');
          }
          html += "</select>";
          return html;
        }
        var hours_select = _self.parent().append(create_selects("hour"));
        var minutes_select = hours_select.append(create_selects("minute"));
        var seconds_select = minutes_select.append(create_selects("second"));

        return _self;
      }
    }(config));
  }
}());
