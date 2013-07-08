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

"""Tests for melange.request.access."""

import unittest

from nose.plugins import skip

from melange.request import access


class Explosive(object):
  """Raises an exception on any attribute access."""

  def __getattribute__(self, attribute_name):
    raise ValueError()


class AllAllowedAccessCheckerTest(unittest.TestCase):
  """Tests the AllAllowedAccessChecker class."""

  def testAccessAllowedWithPhonyInputs(self):
    """Tests that access is allowed without examining inputs."""
    access_checker = access.AllAllowedAccessChecker()
    access_checker.checkAccess(Explosive(), Explosive(), Explosive())


# TODO(nathaniel): Because the idea of RequestData objects having
# an "is_host" attribute isn't unified across all program types
# (it is actually separately implemented in GCI's and GSoC's
# individual RequestData subclasses) this text can't be written
# without either bringing in GCI-specific or GSoC-specific code
# or faking out too much.
class ProgramAdministratorAccessCheckerTest(unittest.TestCase):
  """Tests the ProgramAdministratorAccessChecker class."""

  def testProgramAdministratorsAllowedAccess(self):
    """Tests that a program administrator is allowed access."""
    raise skip.SkipTest()

  def testOrganizationAdministratorsDeniedAccess(self):
    """Tests that an organization administrator is denied access."""
    raise skip.SkipTest()

  def testMentorDeniedAccess(self):
    """Tests that a mentor is denied access."""
    raise skip.SkipTest()

  def testStudentDeniedAccess(self):
    """Tests that students are denied access."""
    raise skip.SkipTest()

  def testAnonymousDeniedAccess(self):
    """Tests that logged-out users are denied access."""
    raise skip.SkipTest()
