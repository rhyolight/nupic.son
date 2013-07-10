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
    melange.action.toggleButton(
        "verify-consent-form", "on_off", "",
        context.verify_consent_form_init,
        {checked: "Verified",
         unchecked: "Not verified"});
    melange.action.toggleButton(
        "verify-student-id-form", "on_off", "",
        context.verify_student_id_form_init,
        {checked: "Verified",
         unchecked: "Not verified"});
  }
);
