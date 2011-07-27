/* Copyright 2011 the Melange authors.
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
/**
 * @author <a href="mailto:orc.avs@gmail.com">Orcun Avsar</a>
 */
(function () {
  /** @lends melange.gdata */

  if (window.melange === undefined) {
    throw new Error("Melange not loaded");
  }

  var melange = window.melange;

  /** Package that handles gdata related functions
    * @name melange.gdata
    * @namespace melange.gdata
    * @borrows melange.logging.debugDecorator.log as log
    */
  melange.gdata = window.melange.gdata = function () {
    return new melange.gdata();
  };

  /** Shortcut to current package.
    * @private
    */
  var $m = melange.logging.debugDecorator(melange.gdata);

  melange.error.createErrors([
  ]);

  // Store local variables here
  var locals = {
    is_logged_in: false,
    popup_oauth_redirect_url: '',
    success_callback: null,
    success_callback_parameters: null,
  };

  $m.init = function (is_logged_in, popup_oauth_redirect_url) {
    locals.is_logged_in = is_logged_in;
    locals.popup_oauth_redirect_url = popup_oauth_redirect_url;
  };

  // Public function to be accessed by success popup window
  $m.loginSuccessful = function () {
    locals.is_logged_in = true;
    if (locals.success_callback !== null) {
      locals.success_callback.apply(this, locals.success_callback_parameters);

      // Success callback is run, set to null
      locals.success_callback = null;
      locals.success_callback_parameters = null;
    }
  };

  $m.loginFunctionFactory = function (callback, parameters) {
    function fn() {
      if (locals.is_logged_in) {
        callback.apply(this, parameters);
      }
      else {
        locals.success_callback = callback;
        locals.success_callback_parameters = parameters;

        // Center popup window on screen
        var width = window.screen.availWidth;
        var height = window.screen.availHeight;
        var pop_width = 400;
        var pop_height = 500;
        var left_pos = (width - pop_width) / 2;
        var top_pos = (height - pop_height) / 2;
        window.open(
          locals.popup_oauth_redirect_url, 'popup',
          [
           'width=', pop_width, ',',
           'height=', pop_height, ',',
           'top=', top_pos, ',',
           'left=', left_pos
          ].join("")
        );
      }
    };
    return fn;
  };
}());
