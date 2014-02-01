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

from google.appengine.ext import ndb

from django import http

from melange.models import profile as ndb_profile_model
from melange.request import access
from melange.request import exception

from soc.models import organization as org_model
from soc.models import profile as profile_model
from soc.models import program as program_model
from soc.views.helper import request_data
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import org_utils
from tests import profile_utils
from tests import program_utils
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

  def checkAccess(self, data, check):
    """See access.AccessChecker.checkAccess for specification."""
    raise exception.Forbidden(message=self._identifier)


class EnsureLoggedInTest(unittest.TestCase):
  """Unit tests for ensureLoggedIn function."""

  def testForLoggedInUser(self):
    """Tests that no exception is raised for a logged-in user."""
    data = request_data.RequestData(None, None, {})
    data._gae_user = 'unused'
    access.ensureLoggedIn(data)

  def testForLoggedOutUser(self):
    """Tests that exception is raised for a non logged-in user."""
    data = request_data.RequestData(None, None, {})
    data._gae_user = None
    with self.assertRaises(exception.LoginRequired):
      access.ensureLoggedIn(data)


class EnsureLoggedOutTest(unittest.TestCase):
  """Unit tests for ensureLoggedOut function."""

  def testForLoggedInUser(self):
    """Tests that exception is raised for a logged-in user."""
    data = request_data.RequestData(http.HttpRequest(), None, {})
    data._gae_user = 'unused'
    with self.assertRaises(exception.Redirect):
      access.ensureLoggedOut(data)

  def testForLoggedOutUser(self):
    """Tests that no exception is raised for a non logged-in user."""
    data = request_data.RequestData(http.HttpRequest(), None, {})
    data._gae_user = None
    access.ensureLoggedOut(data)


class AllAllowedAccessCheckerTest(unittest.TestCase):
  """Tests the AllAllowedAccessChecker class."""

  def testAccessAllowedWithPhonyInputs(self):
    """Tests that access is allowed without examining inputs."""
    access_checker = access.AllAllowedAccessChecker()
    access_checker.checkAccess(Explosive(), Explosive())


