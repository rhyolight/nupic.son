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

from google.appengine.ext import ndb

from melange.models import profile as profile_model

from tests import program_utils
from tests import profile_utils
from tests.utils import conversation_utils

from soc.models import conversation as conversation_model

from soc.modules.gci.logic import conversation as gciconversation_logic
from soc.modules.gci.logic import message as gcimessage_logic

from soc.modules.gci.models import message as gcimessage_model

from soc.modules.gci.views import conversation_create as gciconversation_create_view
from soc.modules.gci.views.helper import request_data


class MockRequestData(object):
  """An object that can pretend to be a RequestData object for tests.

  Attributes:
    program: A GCIProgram entity for the request.
    user: A User entity for the request.
    profile: A GCIProfile entity for the request.
  """

  def __init__(self, program, profile, post=None):
    """Populates the request data attributes.

    Args:
      program: Program entity.
      profile: Profile entity.
      post: A dict containing POST data sent along with the request.
    """
    self.program = program
    self.profile = profile
    self.user = profile.user
    self.POST = post


def _getRequestData(profile, postdata=None):
  """Returns a new request data based on the specified profile and post data.

  Args:
    profile: Profile entity.
    postdata: A dict containing POST data.

  Returns:
    RequestData object.
  """
  profile_key = profile.key if isinstance(profile, ndb.Model) else profile.key()
  kwargs = {
      'sponsor': profile_model.getSponsorId(profile_key),
      'program': profile_model.getProgramId(profile_key),
      'user': profile_model.getUserId(profile_key),
      }
  data = request_data.RequestData(None, None, kwargs)
  data._POST = postdata
  return data


