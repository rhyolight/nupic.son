/* Copyright 2013 the Melange authors.
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
melange.templates.inherit(
  function (_self, context) {
    jQuery("select, input:radio, input:file, input:checkbox").uniform();
    jQuery("#birth_date").datepicker({
      changeMonth: true,
      changeYear: true,
      dateFormat: "yy-mm-dd",
      showButtonPanel: true,
      minDate: "-90y",
      maxDate: "+0D",
      yearRange: "-90",
      defaultDate: '1990-01-01'
    });
    var url = "?fmt=json&field=school_name";
    jQuery.ajax({
      url: url,
      success: function(data) {
        var getSchools = function() {
          var country = jQuery("#school_country").attr('value');
          var schools = data[country];
          if(!schools) {
              return [];
          }
          return schools;
        };
        var onchange = function() {
          jQuery("#school_name").autocomplete({
              'source': getSchools()
          });
        };
        jQuery("#school_country").change(onchange);
        // trigger autocomplete for the currently selected country
        onchange();
      }
    });
  }
);
