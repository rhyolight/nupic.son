# Copyright 2012 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module that contains utility functions associated with addresses.
"""

def addAddressColumns(list_config):
  """Adds address columns to the specified list config.

  Columns added:
    * residential_street
    * residential_city
    * residential_province
    * residential_postal_code
    * residential_country
    * phone_number
    * ship_to_name
    * ship_to_street
    * ship_to_city
    * ship_to_province
    * ship_to_postal_code
    * ship_to_country
    * tshirt_style
    * tshirt_size
  """
  list_config.addPlainTextColumn(
      'residential_street', 'Residential Street',
      lambda entity, *args: entity.residential_address.street, hidden=True)
  list_config.addPlainTextColumn(
      'residential_city', 'Residential City',
      lambda entity, *args: entity.residential_address.street, hidden=True)
  list_config.addPlainTextColumn(
      'residential_province', 'Residential State/Province',
      lambda entity, *args: entity.residential_address.province, hidden=True)
  list_config.addPlainTextColumn(
      'residential_postal_code', 'Residential Postal Code',
      lambda entity, *args: entity.residential_address.postal_code, hidden=True)
  list_config.addPlainTextColumn(
      'residential_country', 'Residential Country',
      lambda entity, *args: entity.residential_address.country, hidden=True)
  list_config.addPlainTextColumn(
      'phone_number', 'Phone Number',
      lambda entity, *args: entity.contact.phone, hidden=True)
  list_config.addPlainTextColumn(
      'ship_to_name', 'Ship To Name',
      lambda entity, *args: entity.ship_to_address.name, hidden=True)
  list_config.addPlainTextColumn(
      'ship_to_street', 'Ship To Street',
      lambda entity, *args: entity.ship_to_address.street, hidden=True)
  list_config.addPlainTextColumn(
      'ship_to_city', 'Ship To City',
      lambda entity, *args: entity.ship_to_address.city, hidden=True)
  list_config.addPlainTextColumn(
      'ship_to_province', 'Ship To State/Province',
      lambda entity, *args: entity.ship_to_address.province, hidden=True)
  list_config.addPlainTextColumn(
      'ship_to_postal_code', 'Ship To Postal Code',
      lambda entity, *args: entity.ship_to_address.postal_code, hidden=True)
  list_config.addPlainTextColumn(
      'ship_to_country', 'Ship To Country',
      lambda entity, *args: entity.ship_to_address.country, hidden=True)
