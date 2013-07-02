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
    /* Apply Uniform CSS to form fields. */
    jQuery("select").uniform();

    /* Change all the tooltips to be displayed onhover over a
    * question mark. Calling this function only once will take
    * care of all such instances.
    */
    melange.action.createCluetip();

    /* Create the project featured button and make it post using ajax. */
    if (typeof context.user_toggle_buttons !== "undefined") {
      jQuery.each(context.user_toggle_buttons, function(index, button) {
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

    /* Add new mentors upon the click of "Add new" link below assign mentors*/
    var last_id = 1;
    new_link = function () {
      var new_mentor = jQuery("select#id-assign-mentor").clone(true);
      new_mentor = new_mentor.attr(
          'id', new_mentor.attr('id') + '-new-' + last_id);
      new_mentor.appendTo("div#user-menu-select-mentors");
      new_mentor.children('option').each(function () {
        jQuery(this).removeAttr('selected');
        jQuery(this).removeAttr('disabled');
      });
      new_mentor.uniform();
      last_id++;
    };

    function initialize() {
      var blog = new BlogPreview(document.getElementById("blog-feed"));
      blog.show(context.feed_url, 5, "Blog Feed");
    }

    if (typeof context.feed_url !== "undefined") {
      jQuery(
        function () {
          google.load("feeds","1", {callback:initialize});
        }
      );
    }
  }
);
