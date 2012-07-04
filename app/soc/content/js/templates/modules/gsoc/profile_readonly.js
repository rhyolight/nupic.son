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
    var css_prefix = "profile_show";
  
    // Create global variables
    var map;
    var marker;
  
    // The following strings can be customized to reflect ids in the page.
    // You can also add or remove fields used for GMap Geocoding in 
    // the JSON address object
  
    var current_lat = 0;
    var current_lng = 0;
  
    // Two different levels for zoom: Starting one and an inner that 
    // is used when showing the map if lat and lon page fields are set
    var world_zoom = 1;
    var address_zoom = 13;
  
    var map_div = "profile_map";
  
    // Id of the element which the map will be appended after.
    var append_to = "#gsoc_" + css_prefix + "-contact-info-private";
  
    var field_lat = "#latitude";
    var field_lng = "#longitude";
  
    // Read lat and lng fields and store them
    function readLatLngFields() {
      current_lat = jQuery(field_lat).text();
      current_lng = jQuery(field_lng).text();
    }
  
    // Public function to load the map
    function map_load() {
      var init_map_options = {
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        mapTypeControl: true,
        panControl: true,
        zoomControl: true
      };
      var starting_point;
      var zoom_selected = world_zoom;
      var show_marker = false;
  
      // Create the map and pass initialization
      map = new google.maps.Map(jQuery("#" + map_div)[0], init_map_options);
  
      // If lat and lng fields are not empty then
      // do not show the marker
      if (jQuery(field_lat).text() !== "" && jQuery(field_lng).text() !== "") {
        readLatLngFields();
        zoom_selected = address_zoom;
        show_marker = true;
      }
  
      // Set map center, marker coords if present
      starting_point = new google.maps.LatLng(current_lat, current_lng);
      map.setZoom(zoom_selected);
      map.setCenter(starting_point);
      marker = new google.maps.Marker({position: starting_point, draggable: false});
      if (show_marker) {
        marker.setMap(map);
      }
    }
  
    jQuery(
      function () {
        jQuery(append_to).append("<div id='" + map_div + "' style=\"width: 100%\"></div>");
        melange.loadGoogleApi("maps", "3", {other_params: "sensor=false"}, map_load);
      }
    );
  }
);
