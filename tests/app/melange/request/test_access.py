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

import httplib
import unittest

from nose.plugins import skip

from melange.request import access
from melange.request import exception

from soc.models import profile as profile_model
from soc.models import program as program_model
from soc.models import user as user_model
from soc.views.helper import request_data
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import timeline_utils


class Explosive(object):
  """Raises an exception on any attribute access."""

  def __getattribute__(self, attribute_name):
    raise ValueError()


class NoneAllowedAccessChecker(access.AccessChecker):
  """Tests only implementation of access checker that grants access to nobody
  and always raises exception.Forbidden error. The exception will contain
  identifier of particular instance of this class so that callers can recognize
  objects that raised the exception after all.
  """

  def __init__(self, identifier):
    """Initializes a new instance of the access checker.

    Args:
      identifier: a string that identifies this checker.
    """
    self._identifier = identifier

  def checkAccess(self, data, check, mutator):
    """See access.AccessChecker.checkAccess for specification."""
    raise exception.Forbidden(message=self._identifier)


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


class ConjuctionAccessCheckerTest(unittest.TestCase):
  """Tests for ConjuctionAccessChecker class."""

  def testForAllPassingCheckers(self):
    """Tests that checker passes if all sub-checkers pass."""
    checkers = [access.AllAllowedAccessChecker() for _ in xrange(5)]
    access_checker = access.ConjuctionAccessChecker(checkers)
    access_checker.checkAccess(None, None, None)

  def testFirstCheckerFails(self):
    """Tests that checker fails if the first sub-checker fails."""
    checkers = [NoneAllowedAccessChecker('first')]
    checkers.extend([access.AllAllowedAccessChecker() for _ in xrange(4)])
    access_checker = access.ConjuctionAccessChecker(checkers)
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(None, None, None)
    self.assertEqual(context.exception.message, 'first')

  def testLastCheckerFails(self):
    """Tests that checker fails if the last sub-checker fails."""
    checkers = [access.AllAllowedAccessChecker() for _ in xrange(4)]
    checkers.append(NoneAllowedAccessChecker('last'))
    access_checker = access.ConjuctionAccessChecker(checkers)
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(None, None, None)
    self.assertEqual(context.exception.message, 'last')


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


class ProgramActiveAccessCheckerTest(unittest.TestCase):
  """Tests for ProgramActiveAccessChecker class."""

  def setUp(self):
    """See unittest.setUp for specification."""
    self.program = seeder_logic.seed(program_model.Program)

  def testForNonExistingProgram(self):
    """Tests that access is denied if the program does not exist."""
    data = request_data.RequestData(None, None, None)
    data._program = None

    access_checker = access.ProgramActiveAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(data, None, None)
    self.assertEqual(context.exception.message,
        access._MESSAGE_PROGRAM_NOT_EXISTING)

  def testForNotActiveProgram(self):
    """Tests that access if denied if the program is not active."""
    data = request_data.RequestData(None, None, None)
    data._program = self.program
    data._timeline = request_data.TimelineHelper(self.program.timeline, None)

    access_checker = access.ProgramActiveAccessChecker()

    # the program is not visible
    data._program.status = program_model.STATUS_INVISIBLE
    data._program.timeline.program_start = timeline_utils.past()
    data._program.timeline.program_end = timeline_utils.future()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(data, None, None)
    self.assertEqual(context.exception.message,
        access._MESSAGE_PROGRAM_NOT_ACTIVE)

    # the program is has already ended
    data._program.status = program_model.STATUS_VISIBLE
    data._program.timeline.program_start = timeline_utils.past(delta=100)
    data._program.timeline.program_end = timeline_utils.past(delta=50)
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(data, None, None)
    self.assertEqual(context.exception.message,
        access._MESSAGE_PROGRAM_NOT_ACTIVE)

  def testForActiveProgram(self):
    """Tests that access is granted if the program is active."""

    data = request_data.RequestData(None, None, None)
    data._program = self.program
    data._timeline = request_data.TimelineHelper(self.program.timeline, None)

    access_checker = access.ProgramActiveAccessChecker()

    # program is active and visible
    data._program.status = program_model.STATUS_VISIBLE
    data._program.timeline.program_start = timeline_utils.past()
    data._program.timeline.program_end = timeline_utils.future()
    access_checker.checkAccess(data, None, None)


class IsUrlUserAccessCheckerTest(unittest.TestCase):
  """Tests for IsUrlUserAccessChecker class."""

  def setUp(self):
    """See unittest.setUp for specification."""
    self.data = request_data.RequestData(None, None, {})
    self.data._user = seeder_logic.seed(user_model.User)

  def testForMissingUserData(self):
    """Tests for URL data that does not contain any user data."""
    access_checker = access.IsUrlUserAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None, None)
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

  def testNonUserAccessDenied(self):
    """Tests that access is denied for a user with no User entity."""
    self.data.kwargs['user'] = self.data._user.link_id
    self.data._user = None
    access_checker = access.IsUrlUserAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testOtherUserAccessDenied(self):
    """Tests that access is denied for a user who is not defined in URL."""
    self.data.kwargs['user'] = 'other'
    access_checker = access.IsUrlUserAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testSameUserAccessGranted(self):
    """Tests that access is granted for a user who is defined in URL."""
    self.data.kwargs['user'] = self.data._user.link_id
    access_checker = access.IsUrlUserAccessChecker()
    access_checker.checkAccess(self.data, None, None)
