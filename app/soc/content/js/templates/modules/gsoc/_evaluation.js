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
    jQuery(document).ready(function(){
      jQuery("select, input:radio, input:file, input:checkbox").uniform();

      var config = {
        changeMonth: true,
        changeYear: false,
        dateFormat: "yy-mm-dd",
        showButtonPanel: true
      };
      var fields_to_enhance = [
        "#survey_start",
        "#survey_end"
      ].join(",");
      jQuery(fields_to_enhance).datetimepicker(config);

      jQuery('#form-builder').formbuilder({
        save_url: context.post_url,
        load_url: context.post_url,
        useJson: true
      });
      jQuery(function() {
        jQuery("#form-wrap ul").sortable({ opacity: 0.6, cursor: 'move'});
        // Set all options listings (select, radio and checkbox) to be sortable
        jQuery(".options-wrap").sortable({ items: 'div', opacity: 0.6, cursor: 'move'});
        jQuery('.add_ck, .add_opt, .add_rd').live("click", function() {
          // use test of option to see if this is a sortable element
          // ("one" method doesn't work on click for this element, for some reason)
          if (jQuery.type(jQuery(this).parent().parent().sortable('option','cursor')) !== "string") {
            // if the parent element is not already draggable, make it so
            jQuery(this).parent().parent().sortable({ items: 'div', opacity: 0.6, cursor: 'move'});
          }
          return false;
        });
      });

    });

    tinyMCE.init(melange.tinyMceConfig(["melange-content-textarea"], "advanced"));
  }
);