class ProgramAdministratorAccessCheckerTest(unittest.TestCase):
  """Tests the ProgramAdministratorAccessChecker class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.sponsor = program_utils.seedSponsor()
    self.program = program_utils.seedProgram(sponsor_key=self.sponsor.key())

    # seed a user who will be tested for access
    self.user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(self.user)

    kwargs = {
        'sponsor': self.sponsor.key().name(),
        'program': self.program.program_id,
        }
    self.data = request_data.RequestData(None, None, kwargs)

  def testProgramAdministratorsAllowedAccess(self):
    """Tests that a program administrator is allowed access."""
    # make the user a program administrator
    self.user.host_for = [ndb.Key.from_old_key(self.program.key())]
    self.user.put()

    access_checker = access.ProgramAdministratorAccessChecker()
    access_checker.checkAccess(self.data, None)

  def testOrganizationAdministratorsDeniedAccess(self):
    """Tests that an organization administrator is denied access."""
    # seed a profile who is an organization admin
    org = org_utils.seedOrganization(self.program.key())
    profile_utils.seedNDBProfile(
        self.program.key(), user=self.user, admin_for=[org.key])

    access_checker = access.ProgramAdministratorAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.message,
        access._MESSAGE_NOT_PROGRAM_ADMINISTRATOR)

  def testMentorDeniedAccess(self):
    """Tests that a mentor is denied access."""
    # seed a profile who is a mentor
    org = org_utils.seedOrganization(self.program.key())
    profile_utils.seedNDBProfile(
        self.program.key(), user=self.user, mentor_for=[org.key])

    access_checker = access.ProgramAdministratorAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.message,
        access._MESSAGE_NOT_PROGRAM_ADMINISTRATOR)

  def testStudentDeniedAccess(self):
    """Tests that students are denied access."""
    # seed a profile who is a student
    profile_utils.seedNDBStudent(self.program, user=self.user)

    access_checker = access.ProgramAdministratorAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.message,
        access._MESSAGE_NOT_PROGRAM_ADMINISTRATOR)

  def testAnonymousDeniedAccess(self):
    """Tests that logged-out users are denied access."""
    access_checker = access.ProgramAdministratorAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.message,
        access._MESSAGE_NOT_PROGRAM_ADMINISTRATOR)


class DeveloperAccessCheckerTest(unittest.TestCase):
  """Tests the DeveloperAccessChecker class."""

  def testDeveloperAccessAllowed(self):
    data = request_data.RequestData(None, None, None)
    # TODO(nathaniel): Reaching around RequestHandler public API.
    data._is_developer = True

    access_checker = access.DeveloperAccessChecker()
    access_checker.checkAccess(data, None)

  def testNonDeveloperAccessDenied(self):
    data = request_data.RequestData(None, None, None)
    # TODO(nathaniel): Reaching around RequestHandler public API.
    data._is_developer = False

    access_checker = access.DeveloperAccessChecker()
    with self.assertRaises(exception.UserError):
      access_checker.checkAccess(data, None)


class ConjuctionAccessCheckerTest(unittest.TestCase):
  """Tests for ConjuctionAccessChecker class."""

  def testForAllPassingCheckers(self):
    """Tests that checker passes if all sub-checkers pass."""
    checkers = [access.AllAllowedAccessChecker() for _ in xrange(5)]
    access_checker = access.ConjuctionAccessChecker(checkers)
    access_checker.checkAccess(None, None)

  def testFirstCheckerFails(self):
    """Tests that checker fails if the first sub-checker fails."""
    checkers = [NoneAllowedAccessChecker('first')]
    checkers.extend([access.AllAllowedAccessChecker() for _ in xrange(4)])
    access_checker = access.ConjuctionAccessChecker(checkers)
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(None, None)
    self.assertEqual(context.exception.message, 'first')

  def testLastCheckerFails(self):
    """Tests that checker fails if the last sub-checker fails."""
    checkers = [access.AllAllowedAccessChecker() for _ in xrange(4)]
    checkers.append(NoneAllowedAccessChecker('last'))
    access_checker = access.ConjuctionAccessChecker(checkers)
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(None, None)
    self.assertEqual(context.exception.message, 'last')


class NonStudentUrlProfileAccessCheckerTest(unittest.TestCase):
  """Tests for NonStudentUrlProfileAccessChecker class."""

  def setUp(self):
    """See unittest.setUp for specification."""
    sponsor = program_utils.seedSponsor()
    self.program = program_utils.seedProgram(sponsor_key=sponsor.key())

    self.kwargs = {
        'sponsor': sponsor.key().name(),
        'program': self.program.program_id,
        }

  def testUrlUserWithNoProfileAccessDenied(self):
    """Tests that access is denied for a user that does not have a profile."""
    self.kwargs['user'] = 'non_existing_user'
    data = request_data.RequestData(None, None, self.kwargs)

    access_checker = access.NonStudentUrlProfileAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(data, None)
    self.assertEqual(context.exception.status, httplib.NOT_FOUND)

  def testStudentAccessDenied(self):
    """Tests that access is denied for a user with a student profile."""
    # additionally, seed a profile who is not a student
    # access should be still denied as the check corresponds to URL profile
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    # seed URL profile who is a student
    url_profile = profile_utils.seedNDBStudent(self.program)
    self.kwargs['user'] = url_profile.profile_id
    data = request_data.RequestData(None, None, self.kwargs)

    access_checker = access.NonStudentUrlProfileAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(data, None)
    self.assertEqual(context.exception.message,
        access._MESSAGE_STUDENTS_DENIED)

  def testNonStudentAccessGranted(self):
    """Tests that access is granted for users with non-student accounts."""
    # seed URL profile who is not a student
    url_profile = profile_utils.seedNDBProfile(self.program.key())
    self.kwargs['user'] = url_profile.profile_id
    data = request_data.RequestData(None, None, self.kwargs)

    access_checker = access.NonStudentUrlProfileAccessChecker()
    access_checker.checkAccess(data, None)


class NonStudentProfileAccessCheckerTest(unittest.TestCase):
  """Tests for NonStudentProfileAccessChecker class."""

  def setUp(self):
    """See unittest.setUp for specification."""
    sponsor = program_utils.seedSponsor()
    self.program = program_utils.seedProgram(sponsor_key=sponsor.key())

    kwargs = {
        'sponsor': sponsor.key().name(),
        'program': self.program.link_id,
        }
    self.data = request_data.RequestData(None, None, kwargs)

  def testUserWithNoProfileAccessDenied(self):
    """Tests that access is denied if current user has no profile"""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    access_checker = access.NON_STUDENT_PROFILE_ACCESS_CHECKER
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testUserWithStudentProfileAccessDenied(self):
    """Tests that access is denied if current user has student profile."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedSOCStudent(self.program, user=user)

    access_checker = access.NON_STUDENT_PROFILE_ACCESS_CHECKER
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testUserWithNonStudentProfileAccessGranted(self):
    """Tests that access is granted if current user has non-student profile."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    access_checker = access.NON_STUDENT_PROFILE_ACCESS_CHECKER
    access_checker.checkAccess(self.data, None)


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
      access_checker.checkAccess(data, None)
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
      access_checker.checkAccess(data, None)
    self.assertEqual(context.exception.message,
        access._MESSAGE_PROGRAM_NOT_ACTIVE)

    # the program is has already ended
    data._program.status = program_model.STATUS_VISIBLE
    data._program.timeline.program_start = timeline_utils.past(delta=100)
    data._program.timeline.program_end = timeline_utils.past(delta=50)
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(data, None)
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
    access_checker.checkAccess(data, None)


class IsUrlUserAccessCheckerTest(unittest.TestCase):
  """Tests for IsUrlUserAccessChecker class."""

  def setUp(self):
    """See unittest.setUp for specification."""
    self.data = request_data.RequestData(None, None, {})
    self.data._ndb_user = profile_utils.seedNDBUser()

  def testForMissingUserData(self):
    """Tests for URL data that does not contain any user data."""
    access_checker = access.IsUrlUserAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

  def testNonLoggedInUserAccessDenied(self):
    """Tests that exception is raised for a non logged-in user."""
    data = request_data.RequestData(None, None, {})
    data._gae_user = None
    data.kwargs['user'] = 'some_username'
    access_checker = access.IsUrlUserAccessChecker()
    with self.assertRaises(exception.LoginRequired):
      access_checker.checkAccess(data, None)

  def testNonUserAccessDenied(self):
    """Tests that access is denied for a user with no User entity."""
    self.data.kwargs['user'] = self.data._ndb_user.user_id
    self.data._ndb_user = None
    access_checker = access.IsUrlUserAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testOtherUserAccessDenied(self):
    """Tests that access is denied for a user who is not defined in URL."""
    self.data.kwargs['user'] = 'other'
    access_checker = access.IsUrlUserAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testSameUserAccessGranted(self):
    """Tests that access is granted for a user who is defined in URL."""
    self.data.kwargs['user'] = self.data._ndb_user.user_id
    access_checker = access.IsUrlUserAccessChecker()
    access_checker.checkAccess(self.data, None)


class IsUserOrgAdminForUrlOrgTest(unittest.TestCase):
  """Tests for IsUserOrgAdminForUrlOrg class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    sponsor = program_utils.seedSponsor()

    program_properties = {
        'sponsor': sponsor,
        'scope': sponsor,
        }
    program = seeder_logic.seed(
        program_model.Program, properties=program_properties)

    org_properties = {
        'program': program,
        'scope': program,
        }
    self.organization = seeder_logic.seed(
        org_model.Organization, properties=org_properties)

    kwargs = {
        'sponsor': sponsor.key().name(),
        'program': program.link_id,
        'organization': self.organization.link_id,
        }
    self.data = request_data.RequestData(None, None, kwargs)

  def testNoProfileAccessDenied(self):
    """Tests that error is raised if profile does not exist."""
    self.data._profile = None

    access_checker = access.IsUserOrgAdminForUrlOrg()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)
    self.assertEqual(context.exception.message, access._MESSAGE_NO_PROFILE)

  def testForNonExistingOrg(self):
    """Tests that error is raised when organization does not exist."""
    profile_properties = {
        'is_org_admin': True,
        'org_admin_for': [self.organization.key()],
        'is_mentor': True,
        'mentor_for': [self.organization.key()],
        'is_student': False,
        }
    self.data._profile = seeder_logic.seed(
        profile_model.Profile, properties=profile_properties)

    self.data.kwargs['organization'] = 'non_existing_org_id'

    access_checker = access.IsUserOrgAdminForUrlOrg()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.NOT_FOUND)

  def testMentorAccessDenied(self):
    """Tests that a mentor is denied access."""
    profile_properties = {
        'is_org_admin': False,
        'org_admin_for': [],
        'is_mentor': True,
        'mentor_for': [self.organization.key()],
        'is_student': False,
        }
    self.data._profile = seeder_logic.seed(
        profile_model.Profile, properties=profile_properties)
    self.data._url_org = self.organization

    access_checker = access.IsUserOrgAdminForUrlOrg()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testStudentAccessDenied(self):
    """Tests that a student is denied access."""
    profile_properties = {
        'is_org_admin': False,
        'org_admin_for': [],
        'is_mentor': False,
        'mentor_for': [],
        'is_student': True,
        }
    self.data._profile = seeder_logic.seed(
        profile_model.Profile, properties=profile_properties)
    self.data._url_org = self.organization

    access_checker = access.IsUserOrgAdminForUrlOrg()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testOrgAdminAccessGranted(self):
    """Tests that an organization administrator is granted access."""
    profile_properties = {
        'is_org_admin': True,
        'org_admin_for': [self.organization.key()],
        'is_mentor': True,
        'mentor_for': [self.organization.key()],
        'is_student': False,
        }
    self.data._profile = seeder_logic.seed(
        profile_model.Profile, properties=profile_properties)
    self.data._url_org = self.organization

    access_checker = access.IsUserOrgAdminForUrlOrg()
    access_checker.checkAccess(self.data, None)


