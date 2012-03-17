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
 * @author <a href="mailto:fadinlight@gmail.com">Mario Ferraro</a>
 */

melange.templates.inherit(
  function (_self, context) {
 
    // Create global variables
    var map;
    var marker;
    var geocoder;

    var current_lat = 0;
    var current_lng = 0;

    // Different levels of zoom dependent on which fields are filled
    var world_zoom = 1;
    var country_zoom = 4;
    var state_zoom = 6;
    var city_zoom = 10;
    var address_zoom = 14;

    // The following strings can be customized to reflect ids in the page.
    // You can also add or remove fields used for GMap Geocoding in
    // the JSON address object

    var map_div = "profile_map";

    // Id of the element which the map will be appended after.
    var append_to = "#form_row_publish_location";

    var field_lat = "#latitude";
    var field_lng = "#longitude";

    // Need to save old values to avoid unwanted updating 
    // of lat and lon if marker dragged and blur another time an address field
    var address = {
      street: {
        id: "#res_street",
        old_value: ""
      },
      city: {
        id: "#res_city",
        old_value: ""
      },
      state: {
        id: "#res_state",
        old_value: ""
      },
      country: {
        id: "#res_country",
        old_value: ""
      },
      postalcode: {
        id: "#res_postalcode",
        old_value: ""
      }
    };

    // Save current address fields in the JSON Object
    function saveOldAddress() {
      jQuery.each(address, function (level, level_details) {
        level_details.old_value = jQuery(level_details.id).val();
      });
    }

    // Return true if the user has edited address fields
    function isNewAddress() {
      var is_new = false;
      jQuery.each(address, function (level, level_details) {
        if (jQuery(level_details.id).val() !== level_details.old_value) {
          is_new = true;
          return false;
        }
      });
      return is_new;
    }

    // Write saved lat and lng values to page fields
    function setLatLngFields() {
      jQuery(field_lat).val(current_lat);
      jQuery(field_lng).val(current_lng);
    }

    // Read lat and lng fields and store them
    function readLatLngFields() {
      current_lat = jQuery(field_lat).val();
      current_lng = jQuery(field_lng).val();
    }

    // This function reads address fields, merge them and uses
    // GMap API geocoding to find the first hit
    // Using geocoding
    function calculateAddress() {
      // If the user has really edited address fields...
      if (isNewAddress()) {
        // Merge address fields
        var address_string = "";
        jQuery.each(address, function (level, level_details) {
          address_string += jQuery(level_details.id).val() + ",";
        });
  
        // Ask GMap API for geocoding
        geocoder.geocode(
          {
            address: address_string
          },
          function (geocoder_result, geocoder_status) {
            // If the geocoding has been successful
            if (geocoder_status === google.maps.GeocoderStatus.OK) {
              var point = geocoder_result[0].geometry.location;
              // Save the current address in the JSON object
              saveOldAddress();
              // Set the new zoom, map center and marker coords
              var zoom_set = world_zoom;
              if (jQuery(address.street.id).val() !== "") {
                zoom_set = address_zoom;
              }
              else if (jQuery(address.city.id).val() !== "") {
                zoom_set = city_zoom;
              }
              else if (jQuery(address.state.id).val() !== "") {
                zoom_set = state_zoom;
              }
              else if (jQuery(address.country.id).val() !== "") {
                zoom_set = country_zoom;
              }
              map.setZoom(zoom_set);
              map.setCenter(point);
              marker.setPosition(point);
              // Save point coords in local variables and then update 
              // the page lat/lng fields
              current_lat = point.lat();
              current_lng = point.lng();
              setLatLngFields();
            }
          }
        );
      }
    }
  
    // Public function to load the map
    function map_load() {
      // Save the address fields. This is useful if the page is being edited
      // to not update blindly the lat/lng fields with GMap geocoding if
      // blurring an address field
      saveOldAddress();
      var starting_point;
      var zoom_selected = world_zoom;
      var show_marker = true;

      var init_map_options = {
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        mapTypeControl: true,
        panControl: true,
        zoomControl: true
      };
  
      // Create the map
      map = new google.maps.Map(jQuery("#" + map_div)[0], init_map_options);
  
      // Instantiate a global geocoder for future use
      geocoder = new google.maps.Geocoder();
  
      // If lat and lng fields are not empty (the page is being edited) then
      // update the starting coords, modify the zoom level and tells following
      // code to show the marker
      if (jQuery(field_lat).val() !== "" && jQuery(field_lng).val() !== "") {
        readLatLngFields();
        zoom_selected = address_zoom;
        show_marker = true;
      }
  
      // Set map center, marker coords and show it if this is an editing
      starting_point = new google.maps.LatLng(current_lat, current_lng);
      map.setZoom(zoom_selected);
      map.setCenter(starting_point);

      marker = new google.maps.Marker({position: starting_point, draggable: true});
      if (show_marker) {
        marker.setMap(map);
      }
  
      // Adds a new event listener to geocode the address when an address
      // field is blurred
      jQuery.each(address, function (level, level_details) {
        jQuery(level_details.id).blur(calculateAddress);
      });
  
      // Adds a new event listener: if the marker has been dragged around...
      google.maps.event.addListener(marker, "dragend", function () {
        // Update internal variables with current marker coords...
        current_lat = marker.getPosition().lat();
        current_lng = marker.getPosition().lng();
        // ...and set page fields accordingly
        setLatLngFields();
      });
    }
  
    jQuery(
      function () {
        jQuery(append_to).append("<div id='" + map_div + "'></div>");
        melange.loadGoogleApi("maps", "3", {other_params: "sensor=false"}, map_load);
      }
    );
  }
);
