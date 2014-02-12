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

"""Tests for profile logic."""

import mock
import unittest

from google.appengine.ext import ndb

from codein.logic import profile as profile_logic

from melange.utils import rich_bool

from soc.modules.gci.models import organization as org_model
from soc.modules.gci.models import profile as profile_model
from soc.modules.gci.models import task as task_model
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import profile_utils
from tests import program_utils


class CanResignAsMentorForOrgTest(unittest.TestCase):
  """Unit tests for canResignAsMentorForOrg function."""

  def setUp(self):
    # seed an organization
    self.org = seeder_logic.seed(org_model.GCIOrganization)

    # seed a mentor
    profile_properties = {
        'is_mentor': True,
        'mentor_for': [self.org.key()],
        }
    self.profile = seeder_logic.seed(
        profile_model.GCIProfile, properties=profile_properties)

    # seed a task
    task_properties = {'org': self.org}
    self.task = seeder_logic.seed(
        task_model.GCITask, properties=task_properties)

  def testForNoTasksAssigned(self):
    """Tests for a mentor with no tasks assigned."""
    result = profile_logic.canResignAsMentorForOrg(
        self.profile, self.org.key())
    self.assertTrue(result)

  def testForClosedTask(self):
    """Tests for a mentor with a closed task assigned."""
    self.task.mentors = [self.profile.key()]
    self.task.status = 'Closed'
    self.task.put()

    result = profile_logic.canResignAsMentorForOrg(
        self.profile, self.org.key())
    self.assertTrue(result)

  def testForNonClosedTask(self):
    self.task.mentors = [self.profile.key()]
    statuses = [status for status in task_model.GCITask.status.choices
        if status != 'Closed']
    for status in statuses:
      self.task.status = status
      self.task.put()

      result = profile_logic.canResignAsMentorForOrg(
          self.profile, self.org.key())
      self.assertFalse(result)


class IsNoRoleEligibleForOrgTest(unittest.TestCase):
  """Unit tests for isNoRoleEligibleForOrg function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    # seed an organization
    self.org = seeder_logic.seed(org_model.GCIOrganization)

    # seed a user
    self.profile = seeder_logic.seed(profile_model.GCIProfile)

    # seed a task
    task_properties = {'org': self.org}
    self.task = seeder_logic.seed(
        task_model.GCITask, properties=task_properties)

  def testForNoRole(self):
    """Tests for a user who does not have a role with organization."""
    result = profile_logic.isNoRoleEligibleForOrg(self.profile, self.org.key())
    self.assertTrue(result)

  @mock.patch.object(
      profile_logic, 'canResignAsMentorForOrg', return_value=rich_bool.FALSE)
  def testForMentorThatCannotResign(self, mock_func):
    """Tests for a user who is a mentor that cannot currently resign."""
    # make profile a mentor for organization
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.org.key()]

    result = profile_logic.isNoRoleEligibleForOrg(self.profile, self.org.key())
    self.assertFalse(result)

  @mock.patch.object(
      profile_logic, 'canResignAsMentorForOrg', return_value=rich_bool.TRUE)
  def testForMentorThatCanResign(self, mock_func):
    """Tests for a user who is a mentor that can currently resign."""
    # make profile a mentor for organization
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.org.key()]

    result = profile_logic.isNoRoleEligibleForOrg(self.profile, self.org.key())
    self.assertTrue(result)

  @mock.patch.object(
      profile_logic, 'canResignAsOrgAdminForOrg', return_value=rich_bool.FALSE)
  def testForOrgAdminThatCannotResign(self, mock_func):
    """Tests for u user who is an org admin that cannot currently resign."""
    # make profile an administrator for organization
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.org.key()]
    self.profile.is_org_admin = True
    self.profile.org_admin_for = [self.org.key()]

    result = profile_logic.isNoRoleEligibleForOrg(self.profile, self.org.key())
    self.assertFalse(result)

  @mock.patch.object(
      profile_logic, 'canResignAsOrgAdminForOrg', return_value=rich_bool.TRUE)
  def testForOrgAdminThatCanResign(self, mock_func):
    """Tests for u user who is an org admin that can currently resign."""
    # make profile an administrator for organization
    self.profile.is_mentor = True
    self.profile.mentor_for = [self.org.key()]
    self.profile.is_org_admin = True
    self.profile.org_admin_for = [self.org.key()]

    # profile cannot resign as mentor, though
    with mock.patch.object(
        profile_logic, 'canResignAsMentorForOrg',
        return_value=rich_bool.FALSE):
      result = profile_logic.isNoRoleEligibleForOrg(
          self.profile, self.org.key())
      self.assertFalse(result)

    # now, profile can resign as mentor
    with mock.patch.object(
        profile_logic, 'canResignAsMentorForOrg',
        return_value=rich_bool.TRUE):
      result = profile_logic.isNoRoleEligibleForOrg(
          self.profile, self.org.key())
      self.assertTrue(result)


class IsMentorRoleEligibleForOrgTest(unittest.TestCase):
  """Unit tests for isMentorRoleEligibleForOrg function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    program = program_utils.seedGCIProgram()

    # seed an organization
    self.org = program_utils.seedOldOrganization(program.key())

    # seed a profile
    self.profile = profile_utils.seedNDBProfile(program.key())

  def testForUserWithNoRole(self):
    """Tests that user with no role is eligible."""
    result = profile_logic.isMentorRoleEligibleForOrg(
        self.profile, ndb.Key.from_old_key(self.org.key()))
    self.assertTrue(result)

  @mock.patch.object(
      profile_logic, 'canResignAsOrgAdminForOrg', return_value=rich_bool.FALSE)
  def testForOrgAdminThatCannotResign(self, mock_func):
    """Tests that org admin that cannot resign is not eligible."""
    self.profile.mentor_for = [ndb.Key.from_old_key(self.org.key())]
    self.profile.admin_for = [ndb.Key.from_old_key(self.org.key())]

    result = profile_logic.isMentorRoleEligibleForOrg(
        self.profile, ndb.Key.from_old_key(self.org.key()))
    self.assertFalse(result)

  @mock.patch.object(
      profile_logic, 'canResignAsOrgAdminForOrg', return_value=rich_bool.TRUE)
  def testForOrgAdminThatCanResign(self, mock_func):
    """Tests that org admin that can resign is eligible."""
    self.profile.mentor_for = [ndb.Key.from_old_key(self.org.key())]
    self.profile.admin_for = [ndb.Key.from_old_key(self.org.key())]

    result = profile_logic.isMentorRoleEligibleForOrg(
        self.profile, ndb.Key.from_old_key(self.org.key()))
    self.assertTrue(result)