class HasProfileAccessCheckerTest(unittest.TestCase):
  """Unit tests for HasProfileAccessChecker class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.sponsor = program_utils.seedSponsor()
    self.program = program_utils.seedProgram(sponsor_key=self.sponsor.key())

    kwargs = {
        'sponsor': self.sponsor.key().name(),
        'program': self.program.program_id,
        }
    self.data = request_data.RequestData(None, None, kwargs)

  def testUserWithNoProfileAccessDenied(self):
    """Tests that access is denied if the user has no profile."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    access_checker = access.HAS_PROFILE_ACCESS_CHECKER
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testUserWithActiveProfileAccessGranted(self):
    """Tests that access is granted if the user has an active profile."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    access_checker = access.HAS_PROFILE_ACCESS_CHECKER
    access_checker.checkAccess(self.data, None)

  def testUserWithBannedProfileAccessDenied(self):
    """Tests that access is denied if the user has a banned profile."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        status=ndb_profile_model.Status.BANNED)

    access_checker = access.HAS_PROFILE_ACCESS_CHECKER
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testUserProfileForAnotherProgramAccessDenied(self):
    """Tests that access is denied if the profile is another program."""
    other_program = program_utils.seedProgram(sponsor_key=self.sponsor.key())
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(other_program.key(), user=user)

    access_checker = access.HAS_PROFILE_ACCESS_CHECKER
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)


