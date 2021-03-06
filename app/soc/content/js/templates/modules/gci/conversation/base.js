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
    // Set up TinyMCE reply editor
    tinyMceSettings = melange.tinyMceConfig(context.tinymce_inputs, "basic");
    tinyMceSettings["height"] = 240;
    tinyMceSettings["width"] = 640;
    tinyMCE.init(tinyMceSettings);

    // Make tooltips visible only on hover
    melange.action.createCluetip();

    // Create conversation toggle buttons
    if (typeof context.toggle_buttons !== "undefined") {
      jQuery.each(context.toggle_buttons, function(index, button) {
        melange.action.toggleButton(
          button.id,
          button.type,
          button.post_url,
          button.state,
          {
            checked: button.checked_label,
            unchecked: button.unchecked_label
          }
        );
      });
    }
  }
);
