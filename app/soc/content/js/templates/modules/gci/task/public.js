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
    if (typeof context.comments !== "undefined") {
      tinyMCE.init(melange.tinyMceConfig(context.comments));
    }
    // Task pages: Hide/show reply box
    jQuery(document).ready(function(){
      jQuery(".task-btn-comment-reply").click(function(){
        jQuery(this).toggleClass("active").next().slideToggle("slow");
      });

      jQuery(".task-btn-comment-new").click(function(){
        jQuery(this).toggleClass("active").next().slideToggle("slow");
      });

  /* If there is an error in the comment form, it should be expanded */
  jQuery(".form-comment-post-new").each(function() {

    var errors = jQuery(this).find(".error");
    if (errors.length > 0) {
    jQuery(this).closest("div.block-comments-post-new").slideDown("slow");
    }

  });

      jQuery(".task-btn-extended-deadline").click(function() {
          jQuery("#deadline-extend").toggle();
      });

      jQuery("#deadline-extend-close").click(function() {
          jQuery("#deadline-extend").toggle();
      });

      /* Fancy dynamic remaining time displaying clock */
      //melange.clock.loadClock({{ complete_percentage }});

      var form_name = "#file-form";
      jQuery(form_name).submit(function() {
        var url = melange.getUploadUrl();
        jQuery(form_name).get(0).setAttribute('action', url);
        return true;
      });

      jQuery('input[name="button_unpublish"]').click(function(event) {
        jQuery('#task_form').data('unpublish_button', true);
      });

      jQuery('input[name="button_delete"]').click(function(event) {
        jQuery('#task_form').data('delete_button', true);
      });

      jQuery('#task_form').submit(function(event) {

        var unpublish_clicked = !!jQuery('#task_form').data('unpublish_button');
        var unpublish_allowed = !!jQuery('#task_form').data('unpublish_allow');
        if (unpublish_clicked && unpublish_allowed) {
          jQuery('#task_form').data('unpublish_allow', false);
          jQuery('#task_form').data('unpublish_button', false);
          return true;
        }
        if (unpublish_clicked) {
          jQuery('#task_form').data('unpublish_button', false);
          event.preventDefault();
          event.stopPropagation();
          $("#unpublish-confirm-dialog").dialog({
            title: "Confirm Unpublish",
            resizable: false,
            height:140,
            modal: true,
            buttons: {
              "Unpublish": function() {
                $(this).dialog("close");
                jQuery('#task_form').data('unpublish_allow', true);
                jQuery('input[name="button_unpublish"]').click();
              },
              Cancel: function() {
                $(this).dialog("close");
              }
            }
          });
        }

        var delete_clicked = !!jQuery('#task_form').data('delete_button');
        var delete_allowed = !!jQuery('#task_form').data('delete_allow');
        if (delete_clicked && delete_allowed) {
          jQuery('#task_form').data('delete_allow', false);
          jQuery('#task_form').data('delete_button', false);
          return true;
        }
        if (delete_clicked) {
          jQuery('#task_form').data('delete_button', false);
          event.preventDefault();
          event.stopPropagation();
          $("#delete-confirm-dialog").dialog({
            title: "Confirm Delete",
            resizable: false,
            height:140,
            modal: true,
            buttons: {
              "Delete": function() {
                $(this).dialog("close");
                jQuery('#task_form').data('delete_allow', true);
                jQuery('input[name="button_delete"]').click();
              },
              Cancel: function() {
                $(this).dialog("close");
              }
            }
          });
        }

      });
    });
  }
);
