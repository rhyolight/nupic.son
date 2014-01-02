/* Copyright 2014 the Melange authors.
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
    jQuery("select, input:radio, input:file, input:checkbox").uniform();
    jQuery("#birth_date").datepicker({
      changeMonth: true,
      changeYear: true,
      dateFormat: "yy-mm-dd",
      showButtonPanel: true,
      minDate: "-90y",
      maxDate: "+0D",
      yearRange: "-90",
      defaultDate: '1990-01-01'
    });

    var shippingAddressElements = [
        ".shipping_name", ".shipping_street", ".shipping_city", ".shipping_province",
        ".shipping_country", ".shipping_postal_code"];

	// Initialize Shipping Address section
	jQuery("#is_shipping_address_different").each(function () {
	  if (this.checked) {
	    jQuery(shippingAddressElements.join(", ")).show(0); 
	  } else {
	    jQuery(shippingAddressElements.join(", ")).hide(0);
	  };
	});

	// Shipping Address related fields should be visible only when the checkbox is checked.
    jQuery("#is_shipping_address_different").change(function () {
	  if (this.checked) {
	    jQuery(shippingAddressElements.join(", ")).show(0); 
	  } else {
	    jQuery(shippingAddressElements.join(", ")).hide(0);
	    jQuery(shippingAddressElements.join(", ")).find("input, select").val("");
	    jQuery.uniform.update();
	  }
    });
  }
);
