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
    var config = {
      changeMonth: true,
      changeYear: false,
      dateFormat: "yy-mm-dd",
      showButtonPanel: true
    };
    var fields_to_enhance = [
      "#program_start",
      "#program_end",
      "#accepted_organization_announced_deadline",
      "#student_signup_start",
      "#student_signup_end",
      "#application_review_deadline",
      "#student_application_matched_deadline",
      "#accepted_students_announced_deadline",
      "#form_submission_start",
      "#bonding_start",
      "#bonding_end",
      "#coding_start",
      "#coding_end",
      "#suggested_coding_deadline",
      "#mentor_summit_start",
      "#mentor_summit_end"
    ].join(",");
    jQuery(fields_to_enhance).datetimepicker(config);
  }
);
