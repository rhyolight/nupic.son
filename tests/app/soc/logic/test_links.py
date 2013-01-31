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

TEST_PROGRAM_SPONSOR = 'test_sponsor'
TEST_PROGRAM_NAME = 'test_program'


# TODO(nathaniel): use a real program here.
class MockProgram(object):
  scope_path = TEST_PROGRAM_SPONSOR
  link_id = TEST_PROGRAM_NAME


class TestLinker(unittest.TestCase):
  """Tests the Linker class."""

  def setUp(self):
    self.linker = links.Linker()

  def testProgram(self):
    self.assertEqual(
        '/gci/homepage/%s/%s' % (TEST_PROGRAM_SPONSOR, TEST_PROGRAM_NAME),
        self.linker.program(MockProgram(), 'gci_homepage'))
