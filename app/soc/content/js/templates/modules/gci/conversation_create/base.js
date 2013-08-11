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
    var $users = jQuery('#users');

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

    // Textext input for users, with tags for initial values if initial values
    // are provided. Eval is used because if an initial tags value is provided,
    // it will be in the format of '["foo", "bar"]'.
    var existing_tags = []
    if ($users.val()) {
      try {
        var value = eval($users.val());
        if (value instanceof Array) {
          existing_tags = value;
        }
      } catch (e) {
        // nothing
      }
      $users.val('');
    }
    $users.textext({
        plugins : 'tags',
        tagsItems: existing_tags
    });

    // Forces the textext.js input to create a tag out of entered text by
    // sending the enter key.
    var creating_tag = false;
    var create_tag = function(blur) {
      if (creating_tag) return;
      creating_tag = true;
      var event_down = jQuery.Event("keydown");
      var event_up = jQuery.Event("keyup");
      event_down.keyCode = 13;
      event_up.keyCode = 13;
      $users.triggerHandler(event_down);
      $users.triggerHandler(event_up);
      if (blur) $users.blur();
      creating_tag = false;
    };

    // Create a tag out of remaining text on blur, or a comma or space is typed.
    $users.blur(function() { create_tag(true); });
    $users.bind('keypress', function(event) {
      var character = String.fromCharCode(event.keyCode);
      if (character === ',' || character == ' ') {
        create_tag(false);
        return false;
      }
    });

    if ($recipients_type.children().length <= 1) {
      jQuery('#recipients_type-container').hide();
    }
  }
);
