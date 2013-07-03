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

    /* Add new mentors upon the click of "Add new" link below assign mentors*/
    var last_id = 1;
    new_link = function () {
      var new_mentor = jQuery("select#assign-mentor-0").clone(true);
      new_mentor = new_mentor.attr(
          'id', new_mentor.attr('id') + '-new-' + last_id);
      new_mentor.appendTo("div#select-mentors-wrapper");
      new_mentor.children('option').each(function () {
        jQuery(this).removeAttr('selected');
        jQuery(this).removeAttr('disabled');
      });
      new_mentor.uniform();
      last_id++;
    };
    tinyMCE.init(melange.tinyMceConfig(["melange-description-textarea"], "advanced"));
  }
);
