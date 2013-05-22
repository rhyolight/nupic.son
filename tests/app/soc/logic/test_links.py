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

"""Tests of soc.logic.linker."""

import unittest
import urllib

from soc.logic import links

TEST_PROGRAM_NAME = 'test_program'
TEST_SPONSOR_KEY_NAME = 'test_sponsor_key_name'


class MockKey(object):

  def __init__(self, name):
    self._name = name

  def name(self):
    return self._name


class MockSponsor(object):
  def key(self):
    return MockKey(TEST_SPONSOR_KEY_NAME)


# TODO(nathaniel): use a real program here.
class MockProgram(object):
  scope = MockSponsor()
  link_id = TEST_PROGRAM_NAME


class _PathOnlyMockHttpRequest(object):
  """A mock HttpRequest supporting only the get_full_path method.

  Why Django doesn't provide an instantiable HttpRequest
  implementation is completely beyond me.
  """

  def __init__(self, path):
    """Creates a _PathOnlyMockHttpRequest.

    Args:
      path: Any string intended to represent the path portion of
        a requested URL.
    """
    self._path = path

  def get_full_path(self):
    """See http.HttpRequest.get_full_path for specification."""
    return self._path


# TODO(daniel): this class is on a non-specific level, but it refers
# to GCI specific names. Make it generic.
class TestLinker(unittest.TestCase):
  """Tests the Linker class."""

  def setUp(self):
    self.linker = links.Linker()

  def testLogin(self):
    """Tests that some reasonable value is created by Linker.login."""
    test_path = '/a/fake/test/path'
    # NOTE(nathaniel): The request parameter and value are just here
    # for coverage; I don't actually have sufficient familiarity with
    # them to assert that their quoting and escaping are completely
    # correct.
    test_arg = 'some_test_arg'
    test_arg_value = 'some_test_value'

    request = _PathOnlyMockHttpRequest(
        '%s?%s=%s' % (test_path, test_arg, test_arg_value))
    login_url = self.linker.login(request)
    self.assertIn(test_path, login_url)
    self.assertIn(
        urllib.quote('%s=%s' % (test_arg, test_arg_value)), login_url)

  def testLogout(self):
    """Tests that some reasonable value is created by Linker.logout."""
    test_path = 'a/fake/test/path/to/visit/after/logout'
    request = _PathOnlyMockHttpRequest(test_path)
    logout_path = self.linker.logout(request)
    self.assertIn(test_path, logout_path)

  def testSite(self):
    self.assertEqual('/site/edit', self.linker.site('edit_site_settings'))

  def testProgram(self):
    self.assertEqual(
        '/gci/homepage/%s/%s' % (TEST_SPONSOR_KEY_NAME, TEST_PROGRAM_NAME),
        self.linker.program(MockProgram(), 'gci_homepage'))

  def testSponsor(self):
    self.assertEqual(
        '/gci/program/create/%s' % TEST_SPONSOR_KEY_NAME,
        self.linker.sponsor(MockSponsor(), 'gci_program_create'))
