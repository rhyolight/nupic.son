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

"""Tests for address logic."""

import unittest

from melange.logic import address as address_logic


TEST_NAME = 'Test name'
TEST_STREET = 'Test street'
TEST_STREET_EXTRA = 'Test street extra'
TEST_CITY = 'Test city'
TEST_PROVINCE = 'CA'
TEST_COUNTRY = 'United States'
TEST_POSTAL_CODE = '90000'

class CreateAddressTest(unittest.TestCase):
  """Unit tests for createAddress function."""

  def testValidData(self):
    """Tests that address entity is created properly if all data is valid."""
    result = address_logic.createAddress(
        TEST_STREET, TEST_CITY, TEST_COUNTRY, TEST_POSTAL_CODE,
        province=TEST_PROVINCE, name=TEST_NAME, street_extra=TEST_STREET_EXTRA)
    self.assertTrue(result)

    address = result.extra
    self.assertEqual(address.name, TEST_NAME)
    self.assertEqual(address.street, TEST_STREET)
    self.assertEqual(address.street_extra, TEST_STREET_EXTRA)
    self.assertEqual(address.city, TEST_CITY)
    self.assertEqual(address.province, TEST_PROVINCE)
    self.assertEqual(address.country, TEST_COUNTRY)
    self.assertEqual(address.postal_code, TEST_POSTAL_CODE)

  def testInvalidData(self):
    """Tests that address entity is not created if data is not valid."""
    # non-existing country
    result = address_logic.createAddress(
        TEST_STREET, TEST_CITY, 'Neverland', TEST_POSTAL_CODE)
    self.assertFalse(result)