class GCICreateConversationFormTest(unittest.TestCase):
  """Tests the views for creating GCI conversations."""

  def setUp(self):
    self.program = program_utils.seedGCIProgram()
    self.program_key = ndb.Key.from_old_key(self.program.key())
    self.conv_utils = conversation_utils.GCIConversationHelper(self.program_key)

    self.org_a = program_utils.seedOldOrganization(
        self.program.key(), name='org_a')
    self.org_b = program_utils.seedOldOrganization(
        self.program.key(), name='org_b')
    self.org_c = program_utils.seedOldOrganization(
        self.program.key(), name='org_c')
    self.org_d = program_utils.seedOldOrganization(
        self.program.key(), name='org_d')
    self.createProfile()

  def assertEmpty(self, item):
    """Asserts that an object is not empty.

    Args:
      item: The object.
    """
    l = len(item)
    if l > 0:
      raise AssertionError('Object is not empty, with a length of %d.' % l)

  def assertConversation(
      self, conversation, subject=None, creator=None, recipients_type=None,
      include_admins=None, include_mentors=None, include_students=None,
      include_winners=None, organization=None, message_content=None, users=None,
      auto_update_users=None):
    """Asserts that a conversation has been created with certain properties.

    Only conversation must be passed. The other attributes are optional, and
    will not be tested if None.

    Args:
      conversation: Key (ndb) of GCIConversation.
      subject: If not None, test that the conversation has this subject string.
      creator: If not None, test that the conversation and first message (if
               applicable) was created by this User key (ndb).
      recipients_type: If not None, test that the conversation has this
                       recipients_type.
      include_admins: If not None, test that the conversations will include
                      admins or not.
      include_mentors: If not None, test that the conversations will include
                       mentors or not.
      include_students: If not None, test that the conversations will include
                        students or not.
      include_winners: If not None, test that the conversations will include
                       winners or not.
      organization: If not None, test that the conversation organization is this
                    organization key (ndb).
      message_content: If not None, test that the first message in the
                       conversation has this content.
      users: If not None, test that this list of User keys (ndb) are added to
             the conversation.
      auto_update_users: If not None, test that the conversation has the correct
                         auto_update_users value.
    """
    self.assertIsNotNone(conversation, msg='The conversation key is None.')

    conversation_ent = conversation.get()
    message_query = (gcimessage_logic.queryForConversation(conversation)
        .order(gcimessage_model.GCIMessage.sent_on)
        .fetch(1))
    message_ent = message_query[0] if message_query else None

    if subject is not None:
      self.assertEqual(
          subject, conversation_ent.subject,
          msg='Conversation subject is incorrect.')

    if creator is not None:
      self.assertEqual(
          creator, conversation_ent.creator,
          msg='Conversation creator is incorrect.')
      if message_ent:
        self.assertEqual(
            creator, message_ent.author,
            msg='Conversation message author is incorrect.')

    if recipients_type is not None:
      self.assertEqual(
          recipients_type, conversation_ent.recipients_type,
          msg='Conversation recipients_type is incorrect.')

    if include_admins is not None:
      self.assertEqual(
          include_admins, conversation_ent.include_admins,
          msg='Conversation include_admins is incorrect.')

    if include_mentors is not None:
      self.assertEqual(
          include_mentors, conversation_ent.include_mentors,
          msg='Conversation include_mentors is incorrect.')

    if include_students is not None:
      self.assertEqual(
          include_students, conversation_ent.include_students,
          msg='Conversation include_students is incorrect.')

    if include_winners is not None:
      self.assertEqual(
          include_winners, conversation_ent.include_winners,
          msg='Conversation include_winners is incorrect.')

    if organization is not None:
      self.assertEqual(
          organization, conversation_ent.organization,
          msg='Conversation organization is incorrect.')

    if message_content is not None:
      self.assertIsNotNone(
          message_ent,
          msg='Cannot test message content because initial message is None.')
      self.assertEqual(
          message_content, message_ent.content,
          msg='Conversation message content is incorrect.')

    if users is not None:
      added_users = map(
        lambda e: e.user,
        gciconversation_logic.queryConversationUserForConversation(
            conversation))
      self.assertEqual(
          set(users), set(added_users), msg='Conversation users are incorrect.')

    if auto_update_users is not None:
      self.assertEqual(
          auto_update_users, conversation_ent.auto_update_users,
          msg='Conversation auto_update_users is incorrect.')

  def createProfile(self, post=None):
    """Creates a new GCIProfileHelper and a profile"""
    self.profile_helper = profile_utils.GCIProfileHelper(
        self.program, False)
    self.profile_helper.createProfile()
    self.user_key = ndb.Key.from_old_key(self.profile_helper.profile.user.key())
    self.profile = self.profile_helper.profile


  def testCreateProgramRoleChoices(self):
    """Tests that createProgramRoleChoices() returns the appropriate program
    role choices (if any) for a user."""

    # Test that for an average user, no program roles are available
    data = _getRequestData(self.profile)
    actual = set(gciconversation_create_view.createProgramRoleChoices(data))
    self.assertEqual(actual, set())

    # Test that all program role choices are available for a host of the program
    self.createProfile()
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
      (
        gciconversation_create_view.ROLE_PROGRAM_WINNERS,
        gciconversation_create_view.DEF_ROLE_PROGRAM_WINNERS),
    ])

    data = _getRequestData(self.profile)
    actual = set(gciconversation_create_view.createProgramRoleChoices(data))
    self.assertEqual(expected, actual)

    # Test that all program role choices are available for a developer
    self.createProfile()
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
      (
        gciconversation_create_view.ROLE_PROGRAM_WINNERS,
        gciconversation_create_view.DEF_ROLE_PROGRAM_WINNERS),
    ])

    data = _getRequestData(self.profile)
    actual = set(gciconversation_create_view.createProgramRoleChoices(data))
    self.assertEqual(expected, actual)

    # Test that someone who's just an org admin can send messages to other org
    # admins in the program
    self.createProfile()
    self.profile_helper.createOrgAdmin(self.org_a)

    expected = set([(
        gciconversation_create_view.ROLE_PROGRAM_ADMINISTRATORS,
        gciconversation_create_view.DEF_ROLE_PROGRAM_ADMINISTRATORS)])

    data = _getRequestData(self.profile)
    actual = set(gciconversation_create_view.createProgramRoleChoices(data))
    self.assertEqual(expected, actual)

  def testCreateOrganizationRoleChoices(self):
    """Tests that createOrganizationRoleChoices() returns the appropriate
    organization role choices (if any) for a user."""

    # For an average user, only organization mentors and administrators should
    # be choices.
    expected = set([
      (
          gciconversation_create_view.ROLE_ORGANIZATION_ADMINISTRATORS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_ADMINISTRATORS),
      (
          gciconversation_create_view.ROLE_ORGANIZATION_MENTORS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_MENTORS),
    ])
    data = _getRequestData(self.profile)
    actual = set(
        gciconversation_create_view.createOrganizationRoleChoices(data))
    self.assertEqual(expected, actual)

    # Test that all choices are available for org admins
    self.createProfile()
    self.profile_helper.createOrgAdmin(self.org_a)
    expected = set([
      (
          gciconversation_create_view.ROLE_ORGANIZATION_ADMINISTRATORS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_ADMINISTRATORS),
      (
          gciconversation_create_view.ROLE_ORGANIZATION_MENTORS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_MENTORS),
      (
          gciconversation_create_view.ROLE_ORGANIZATION_WINNERS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_WINNERS),
    ])
    data = _getRequestData(self.profile)
    actual = set(
        gciconversation_create_view.createOrganizationRoleChoices(data))
    self.assertEqual(expected, actual)

    # Test that all choices are available for org mentors
    self.createProfile()
    self.profile_helper.createMentor(self.org_b)
    expected = set([
      (
          gciconversation_create_view.ROLE_ORGANIZATION_ADMINISTRATORS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_ADMINISTRATORS),
      (
          gciconversation_create_view.ROLE_ORGANIZATION_MENTORS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_MENTORS),
      (
          gciconversation_create_view.ROLE_ORGANIZATION_WINNERS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_WINNERS),
    ])
    data = _getRequestData(self.profile)
    actual = set(
        gciconversation_create_view.createOrganizationRoleChoices(data))
    self.assertEqual(expected, actual)

    # Test that all choices are available for program hosts
    self.createProfile()
    self.profile_helper.createHost()
    expected = set([
      (
          gciconversation_create_view.ROLE_ORGANIZATION_ADMINISTRATORS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_ADMINISTRATORS),
      (
          gciconversation_create_view.ROLE_ORGANIZATION_MENTORS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_MENTORS),
      (
          gciconversation_create_view.ROLE_ORGANIZATION_WINNERS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_WINNERS),
    ])
    data = _getRequestData(self.profile)
    actual = set(
        gciconversation_create_view.createOrganizationRoleChoices(data))
    self.assertEqual(expected, actual)

    # Test that all choices are available for developers
    self.createProfile()
    self.profile_helper.createDeveloper()
    expected = set([
      (
          gciconversation_create_view.ROLE_ORGANIZATION_ADMINISTRATORS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_ADMINISTRATORS),
      (
          gciconversation_create_view.ROLE_ORGANIZATION_MENTORS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_MENTORS),
      (
          gciconversation_create_view.ROLE_ORGANIZATION_WINNERS,
          gciconversation_create_view.DEF_ROLE_ORGANIZATION_WINNERS),
    ])
    data = _getRequestData(self.profile)
    actual = set(
        gciconversation_create_view.createOrganizationRoleChoices(data))
    self.assertEqual(expected, actual)

  def testCreateOrganizationChoices(self):
    """Tests that testCreateOrganizationChoices() returns the appropriate
    organization choices (if any) for a user."""

    # Test that for an average user, all organizations are available
    self.createProfile()

    expected = set([
        self.org_a.key(), self.org_b.key(), self.org_c.key(), self.org_d.key()])
    data = _getRequestData(self.profile)
    actual = set(
        map(lambda org: org.key(),
            gciconversation_create_view.createOrganizationChoices(data)))
    self.assertEqual(expected, actual)

    # Test that all organizations are available for a host of the program
    self.createProfile()
    self.profile_helper.createHost()

    expected = set([
        self.org_a.key(), self.org_b.key(), self.org_c.key(), self.org_d.key()])
    data = _getRequestData(self.profile)
    actual = set(
        map(lambda org: org.key(),
            gciconversation_create_view.createOrganizationChoices(data)))
    self.assertEqual(expected, actual)

    # Test that all organizations are available for a developer
    self.createProfile()
    self.profile_helper.createDeveloper()

    expected = set([
        self.org_a.key(), self.org_b.key(), self.org_c.key(), self.org_d.key()])
    data = _getRequestData(self.profile)
    actual = set(
        map(lambda org: org.key(),
            gciconversation_create_view.createOrganizationChoices(data)))
    self.assertEqual(expected, actual)

  def testFields(self):
    """Tests that the right fields are created by ConversationCreateForm."""

    # Test that only recipients type choice is 'Organization', and that the
    # standards fields exist along with all organizations
    data = _getRequestData(self.profile)
    form = gciconversation_create_view.ConversationCreateForm(data)
    self.assertIn('recipients_type', form.bound_fields)
    self.assertNotIn('users', form.bound_fields)
    self.assertNotIn('program_roles', form.bound_fields)
    self.assertIn('organization_roles', form.bound_fields)
    self.assertIn('organization', form.bound_fields)
    self.assertIn('auto_update_users', form.bound_fields)
    self.assertIn('subject', form.bound_fields)
    self.assertIn('message_content', form.bound_fields)
    recipients_type_html = form.bound_fields['recipients_type'].render().lower()
    self.assertNotIn('specified users', recipients_type_html)
    self.assertNotIn('roles', recipients_type_html)
    self.assertIn('organization', recipients_type_html)
    organization_roles_html = form.bound_fields['organization_roles'].render()
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_ADMINISTRATORS,
        organization_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_MENTORS,
        organization_roles_html)
    self.assertNotIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_WINNERS,
        organization_roles_html)
    organization_html = form.bound_fields['organization'].render()
    self.assertIn('org_a', organization_html)
    self.assertIn('org_b', organization_html)
    self.assertIn('org_c', organization_html)
    self.assertIn('org_d', organization_html)

    # Test that all fields are present for a developer
    self.createProfile()
    self.profile_helper.createDeveloper()
    data = _getRequestData(self.profile)
    form = gciconversation_create_view.ConversationCreateForm(data)
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
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_PROGRAM_WINNERS,
        program_roles_html)
    organization_roles_html = form.bound_fields['organization_roles'].render()
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_ADMINISTRATORS,
        organization_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_MENTORS,
        organization_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_WINNERS,
        organization_roles_html)
    organization_html = form.bound_fields['organization'].render()
    self.assertIn('org_a', organization_html)
    self.assertIn('org_b', organization_html)
    self.assertIn('org_c', organization_html)
    self.assertIn('org_d', organization_html)

    # Test that all fields are present for a host of the program sponsor
    self.createProfile()
    self.profile_helper.createHost()
    data = _getRequestData(self.profile)
    form = gciconversation_create_view.ConversationCreateForm(data)
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
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_PROGRAM_WINNERS,
        program_roles_html)
    organization_roles_html = form.bound_fields['organization_roles'].render()
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_ADMINISTRATORS,
        organization_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_MENTORS,
        organization_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_WINNERS,
        organization_roles_html)
    organization_html = form.bound_fields['organization'].render()
    self.assertIn('org_a', organization_html)
    self.assertIn('org_b', organization_html)
    self.assertIn('org_c', organization_html)
    self.assertIn('org_d', organization_html)

    # Test that for someone who is a mentor of orgs a,b and admin of orgs b,c,
    # that the correct fields and field options are visible.
    self.createProfile()
    profile = self.profile_helper.profile
    profile.mentor_for = [self.org_a.key(), self.org_b.key()]
    profile.org_admin_for = [self.org_b.key(), self.org_c.key()]
    profile.is_mentor = True
    profile.is_org_admin = True
    profile.put()
    data = _getRequestData(self.profile)
    form = gciconversation_create_view.ConversationCreateForm(data)
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
    self.assertNotIn(
        gciconversation_create_view.DEF_ROLE_PROGRAM_WINNERS,
        program_roles_html)
    organization_roles_html = form.bound_fields['organization_roles'].render()
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_ADMINISTRATORS,
        organization_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_MENTORS,
        organization_roles_html)
    self.assertIn(
        gciconversation_create_view.DEF_ROLE_ORGANIZATION_WINNERS,
        organization_roles_html)
    organization_html = form.bound_fields['organization'].render()
    self.assertIn('org_a', organization_html)
    self.assertIn('org_b', organization_html)
    self.assertIn('org_c', organization_html)
    self.assertIn('org_d', organization_html)

  def testSubmission(self):
    """Tests that the submitting the form correctly creates a conversation or
    displays the right errors.
    """

    org_a_key = ndb.Key.from_old_key(self.org_a.key())
    org_b_key = ndb.Key.from_old_key(self.org_b.key())
    org_c_key = ndb.Key.from_old_key(self.org_c.key())
    org_d_key = ndb.Key.from_old_key(self.org_d.key())

    # Create three dummy admin users, two as admins for two orgs, then a third
    # that is an admin for both first two orgs.
    dummy_org_admin_a = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.ADMIN],
        admin_organizations=[org_a_key])
    dummy_org_admin_b = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.ADMIN],
        admin_organizations=[org_b_key])
    dummy_org_admin_ab = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.ADMIN],
        admin_organizations=[org_a_key, org_b_key])

    # Create three dummy mentor users, two as mentors for two orgs, then a third
    # that is a mentor for both first two orgs.
    dummy_org_mentor_a = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.MENTOR],
        mentor_organizations=[org_a_key])
    dummy_org_mentor_b = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.MENTOR],
        mentor_organizations=[org_b_key])
    dummy_org_mentor_ab = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.MENTOR],
        mentor_organizations=[org_a_key, org_b_key])

    # Create two dummy students
    dummy_student_a = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.STUDENT])
    dummy_student_b = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.STUDENT])

    # Create two dummy winner users, each as a winner of each org
    dummy_winner_a = self.conv_utils.createUser(
        return_key=True, winning_organization=org_a_key,
        roles=[conversation_utils.STUDENT, conversation_utils.WINNER])
    dummy_winner_b = self.conv_utils.createUser(
        return_key=True, winning_organization=org_b_key,
        roles=[conversation_utils.STUDENT, conversation_utils.WINNER])

    # Create a student who's also a mentor of the third org
    dummy_student_org_mentor_c = self.conv_utils.createUser(
        return_key=True, mentor_organizations=[org_c_key],
        roles=[conversation_utils.STUDENT, conversation_utils.MENTOR])

    # Test for correct errors in a mostly blank form for recipients_type 'User'
    self.createProfile()
    self.profile_helper.createDeveloper()
    postdata = {'recipients_type': conversation_model.USER}
    data = _getRequestData(self.profile, postdata=postdata)

    form = gciconversation_create_view.ConversationCreateForm(data)
    self.assertFalse(form.is_valid())
    self.assertEmpty(form.bound_fields['recipients_type'].errors)
    self.assertIn('required', ''.join(form.bound_fields['users'].errors))
    self.assertIn('required', ''.join(form.bound_fields['subject'].errors))
    self.assertIn(
        'required', ''.join(form.bound_fields['message_content'].errors))
    self.assertEmpty(form.bound_fields['organization'].errors)
    self.assertEmpty(form.bound_fields['organization_roles'].errors)
    self.assertEmpty(form.bound_fields['program_roles'].errors)

    # Test for empty users array
    self.createProfile()
    self.profile_helper.createDeveloper()

    postdata = {
        'recipients_type': conversation_model.USER,
        'users': '[]',
        }
    data = _getRequestData(self.profile, postdata=postdata)
    form = gciconversation_create_view.ConversationCreateForm(data)
    self.assertIn('specified', ''.join(form.bound_fields['users'].errors))

    # Test for invalid user error
    self.createProfile()
    self.profile_helper.createDeveloper()

    name_a = ndb.Key.to_old_key(dummy_student_a).name()
    name_b = ndb.Key.to_old_key(dummy_org_mentor_b).name()
    postdata = {
        'recipients_type': conversation_model.PROGRAM,
        'users': '["%s", "foo", "%s", "bar"]' % (name_a, name_b),
        }
    data = _getRequestData(self.profile, postdata=postdata)
    form = gciconversation_create_view.ConversationCreateForm(data)
    self.assertFalse(form.is_valid())
    self.assertIn('foo', ''.join(form.bound_fields['users'].errors))
    self.assertIn('bar', ''.join(form.bound_fields['users'].errors))

    # Test for no errors if valid users given
    self.createProfile()
    self.profile_helper.createDeveloper()

    name_a = ndb.Key.to_old_key(dummy_student_a).name()
    name_b = ndb.Key.to_old_key(dummy_org_mentor_b).name()
    postdata = {
        'recipients_type': conversation_model.PROGRAM,
        'users': '["%s", "%s"]' % (name_a, name_b),
        }
    data = _getRequestData(self.profile, postdata=postdata)
    form = gciconversation_create_view.ConversationCreateForm(data)
    self.assertFalse(form.is_valid())
    self.assertEmpty(form.bound_fields['users'].errors)

    # Test for correct errors in a mostly blank form for recipients_type
    # 'Program'
    self.createProfile()
    self.profile_helper.createDeveloper()

    postdata = {
        'recipients_type': conversation_model.PROGRAM,
        'users': '[]',
        }
    data = _getRequestData(self.profile, postdata=postdata)
    form = gciconversation_create_view.ConversationCreateForm(data)
    self.assertFalse(form.is_valid())
    self.assertEmpty(form.bound_fields['recipients_type'].errors)
    self.assertEmpty(form.bound_fields['users'].errors)
    self.assertIn('required', ''.join(form.bound_fields['subject'].errors))
    self.assertIn(
        'required', ''.join(form.bound_fields['message_content'].errors))
    self.assertEmpty(form.bound_fields['organization'].errors)
    self.assertEmpty(form.bound_fields['organization_roles'].errors)
    self.assertIn(
        'specified', ''.join(form.bound_fields['program_roles'].errors))

    # Test for correct errors in a mostly blank form for recipients_type
    # 'Organization'
    self.createProfile()
    self.profile_helper.createDeveloper()

    postdata = {
        'recipients_type': conversation_model.ORGANIZATION,
        'users': '[]',
        }
    data = _getRequestData(self.profile, postdata=postdata)
    form = gciconversation_create_view.ConversationCreateForm(data)
    self.assertFalse(form.is_valid())
    self.assertEmpty(form.bound_fields['recipients_type'].errors)
    self.assertEmpty(form.bound_fields['users'].errors)
    self.assertIn('required', ''.join(form.bound_fields['subject'].errors))
    self.assertIn(
        'required', ''.join(form.bound_fields['message_content'].errors))
    self.assertIn(
        'specified', ''.join(form.bound_fields['organization'].errors))
    self.assertIn(
        'specified', ''.join(form.bound_fields['organization_roles'].errors))
    self.assertEmpty(form.bound_fields['program_roles'].errors)

    # Test for invalid errors
    self.createProfile()
    self.profile_helper.createDeveloper()

    postdata = {
        'recipients_type': conversation_model.USER,
        'users': '[]',
        'message_content': '  \t\r\n<h1></h1>  ',
        'subject': '  <b>   </b> ',
        }
    data = _getRequestData(self.profile, postdata=postdata)
    form = gciconversation_create_view.ConversationCreateForm(data)
    self.assertFalse(form.is_valid())
    self.assertIn('specified', ''.join(form.bound_fields['users'].errors))
    self.assertIn('blank', ''.join(form.bound_fields['subject'].errors))
    self.assertIn('blank', ''.join(form.bound_fields['message_content'].errors))

    # Test that a conversation is correctly created for specific users.
    # Whitespace is added to the start and end of subject and content to
    # make sure it is stripped.
    self.createProfile()
    self.profile_helper.createDeveloper()

    name_a = ndb.Key.to_old_key(dummy_student_a).name()
    name_b = ndb.Key.to_old_key(dummy_org_mentor_b).name()
    subject = 'Hello world!'
    content = '<h1>Foo</h1><p>Bar</p>'
    postdata = {
        'recipients_type': conversation_model.USER,
        'users': '["%s", "%s"]' % (name_a, name_b),
        'subject': '  \r\n\t  %s  \n ' % subject,
        'message_content': '  \r\n\t  %s  \n ' % content,
        }
    data = _getRequestData(self.profile, postdata=postdata)
    form = gciconversation_create_view.ConversationCreateForm(data)
    self.assertTrue(form.is_valid())
    conversation = form.create()
    self.assertConversation(
        conversation.key, recipients_type=conversation_model.USER,
        creator=self.user_key, subject=subject, message_content=content,
        auto_update_users=False,
        users=[self.user_key, dummy_student_a, dummy_org_mentor_b])

    # Test that a conversation is correctly created for users with specific
    # roles within the program.
    self.createProfile()
    self.profile_helper.createDeveloper()

    postdata = {
        'recipients_type': conversation_model.PROGRAM,
        'users': '[]',
        'program_roles': [
              gciconversation_create_view.ROLE_PROGRAM_MENTORS,
              gciconversation_create_view.ROLE_PROGRAM_STUDENTS,
            ],
        'subject': subject,
        'message_content': content,
        }
    data = _getRequestData(self.profile, postdata=postdata)
    form = gciconversation_create_view.ConversationCreateForm(data)
    self.assertTrue(form.is_valid())
    conversation = form.create()
    self.assertConversation(
        conversation.key, recipients_type=conversation_model.PROGRAM,
        creator=self.user_key, subject=subject, message_content=content,
        include_students=True, include_mentors=True, include_admins=False,
        include_winners=False, auto_update_users=False, users=[
            self.user_key, dummy_org_mentor_a, dummy_org_mentor_b,
            dummy_org_mentor_ab, dummy_student_a, dummy_student_b,
            dummy_student_org_mentor_c, dummy_winner_a, dummy_winner_b])

    # Test that a conversation is correctly created for users with specific
    # roles within an organization. Also tests that it saves auto_update_users.
    self.createProfile()
    self.profile_helper.createDeveloper()

    postdata = {
        'recipients_type': conversation_model.ORGANIZATION,
        'users': '[]',
        'organization': str(self.org_b.key()),
        'organization_roles': [
              gciconversation_create_view.ROLE_ORGANIZATION_MENTORS,
              gciconversation_create_view.ROLE_ORGANIZATION_WINNERS,
            ],
        'subject': subject,
        'message_content': content,
        'auto_update_users': 'on',
        }
    data = _getRequestData(self.profile, postdata=postdata)
    form = gciconversation_create_view.ConversationCreateForm(data)
    self.assertTrue(form.is_valid())
    conversation = form.create()
    self.assertConversation(
        conversation.key, recipients_type=conversation_model.ORGANIZATION,
        creator=self.user_key, subject=subject, message_content=content,
        include_students=False, include_mentors=True, include_admins=False,
        organization=ndb.Key.from_old_key(self.org_b.key()),
        include_winners=True, auto_update_users=True,
        users=[
            self.user_key, dummy_org_mentor_b, dummy_org_mentor_ab,
            dummy_winner_b])