class IsFormVerificationAwaitingTest(unittest.TestCase):
  """Unit tests isFormVerificationAwaiting function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    program = program_utils.seedGCIProgram()
    self.profile = profile_utils.seedNDBStudent(program)

  def testForNoFormsSubmitted(self):
    """Tests the behavior when no forms have been submitted."""
    self.profile.student_data.consent_form = ndb.BlobKey('blob-key')
    self.profile.student_data.enrollment_form = None
    self.assertFalse(profile_logic.isFormVerificationAwaiting(self.profile))

  def testForOneFormSubmitted(self):
    """Tests the behavior when one form has been submitted."""
    # only enrollment form is submitted but not verified
    self.profile.student_data.consent_form = None
    self.profile.student_data.enrollment_form = ndb.BlobKey('blob-key')
    self.profile.student_data.is_enrollment_form_verified = False
    self.assertFalse(profile_logic.isFormVerificationAwaiting(self.profile))

    # only enrollment form is submitted and verified
    self.profile.student_data.is_enrollment_form_verified = True
    self.assertFalse(profile_logic.isFormVerificationAwaiting(self.profile))

    # only consent form is submitted but not verified
    self.profile.student_data.consent_form = ndb.BlobKey('blob-key')
    self.profile.student_data.is_consent_form_verified = False
    self.profile.student_data.enrollment_form = None
    self.profile.student_data.is_enrollment_form_verified = None
    self.assertFalse(profile_logic.isFormVerificationAwaiting(self.profile))

    # only consent form is submitted and verified
    self.profile.student_data.is_consent_form_verified = True
    self.assertFalse(profile_logic.isFormVerificationAwaiting(self.profile))

  def testForTwoFormsSubmitted(self):
    """Tests the behavior when two forms have been submitted."""
    self.profile.student_data.enrollment_form = ndb.BlobKey('blob-key')
    self.profile.student_data.consent_form = ndb.BlobKey('blob-key')

    # no forms have been verified
    self.profile.student_data.is_consent_form_verified = False
    self.profile.student_data.is_enrollment_form_verified = False
    self.assertTrue(profile_logic.isFormVerificationAwaiting(self.profile))

    # only student id form is verified
    self.profile.student_data.is_enrollment_form_verified = True
    self.assertTrue(profile_logic.isFormVerificationAwaiting(self.profile))

    # only consent form is verified
    self.profile.student_data.is_consent_form_verified = True
    self.profile.student_data.is_enrollment_form_verified = False
    self.assertTrue(profile_logic.isFormVerificationAwaiting(self.profile))

    # both forms are verified
    self.profile.student_data.is_enrollment_form_verified = True
    self.assertFalse(profile_logic.isFormVerificationAwaiting(self.profile))
