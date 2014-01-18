/*
 * Copyright 2014 the Melange authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */
melange.templates.inherit(
  function (_self, context) {
    jQuery(
      function () {
        melange.loadGoogleApi("picker", "1", {}, createPicker);
      }
    );

    // Create a Picker object for searching images.
    function createPicker() {
      var picker = new google.picker.PickerBuilder().
          addView(google.picker.ViewId.SPREADSHEETS).
          enableFeature(google.picker.Feature.NAV_HIDDEN).
          setDeveloperKey(context.developer_key).
          setAppId(context.client_id).
          setOAuthToken(context.access_token).
          setCallback(pickerCallback).
          build();
      jQuery("#spreadsheet_id").click(function() {
          picker.setVisible(true);
      })
    }

    // A simple callback implementation.
    function pickerCallback(data) {
      if (data[google.picker.Response.ACTION] == google.picker.Action.PICKED) {
        var doc = data[google.picker.Response.DOCUMENTS][0];
        document_id = doc[google.picker.Document.ID];
        jQuery('#spreadsheet_id').val(document_id);
      }
    }
  }
);
