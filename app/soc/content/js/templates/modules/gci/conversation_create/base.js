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
    // Constants for specifiying the type of recipients
    var ORGANIZATION = 'Organization';
    var USER         = 'User';
    var PROGRAM      = 'Program';

    jQuery('select, input:checkbox').uniform();

    var $recipients_type = jQuery('#recipients_type');

    // Set up TinyMCE message editor
    var tinyMceConfig = melange.tinyMceConfig(context.tinymce_inputs, 'basic');
    tinyMceConfig['height'] = 300;
    tinyMceConfig['width'] = 660;
    tinyMCE.init(tinyMceConfig);

    // Show/hide recipient form elements for different recipient types
    var update_recipients_form = function() {
      var type = $recipients_type.val();

      jQuery('#organization-container').toggle(type === ORGANIZATION);
      jQuery('#auto_update_users-row').toggle(type !== USER);
      jQuery('#users-container').toggle(type === USER);
      jQuery('#program-roles-container').toggle(type === PROGRAM);
      jQuery('#organization-roles-container').toggle(type === ORGANIZATION);
    };
    $recipients_type.change(update_recipients_form);
    update_recipients_form();

    if ($recipients_type.children().length <= 1) {
      jQuery('#recipients_type-container').hide();
    }
  }
);