class HasNoProfileAccessCheckerTest(unittest.TestCase):
  """Unit tests for HasNoProfileAccessChecker class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.sponsor = program_utils.seedSponsor()
    self.program = program_utils.seedProgram(sponsor_key=self.sponsor.key())

    kwargs = {
        'sponsor': self.sponsor.key().name(),
        'program': self.program.program_id
        }
    self.data = request_data.RequestData(None, None, kwargs)

  def testUserWithProfileAccessDenied(self):
    """Tests that access is denied for a user with a profile."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(self.program.key(), user=user)

    access_checker = access.HasNoProfileAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testUserWithNoProfileAccessGranted(self):
    """Tests that access is granted for a user with no profile."""
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    access_checker = access.HasNoProfileAccessChecker()
    access_checker.checkAccess(self.data, None)


class OrgsSignupStartedAccessCheckerTest(unittest.TestCase):
  """Unit tests for OrgsSignupStartedAccessChecker class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    sponsor = program_utils.seedSponsor()
    program = program_utils.seedProgram(sponsor_key=sponsor.key())
    self.app_survey = program_utils.seedApplicationSurvey(program.key())

    kwargs = {
        'sponsor': sponsor.key().name(),
        'program': program.program_id
        }
    self.data = request_data.RequestData(None, None, kwargs)

  def testBeforeOrgSignupStartedAccessDenied(self):
    """Tests that access is denied before organization sign-up starts."""
    self.app_survey.survey_start = timeline_utils.future(delta=100)
    self.app_survey.survey_end = timeline_utils.future(delta=150)
    self.app_survey.put()

    access_checker = access.OrgSignupStartedAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testAfterOrgSignupStartedAccessGranted(self):
    """Tests that access is granted after organization sign-up starts."""
    self.app_survey.survey_start = timeline_utils.past()
    self.app_survey.survey_end = timeline_utils.future()
    self.app_survey.put()

    access_checker = access.OrgSignupStartedAccessChecker()
    access_checker.checkAccess(self.data, None)

  def testAfterOrgSignupEndedAccessGranted(self):
    """Tests that access is granted after organization sign-up ends."""
    self.app_survey.survey_start = timeline_utils.past(delta=150)
    self.app_survey.survey_end = timeline_utils.past(delta=100)
    self.app_survey.put()

    access_checker = access.OrgSignupStartedAccessChecker()
    access_checker.checkAccess(self.data, None)


class OrgsAnnouncedAccessCheckerTest(unittest.TestCase):
  """Unit tests for OrgsAnnouncedAccessChecker class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    sponsor = program_utils.seedSponsor()
    self.program = program_utils.seedProgram(sponsor_key=sponsor.key())

    kwargs = {
        'sponsor': sponsor.key().name(),
        'program': self.program.program_id
        }
    self.data = request_data.RequestData(None, None, kwargs)

  def testBeforeOrgsAnnouncedAccessDenied(self):
    """Tests that access is denied before orgs are announced."""
    self.program.timeline.accepted_organization_announced_deadline = (
        timeline_utils.future())
    self.program.timeline.put()

    access_checker = access.OrgsAnnouncedAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testAfterOrgsAnnouncedAccessGranted(self):
    """Tests that access is granted after orgs are announced."""
    self.program.timeline.accepted_organization_announced_deadline = (
        timeline_utils.past())
    self.program.timeline.put()

    access_checker = access.OrgsAnnouncedAccessChecker()
    access_checker.checkAccess(self.data, None)


