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
 * @author <a href="mailto:fadinlight@gmail.com">Mario Ferraro</a>
 * @author <a href="mailto:madhusudancs@gmail.com">Madhusudan.C.S</a>
 */

(function () {
  /** @lends melange.map */

  if (window.melange === undefined) {
    throw new Error("Melange not loaded");
  }

  var melange = window.melange;

  /** Package that handles all map buttons related functions
    * @name melange.map
    * @namespace melange.map
    * @borrows melange.logging.debugDecorator.log as log
    */
  melange.map = window.melange.map = function () {
    return new melange.map();
  };

  /** Shortcut to current package.
    * @private
    */
  var $m = melange.logging.debugDecorator(melange.map);

  melange.error.createErrors([
  ]);

  // Map load function
  $m.loadMap = function (map_div) {

    var center_latlng = new google.maps.LatLng(0, 0);
    var init_options = {
      zoom: 2,
      center: center_latlng,
      mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    var map = new google.maps.Map(document.getElementById(map_div),
        init_options);
  }

}());
