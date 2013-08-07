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

"""Tests for GCI views for creating conversations."""

import unittest

from tests import profile_utils
from tests import program_utils

from soc.modules.gci.views import conversation_create as gciconversation_create_view


class MockRequestData:
  """An object that can pretend to be a RequestData object for tests.

  Attributes:
    program: A GCIProgram entity for the request.
    user: A User entity for the request.
    profile: A GCIProfile entity for the request.
  """
  def __init__(self, program_helper, profile_helper):
    """Populates the request data attributes.

    Args:
      program_helper: A GCIProgramHelper.
      profile_helper: A GCIProfileHelper.
    """
    self.program = program_helper.program
    self.profile = profile_helper.profile
    self.user = self.profile.user
    self.POST = None


class GCICreateConversationFormTest(unittest.TestCase):
  """Tests the views for creating GCI conversations."""

  def setUp(self):
    self.program_helper = program_utils.GCIProgramHelper()
    self.program_helper.createProgram()
    self.org_a = self.program_helper.createNewOrg({'name': 'org_a'})
    self.org_b = self.program_helper.createNewOrg({'name': 'org_b'})
    self.org_c = self.program_helper.createNewOrg({'name': 'org_c'})
    self.org_d = self.program_helper.createNewOrg({'name': 'org_d'})
    self.createProfileAndRequest()

  def createProfileAndRequest(self):
    """Creates a new GCIProfileHelper, along with a new MockRequestData for the
    helper.
    """
    self.profile_helper = profile_utils.GCIProfileHelper(
        self.program_helper.program, False)
    self.profile_helper.createProfile()
    self.mock_data = MockRequestData(self.program_helper, self.profile_helper)

  def testCreateProgramRoleChoices(self):
    """Tests that createProgramRoleChoices() returns the appropriate program
    role choices (if any) for a user."""

    # Test that for an average user, no program roles are available
    expected = set()
    actual = set(gciconversation_create_view.createProgramRoleChoices(
        self.mock_data))
    self.assertEqual(expected, actual)

    # Test that all program role choices are available for a host of the program
    self.createProfileAndRequest()
    self.profile_helper.createHost()

    expected = set([
      (
        gciconversation_create_view.ROLE_PROGRAM_ADMINISTRATORS,
        gciconversation_create_view.DEF_ROLE_PROGRAM_ADMINISTRATORS),
      (
        gciconversation_create_view.ROLE_PROGRAM_MENTORS,
        gciconversation_create_view.DEF_ROLE_PROGRAM_MENTORS),
      (
        gciconversation_create_view.ROLE_PROGRAM_STUDENTS,
        gciconversation_create_view.DEF_ROLE_PROGRAM_STUDENTS),
    ])
    actual = set(gciconversation_create_view.createProgramRoleChoices(
        self.mock_data))
    self.assertEqual(expected, actual)

    # Test that all program role choices are available for a developer
    self.createProfileAndRequest()
    self.profile_helper.createDeveloper()

    expected = set([
      (
        gciconversation_create_view.ROLE_PROGRAM_ADMINISTRATORS,
        gciconversation_create_view.DEF_ROLE_PROGRAM_ADMINISTRATORS),
      (
        gciconversation_create_view.ROLE_PROGRAM_MENTORS,
        gciconversation_create_view.DEF_ROLE_PROGRAM_MENTORS),
      (
        gciconversation_create_view.ROLE_PROGRAM_STUDENTS,
        gciconversation_create_view.DEF_ROLE_PROGRAM_STUDENTS),
    ])
    actual = set(gciconversation_create_view.createProgramRoleChoices(
        self.mock_data))
    self.assertEqual(expected, actual)

    # Test that someone who's just an org admin can send messages to other org
    # admins in the program
    self.createProfileAndRequest()
    self.profile_helper.createOrgAdmin(self.org_a)

    expected = set([
      (
        gciconversation_create_view.ROLE_PROGRAM_ADMINISTRATORS,
        gciconversation_create_view.DEF_ROLE_PROGRAM_ADMINISTRATORS),
    ])
    actual = set(gciconversation_create_view.createProgramRoleChoices(
        self.mock_data))
    self.assertEqual(expected, actual)

  def testCreateOrganizationRoleChoices(self):
    """Tests that createOrganizationRoleChoices() returns the appropriate
    organization role choices (if any) for a user."""

    # The choices are fixed at the moment
    expected = set([
      (
          gciconversation_create_view.ROLE_ORGANIZATION_ADMINISTRATORS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_ADMINISTRATORS),
      (
          gciconversation_create_view.ROLE_ORGANIZATION_MENTORS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_MENTORS),
    ])
    actual = set(gciconversation_create_view.createOrganizationRoleChoices(
        self.mock_data))
    self.assertEqual(expected, actual)

  def testCreateOrganizationChoices(self):
    """Tests that testCreateOrganizationChoices() returns the appropriate
    organization choices (if any) for a user."""

    # Test that for someone who is a mentor of orgs a,b and admin of orgs b,c,
    # that the correct organization choices are available
    self.createProfileAndRequest()
    profile = self.profile_helper.profile
    profile.mentor_for = [self.org_a.key(), self.org_b.key()]
    profile.org_admin_for = [self.org_b.key(), self.org_c.key()]
    profile.is_mentor = True
    profile.is_org_admin = True
    profile.put()

    expected = set([self.org_a.key(), self.org_b.key(), self.org_c.key()])
    actual = set(map(
        lambda org: org.key(),
        gciconversation_create_view.createOrganizationChoices(
            self.mock_data)))
    self.assertEqual(expected, actual)

    # Test that all organizations are available for a host of the program
    self.createProfileAndRequest()
    self.profile_helper.createHost()

    expected = set([
        self.org_a.key(), self.org_b.key(), self.org_c.key(), self.org_d.key()])
    actual = set(map(
        lambda org: org.key(),
        gciconversation_create_view.createOrganizationChoices(
            self.mock_data)))
    self.assertEqual(expected, actual)

    # Test that all organizations are available for a developer
    self.createProfileAndRequest()
    self.profile_helper.createDeveloper()

    expected = set([
        self.org_a.key(), self.org_b.key(), self.org_c.key(), self.org_d.key()])
    actual = set(map(
        lambda org: org.key(),
        gciconversation_create_view.createOrganizationChoices(
            self.mock_data)))
    self.assertEqual(expected, actual)

  def testFields(self):
    """Tests that the right fields are created by ConversationCreateForm."""

    # Test that only recipients type choice is 'Users', and that the standard
    # fields exist
    form = gciconversation_create_view.ConversationCreateForm(self.mock_data)
    self.assertIn('recipients_type', form.bound_fields)
    self.assertIn('users', form.bound_fields)
    self.assertNotIn('program_roles', form.bound_fields)
    self.assertNotIn('organization_roles', form.bound_fields)
    self.assertNotIn('organization', form.bound_fields)
    self.assertIn('auto_update_users', form.bound_fields)
    self.assertIn('subject', form.bound_fields)
    self.assertIn('message_content', form.bound_fields)
    recipients_type_html = form.bound_fields['recipients_type'].render().lower()
    self.assertIn('specified users', recipients_type_html)
    self.assertNotIn('roles', recipients_type_html)
    self.assertNotIn('organization', recipients_type_html)

    # Test that all fields are present for a developer
    self.createProfileAndRequest()
    self.profile_helper.createDeveloper()
    form = gciconversation_create_view.ConversationCreateForm(self.mock_data)
    self.assertIn('recipients_type', form.bound_fields)
    self.assertIn('users', form.bound_fields)
    self.assertIn('program_roles', form.bound_fields)
    self.assertIn('organization_roles', form.bound_fields)
    self.assertIn('organization', form.bound_fields)
    self.assertIn('auto_update_users', form.bound_fields)
    self.assertIn('subject', form.bound_fields)
    self.assertIn('message_content', form.bound_fields)
    recipients_type_html = form.bound_fields['recipients_type'].render().lower()
    self.assertIn('specified users', recipients_type_html)
    self.assertIn('roles', recipients_type_html)
    self.assertIn('organization', recipients_type_html)
    program_roles_html = form.bound_fields['program_roles'].render()
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_PROGRAM_ADMINISTRATORS,
        program_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_PROGRAM_MENTORS,
        program_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_PROGRAM_STUDENTS,
        program_roles_html)
    organization_roles_html = form.bound_fields['organization_roles'].render()
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_ADMINISTRATORS,
        organization_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_MENTORS,
        organization_roles_html)
    organization_html = form.bound_fields['organization'].render()
    self.assertIn('org_a', organization_html)
    self.assertIn('org_b', organization_html)
    self.assertIn('org_c', organization_html)
    self.assertIn('org_d', organization_html)

    # Test that all fields are present for a host of the program sponsor
    self.createProfileAndRequest()
    self.profile_helper.createHost()
    form = gciconversation_create_view.ConversationCreateForm(self.mock_data)
    self.assertIn('recipients_type', form.bound_fields)
    self.assertIn('users', form.bound_fields)
    self.assertIn('program_roles', form.bound_fields)
    self.assertIn('organization_roles', form.bound_fields)
    self.assertIn('organization', form.bound_fields)
    self.assertIn('auto_update_users', form.bound_fields)
    self.assertIn('subject', form.bound_fields)
    self.assertIn('message_content', form.bound_fields)
    recipients_type_html = form.bound_fields['recipients_type'].render().lower()
    self.assertIn('specified users', recipients_type_html)
    self.assertIn('roles', recipients_type_html)
    self.assertIn('organization', recipients_type_html)
    program_roles_html = form.bound_fields['program_roles'].render()
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_PROGRAM_ADMINISTRATORS,
        program_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_PROGRAM_MENTORS,
        program_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_PROGRAM_STUDENTS,
        program_roles_html)
    organization_roles_html = form.bound_fields['organization_roles'].render()
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_ADMINISTRATORS,
        organization_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_MENTORS,
        organization_roles_html)
    organization_html = form.bound_fields['organization'].render()
    self.assertIn('org_a', organization_html)
    self.assertIn('org_b', organization_html)
    self.assertIn('org_c', organization_html)
    self.assertIn('org_d', organization_html)

    # Test that for someone who is a mentor of orgs a,b and admin of orgs b,c,
    # that the correct fields and field options are visible.
    self.createProfileAndRequest()
    profile = self.profile_helper.profile
    profile.mentor_for = [self.org_a.key(), self.org_b.key()]
    profile.org_admin_for = [self.org_b.key(), self.org_c.key()]
    profile.is_mentor = True
    profile.is_org_admin = True
    profile.put()
    form = gciconversation_create_view.ConversationCreateForm(self.mock_data)
    self.assertIn('recipients_type', form.bound_fields)
    self.assertIn('users', form.bound_fields)
    self.assertIn('program_roles', form.bound_fields)
    self.assertIn('organization_roles', form.bound_fields)
    self.assertIn('organization', form.bound_fields)
    self.assertIn('auto_update_users', form.bound_fields)
    self.assertIn('subject', form.bound_fields)
    self.assertIn('message_content', form.bound_fields)
    recipients_type_html = form.bound_fields['recipients_type'].render().lower()
    self.assertIn('specified users', recipients_type_html)
    self.assertIn('roles', recipients_type_html)
    self.assertIn('organization', recipients_type_html)
    program_roles_html = form.bound_fields['program_roles'].render()
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_PROGRAM_ADMINISTRATORS,
        program_roles_html)
    self.assertNotIn(
        gciconversation_create_view.DEF_ROLE_PROGRAM_MENTORS,
        program_roles_html)
    self.assertNotIn(
        gciconversation_create_view.DEF_ROLE_PROGRAM_STUDENTS,
        program_roles_html)
    organization_roles_html = form.bound_fields['organization_roles'].render()
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_ADMINISTRATORS,
        organization_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_MENTORS,
        organization_roles_html)
    organization_html = form.bound_fields['organization'].render()
    self.assertIn('org_a', organization_html)
    self.assertIn('org_b', organization_html)
    self.assertIn('org_c', organization_html)
    self.assertNotIn('org_d', organization_html)