class StudentSignupActiveAccessCheckerTest(unittest.TestCase):
  """Unit tests for StudentSignupActiveAccessChecker class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    sponsor = program_utils.seedSponsor()
    self.program = program_utils.seedProgram(sponsor_key=sponsor.key())

    kwargs = {
        'sponsor': sponsor.key().name(),
        'program': self.program.program_id
        }
    self.data = request_data.RequestData(None, None, kwargs)

  def testBeforeStudentSignupAccessDenied(self):
    """Tests that access is denied before student sign-up period."""
    self.program.timeline.student_signup_start = timeline_utils.future(delta=10)
    self.program.timeline.student_signup_end = timeline_utils.future(delta=20)
    self.program.timeline.put()

    access_checker = access.StudentSignupActiveAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testAfterStudentSignupAccessDenied(self):
    """Tests that access is denied after student sign-up period."""
    self.program.timeline.student_signup_start = timeline_utils.past(delta=20)
    self.program.timeline.student_signup_end = timeline_utils.past(delta=10)
    self.program.timeline.put()

    access_checker = access.StudentSignupActiveAccessChecker()
    with self.assertRaises(exception.UserError) as context:
      access_checker.checkAccess(self.data, None)
    self.assertEqual(context.exception.status, httplib.FORBIDDEN)

  def testDuringStudentSignupAccessGranted(self):
    """Tests that access is granted during student sign-up period."""
    self.program.timeline.student_signup_start = timeline_utils.past(delta=10)
    self.program.timeline.student_signup_end = timeline_utils.future(delta=10)
    self.program.timeline.put()

    access_checker = access.StudentSignupActiveAccessChecker()
    access_checker.checkAccess(self.data, None)
