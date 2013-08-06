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


"""Tests for soc.logic.mapreduce_convert_user.
"""


import os
import unittest

from google.appengine.api import users
from google.appengine.ext import db

from soc.models.user import User
from soc.mapreduce import convert_user
from soc.modules.seeder.logic.seeder import logic as seeder_logic
from soc.modules.seeder.logic.providers import string as seeder_string


class TestAccounts(unittest.TestCase):
  """Tests for convert_user logic.
  """
  def setUp(self):
    self.link_id = seeder_string.LinkIDProvider(User).getValue()

  def convert(self, email, same_user_id=False):
    account = users.User(email=email)
    properties = {
        'account': account,
        'key_name': self.link_id,
        'link_id': self.link_id,
        'name': 'Test user',
        'status': 'valid',
    }
    user = seeder_logic.seed(User, properties)
    if same_user_id:
      user = User.get_by_key_name(self.link_id)
      user.user_id = user.account.user_id()
      user.put()
    return convert_user.convert_user_txn(user.key())

  def assertUserEqual(self, email):
    user = User.get_by_key_name(self.link_id)
    self.assertEqual(email, user.account.email())
    self.assertTrue(user.account.user_id())
    self.assertEqual(user.account.user_id(), user.user_id)

  def testNoop(self):
    result = self.convert('test@example.com', True)
    self.assertEqual(convert_user.IGNORED_USER, result)
    self.assertUserEqual('test@example.com')

  def testConverted(self):
    result = self.convert('test@gmail.com', True)
    self.assertEqual(convert_user.IGNORED_USER, result)
    self.assertUserEqual('test@gmail.com')

  def testPartiallyConverted(self):
    result = self.convert('test@gmail.com')
    self.assertEqual(convert_user.CONVERTED_USER, result)
    self.assertUserEqual('test@gmail.com')

  def testNonAuthConverted(self):
    result = self.convert('test@example.com')
    self.assertEqual(convert_user.CONVERTED_USER, result)
    self.assertUserEqual('test@example.com')

  def testFullConversion(self):
    result = self.convert('test')
    self.assertEqual(convert_user.CONVERTED_USER, result)
    self.assertUserEqual('test@gmail.com')
