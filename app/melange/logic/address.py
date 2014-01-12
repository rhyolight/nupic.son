# Copyright 2013 the Melange authors.
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

"""Logic for addresses."""

from google.appengine.api import datastore_errors

from melange.models import address as address_model
from melange.utils import rich_bool


def createAddress(street, city, country, postal_code, province=None, name=None):
  """Creates a new address based on the specified properties.

  Args:
    street: Street information.
    city: City information.
    country: Country information.
    postal_code: Postal code information.
    province: Province (or state) information.
    name: Name of a specific person associated with the address.

  Returns:
    RichBool whose value is set to True if an address entity has been
    successfully created. In that case, extra part points to the newly created
    object. Otherwise, RichBool whose value is set to False and extra part is
    a string that represents the reason why the action could not be completed.
  """
  try:
    return rich_bool.RichBool(True, address_model.Address(
        name=name, street=street, city=city, province=province, country=country,
        postal_code=postal_code))
  except datastore_errors.BadValueError as e:
    return rich_bool.RichBool(False, str(e))
