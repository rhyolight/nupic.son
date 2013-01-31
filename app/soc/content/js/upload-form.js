/* Copyright 2010 the Melange authors.
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


(function ($) {
  if (window.melange === undefined) {
    throw new Error("Melange not loaded");
  }

  var melange = window.melange;

  melange.getUploadUrl = function() {
    // Preserve current query string
    var ampersand_question = "?";
    if (window.location.href.indexOf("?") !== -1) {
      ampersand_question = "&";
    }
    var upload_link;
    jQuery.ajax({
      async: false,
      cache: false,
      url: [
        window.location.href,
        ampersand_question,
        "fmt=json"
      ].join(""),
      dataType: "json",
      success: function( data ) {
        upload_link = data.upload_link;
      },
      error: function(msg, text, e) {
        alert("Could not retrieve upload url: '" + e + "'.");
      }
    });
    return upload_link;
  }

  melange.asyncUpload = function(input_ids) {
    // Following two methods upload files asynchronously.
    var id_selector = input_ids.join(", ");
    jQuery(id_selector)
        .bind('fileuploadsubmit', function (e, data) {
      data.url = melange.getUploadUrl();
      var button = $(this).parent().parent();
      button.hide();
      button.parent().children('.progress').show();
    });

    jQuery(id_selector).fileupload({
      progressall: function (e, data) {
        var progress = parseInt(data.loaded / data.total * 100, 10);
        $('.progress .bar').css(
          'width',
          progress + '%'
        );
      },
      done: function (e, data) {
        var formrow = $(this).parent().parent().parent();
        formrow.children('.progress').hide();
        var filedownload = formrow.children('.filedownload');
        filedownload.children('.filename').html(data.files[0].name);
        filedownload.children('.verified').addClass('button-hide');
        filedownload.children('.to_be_verified').removeClass('button-hide');
        filedownload.removeClass('button-hide');
        filedownload.show();
      }
    });
  }
}(jQuery));
