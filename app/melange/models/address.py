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

"""This module contains a model that stores an address."""

from google.appengine.ext import ndb

from melange.utils import countries


class Address(ndb.Model):
  """Model to store address information."""

  #: Optional name information to link a specific person to this address.
  #: Can only be ASCII, not UTF-8 text, because it may be used as
  #: a shipping address and such characters may not be printable.
  name = ndb.StringProperty()

  #: Required field containing street information. Can only be ASCII,
  #: not UTF-8 text, because it may be used as a shipping address
  #: and such characters may not be printable.
  street = ndb.StringProperty(requred=True)

  #: Required field containing city information. Can only be ASCII,
  #: not UTF-8 text, because it may be used as a shipping address and
  #: such characters may not be printable.
  city = ndb.StringProperty(required=True)

  #: Optional field containing province or state information. It is used only
  #: for certain countries. Can only be ASCII, not UTF-8 text, because
  #: it may be used as a shipping address and such characters
  #: may not be printable.
  province = ndb.StringProperty()

  #: Required field containing residence country or territory information.
  #: Can only be ASCII, not UTF-8 text, because it may be used as
  #: a shipping address and such characters may not be printable.
  country = ndb.StringProperty(
      required=True, choices=countries.COUNTRIES_AND_TERRITORIES)

  #: Required field containing residence postal code, also known as ZIP code
  #: in some countries, information.Can only be ASCII, not UTF-8 text, because
  #: it may be used as a shipping address and
  #: such characters may not be printable.
  postal_code = ndb.StringProperty(required=True)
