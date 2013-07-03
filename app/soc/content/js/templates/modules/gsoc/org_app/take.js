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

    jQuery(document).ready(function () {

      jQuery(':checkbox[value="Other"],:radio').each(function () {
        if (jQuery(this).val() == "Other") {
          var selector = "#form_row_" + jQuery(this).attr("name") + "-other";
          if (jQuery(this).parent().attr("class") == "checked") {
            jQuery(selector).show();
          } else {
            jQuery(selector).hide();
          }
        }
      });

      jQuery(':radio').change(function () {
        var selector = "#form_row_" + jQuery(this).attr("name") + "-other";
        if (jQuery(this).val() != "Other") {
          jQuery(selector).hide("Blind");
        } else {
          jQuery(selector).show("Blind");
        }
      });
      jQuery(':checkbox[value="Other"]').change(function () {
        var selector = "#form_row_" + jQuery(this).attr("name") + "-other";
        jQuery(selector).toggle("Blind");
      });
    });
  }
);
