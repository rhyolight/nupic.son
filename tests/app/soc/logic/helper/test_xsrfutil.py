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

"""Tests for soc.logic.helper.xsrfutil."""

import time
import unittest

from soc.logic.helper import xsrfutil

class XsrfUtilTest(unittest.TestCase):
  """Tests for XsrfUtil functions."""

  def setUp(self):
    self.user_id = '42'
    self.secret_key = 'secret_key'
    self.valid_token = xsrfutil._generateToken(self.secret_key, self.user_id,
                                               when=int(time.time()))

  def testValidateToken(self):
    """Test the validate token function."""
    # No token.
    self.assertRaises(xsrfutil.InvalidTokenException, xsrfutil._validateToken,
                      self.secret_key, '', self.user_id)

    # Not a base64 decodeable token.
    self.assertRaises(xsrfutil.InvalidTokenException, xsrfutil._validateToken,
                      self.secret_key, 'QNotBase64', self.user_id)

    # Not a well-formed token
    self.assertRaises(xsrfutil.InvalidTokenException, xsrfutil._validateToken,
                      self.secret_key, 'a123', self.user_id)

    # An out of date token, generated at epoch
    old_token = xsrfutil._generateToken(self.secret_key, self.user_id, when=1)
    self.assertRaises(xsrfutil.InvalidTokenException, xsrfutil._validateToken,
                      self.secret_key, old_token, self.user_id)

    # A valid token issued for another user.
    self.assertRaises(xsrfutil.InvalidTokenException, xsrfutil._validateToken,
                      self.secret_key, self.valid_token, 'SomeOtherUserId')

    # A valid token.
    xsrfutil._validateToken(self.secret_key, self.valid_token, self.user_id)
