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


# TODO(daniel): this class is on a non-specific level, but it refers
# to GCI specific names. Make it generic.
class TestLinker(unittest.TestCase):
  """Tests the Linker class."""

  def setUp(self):
    self.linker = links.Linker()

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
