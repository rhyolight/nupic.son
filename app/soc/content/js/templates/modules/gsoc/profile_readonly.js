/* Copyright 2009 the Melange authors.
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
 * @author <a href="mailto:admin@gedex.web.id">Akeda Bagus</a>
 */

melange.templates.inherit(
  function (_self, context) {
    // Create global variables
    var css_prefix = "profile_show";
  
    // Id of the element which the map will be appended after.
    var append_to = "#gsoc_" + css_prefix + "-contact-info-private";

    var map_div = "profile_map";

    var field_lat = "#latitude";
    var field_lng = "#longitude";
  
    var lat = 0;
    var lng = 0;

    var map_zoom = 13;
  
    // Public function to load the map
    function map_load() {
      var init_map_options = {
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        mapTypeControl: true,
        panControl: true,
        zoomControl: true
      };
  
      // Create the map and pass initialization
      var map = new google.maps.Map(jQuery("#" + map_div)[0], init_map_options);
  
      // Set map center and marker coords
      var marker_position = new google.maps.LatLng(lat, lng);
      map.setZoom(map_zoom);
      map.setCenter(marker_position);
      marker = new google.maps.Marker({position: marker_position, draggable: false});
      marker.setMap(map);
    }
  
    jQuery(
      function () {
        lat = jQuery(field_lat).text();
        lng = jQuery(field_lng).text();
        // If lat and lng fields are not set, then don't show the map at all
        if (lat !== "" && lng !== "") {
          jQuery(append_to).append("<div id='" + map_div + "' style=\"width: 100%\"></div>");
          melange.loadGoogleApi("maps", "3", {other_params: "sensor=false"}, map_load);
        }
      }
    );
  }
);
