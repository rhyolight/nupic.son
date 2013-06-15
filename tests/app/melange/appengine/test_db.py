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

"""Tests for melange.appengine.db."""

import unittest

from melange.appengine import db


class EmailValidatorTest(unittest.TestCase):
  """Unit tests for email_validator function.

  The class contains only very simple test cases to demonstrate that the
  tested function throws an exception on invalid input and returns normally
  otherwise.

  The reason is that email_validator function simply uses a thirdparty
  validator to do the actual job. It is assumed that it works correctly.
  """

  def testValidEmail(self):
    """Tests that the function returns normally on a valid email."""
    db.email_validator(None, 'test@example.com')

  def testInvalidEmail(self):
    """Tests that the function returns ValueError on an invalid email."""
    with self.assertRaises(ValueError):
      db.email_validator(None, 'invalid_email_address')


class UrlValidatorTest(unittest.TestCase):
  """Unit tests for url_validator function.

  The class contains only very simple test cases to demonstrate that the
  tested function throws an exception on invalid input and returns normally
  otherwise.

  The reason is that url_validator function simply uses a thirdparty
  validator to do the actual job. It is assumed that it works correctly.
  """

  def testValidUrl(self):
    """Tests that the function returns normally on a valid URL."""
    db.url_validator(None, 'http://www.melange.com')

  def testInvalidEmail(self):
    """Tests that the function returns ValueError on an invalid URL."""
    with self.assertRaises(ValueError):
      db.url_validator(None, 'invalid_url_address')

  