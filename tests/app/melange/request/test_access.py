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
from melange.request import exception

from soc.models import profile as profile_model
from soc.views.helper import request_data
from soc.modules.seeder.logic.seeder import logic as seeder_logic

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


class DeveloperAccessCheckerTest(unittest.TestCase):
  """Tests the DeveloperAccessChecker class."""

  def testDeveloperAccessAllowed(self):
    data = request_data.RequestData(None, None, None)
    # TODO(nathaniel): Reaching around RequestHandler public API.
    data._is_developer = True

    access_checker = access.DeveloperAccessChecker()
    access_checker.checkAccess(data, None, None)

  def testNonDeveloperAccessDenied(self):
    data = request_data.RequestData(None, None, None)
    # TODO(nathaniel): Reaching around RequestHandler public API.
    data._is_developer = False

    access_checker = access.DeveloperAccessChecker()
    with self.assertRaises(exception.UserError):
      access_checker.checkAccess(data, None, None)


class NonStudentAccessCheckerTest(unittest.TestCase):
  """Tests for NonStudentAccessChecker class."""

  def setUp(self):
    """See unittest.setUp for specification."""
    # seed a profile
    profile_properties = {'status': 'active'}
    self.profile = seeder_logic.seed(profile_model.Profile, profile_properties)

  def testUserWithNoLoggedInAccessDenied(self):
    """Tests that access is denied for a user that is not logged in."""
    data = request_data.RequestData(None, None, None)
    data._gae_user = None

    access_checker = access.NonStudentAccessChecker()
    with self.assertRaises(exception.LoginRequired):
      access_checker.checkAccess(data, None, None)

  def testUserWithNoProfileAccessDenied(self):
    """Tests that access is denied for a user that does not have a profile."""
    data = request_data.RequestData(None, None, None)
    data._gae_user = 'unused'
    data._profile = None

    access_checker = access.NonStudentAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(data, None, None)
    self.assertEqual(context.exception.message, access._MESSAGE_NO_PROFILE)

  def testStudentAccessDenied(self):
    """Tests that access is denied for a user with a student profile."""
    self.profile.is_student = True

    data = request_data.RequestData(None, None, None)
    data._gae_user = 'unused'
    data._profile = self.profile

    access_checker = access.NonStudentAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(data, None, None)
    self.assertEqual(context.exception.message,
        access._MESSAGE_STUDENTS_DENIED)

  def testNonStudentAccessGranted(self):
    """Tests that access is granted for users with non-student accounts."""
    self.profile.is_student = False

    data = request_data.RequestData(None, None, None)
    data._gae_user = 'unused'
    data._profile = self.profile

    access_checker = access.NonStudentAccessChecker()
    access_checker.checkAccess(data, None, None)
