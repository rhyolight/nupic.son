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
    tinyMCE.init(melange.tinyMceConfig(["melange-description-textarea",
                                       "accepted_orgs_msg"]));
    melange.autocomplete.makeAutoComplete("org_admin_agreement");
    melange.autocomplete.makeAutoComplete("mentor_agreement");
    melange.autocomplete.makeAutoComplete("student_agreement");
    melange.autocomplete.makeAutoComplete("about_page");
    melange.autocomplete.makeAutoComplete("events_page");
    melange.autocomplete.makeAutoComplete("connect_with_us_page");
    melange.autocomplete.makeAutoComplete("help_page");
    melange.autocomplete.makeAutoComplete("terms_and_conditions");

    jQuery('#form_row_task_types').dynamicoptions({
      id: "task-types",
      label: context.label,
      initial: context.initial,
      fields: {task_type_name: 'Tag name'}
    });
  }
);
