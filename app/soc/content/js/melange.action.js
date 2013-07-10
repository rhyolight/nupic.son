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
 * @author <a href="mailto:madhusudancs@gmail.com">Madhusudan.C.S</a>
 */
(function () {
  /** @lends melange.action */

  if (window.melange === undefined) {
    throw new Error("Melange not loaded");
  }

  var melange = window.melange;

  /** Package that handles all action buttons related functions
    * @name melange.action
    * @namespace melange.action
    * @borrows melange.logging.debugDecorator.log as log
    */
  melange.action = window.melange.action = function () {
    return new melange.action();
  };

  /** Shortcut to current package.
    * @private
    */
  var $m = melange.logging.debugDecorator(melange.action);

  $m.toggleButton = function (id, type, postUrl, initState, labels, callback) {
    jQuery(document).ready(function() {
      jQuery("." + type + " :checkbox#" + id)
        .iphoneStyle({
          checkedLabel: labels.checked,
          uncheckedLabel: labels.unchecked
        })
        .change(function (){
          jQuery.post(
            postUrl,
            {
              id: id,
              value: initState,
              xsrf_token: window.xsrf_token
            },
            function() {
              if (callback !== undefined && typeof(callback) === "function") {
                callback();
              }
            }
          );
        });
    });
  };

  $m.createCluetip = function () {
    jQuery(document).ready(function() {
      jQuery("a.load-tooltip").cluetip({
        local: true,
        cursor: "pointer",
        showTitle: false,
        tracking: true,
        dropShadow: false
      });
    });
  };
}());
