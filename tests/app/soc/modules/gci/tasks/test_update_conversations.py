# Copyright 2013 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for update_conversations task."""

import httplib
import urllib

from google.appengine.ext import ndb

from tests import test_utils
from tests.utils import conversation_utils

from soc.models import conversation as conversation_model

from soc.modules.gci.logic import conversation as gciconversation_logic
from soc.modules.gci.tasks import update_conversations


TASK_URL = '/tasks/gci/task/update_conversations'


class UpdateConversationsTest(
    test_utils.GCIDjangoTestCase, test_utils.TaskQueueTestCase):
  """Tests for update conversations task."""

  def setUp(self):
    super(UpdateConversationsTest, self).setUp()
    self.init()

    self.conv_utils = conversation_utils.GCIConversationHelper()
    self.program_key = self.conv_utils.program_key

  def testUpdateConversations(self):
    """Tests that the updateConversations task correctly adds a user to all
    conversations they should be in but aren't, and removes them from
    conversations they shouldn't be in.
    """

    def run_update_task(user_key, program_key):
      """Runs the task and test that it runs correctly.

      Args:
        user_key: Key (ndb) of User.
        program_key: Key (ndb) of GCIProgram.
      """
      update_conversations.spawnUpdateConversationsTask(user_key, program_key)
      self.assertTasksInQueue(n=1, url=TASK_URL)

      for task in self.get_tasks():
        if task['url'] == TASK_URL:
          params = task['params']
          self.assertIn('user_key', params)
          self.assertEqual(params['user_key'], user_key.urlsafe())
          self.assertIn('program_key', params)
          self.assertEqual(params['program_key'], program_key.urlsafe())

      # Test task
      post_data = {
          'user_key': user_key.urlsafe(),
          'program_key': program_key.urlsafe(),
          }
      response = self.post(TASK_URL, post_data)
      self.assertEqual(response.status_code, httplib.OK)

      self.clear_task_queue()

    # Create a couple dummy organizations
    org_keys = map(
        lambda org: ndb.Key.from_old_key(org.key()),
        list(self.conv_utils.program_helper.createNewOrg() for x in range(2)))

    # Create various dummy users
    user_admin_key = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.ADMIN],
        admin_organizations=[org_keys[0]])
    user_mentor_key = self.conv_utils.createUser(
        return_key=True, roles=[conversation_utils.MENTOR],
        mentor_organizations=[org_keys[0], org_keys[1]])
    user_mentor_student_key = self.conv_utils.createUser(
        return_key=True,
        roles=[conversation_utils.MENTOR, conversation_utils.STUDENT])
    user_winner_key = self.conv_utils.createUser(
        return_key=True, winning_organization=org_keys[1],
        roles=[conversation_utils.WINNER, conversation_utils.STUDENT])
    
    # Conversation for program admins and mentors
    conv_a = self.conv_utils.createConversation(subject='')
    conv_a.recipients_type = conversation_model.PROGRAM
    conv_a.include_admins = True
    conv_a.include_mentors = True
    conv_a.put()

    # Conversation for first org's admins
    conv_b = self.conv_utils.createConversation(subject='')
    conv_b.recipients_type = conversation_model.ORGANIZATION
    conv_b.organization = org_keys[0]
    conv_b.include_admins = True
    conv_b.put()

    # Conversation for second org's mentors
    conv_c = self.conv_utils.createConversation(subject='')
    conv_c.recipients_type = conversation_model.ORGANIZATION
    conv_c.organization = org_keys[1]
    conv_c.include_mentors = True
    conv_c.put()

    # Conversation for program mentors and students
    conv_d = self.conv_utils.createConversation(subject='')
    conv_d.recipients_type = conversation_model.PROGRAM
    conv_d.include_mentors = True
    conv_d.include_students = True
    conv_d.put()

    # Conversation for program students, created by a non-student
    conv_e = self.conv_utils.createConversation(subject='')
    conv_e.creator = user_admin_key
    conv_e.recipients_type = conversation_model.PROGRAM
    conv_e.include_students = True
    conv_e.put()
    self.conv_utils.addUser(conversation=conv_e.key, user=conv_e.creator)

    # Conversation for basically nobody, in which the participants should not
    # be changed after the conversation's creation, and all users are added.
    # This is to ensure that users won't be removed if the conversation's
    # auto_update_users property is False.
    conv_f = self.conv_utils.createConversation(subject='')
    conv_f.recipients_type = conversation_model.PROGRAM
    conv_f.auto_update_users = False
    conv_f.put()
    self.conv_utils.addUser(conversation=conv_f.key, user=user_admin_key)
    self.conv_utils.addUser(conversation=conv_f.key, user=user_mentor_key)
    self.conv_utils.addUser(
        conversation=conv_f.key, user=user_mentor_student_key)
    self.conv_utils.addUser(conversation=conv_f.key, user=user_winner_key)

    # Conversation for that all users fit the criteria to participate in, but
    # should not be added after the converation's creation.
    conv_g = self.conv_utils.createConversation(subject='')
    conv_g.recipients_type = conversation_model.PROGRAM
    conv_g.include_students = True
    conv_g.include_mentors = True
    conv_g.include_admins = True
    conv_g.auto_update_users = False
    conv_g.put()

    # Conversation for program winners, created by a non-winner
    conv_h = self.conv_utils.createConversation(subject='')
    conv_h.recipients_type = conversation_model.PROGRAM
    conv_h.include_winners = True
    conv_h.put()

    # Conversation for winners of first organization
    conv_i = self.conv_utils.createConversation(subject='')
    conv_i.recipients_type = conversation_model.ORGANIZATION
    conv_i.organization = org_keys[0]
    conv_i.include_winners = True
    conv_i.put()

    # Conversation for winners of second organization
    conv_j = self.conv_utils.createConversation(subject='')
    conv_j.recipients_type = conversation_model.ORGANIZATION
    conv_j.organization = org_keys[1]
    conv_j.include_winners = True
    conv_j.put()

    # Refresh each user's conversations
    run_update_task(user_admin_key, self.program_key)
    run_update_task(user_mentor_key, self.program_key)
    run_update_task(user_mentor_student_key, self.program_key)
    run_update_task(user_winner_key, self.program_key)

    # Test that admin user is in the correct conversations
    expected_keys = set([conv_a.key, conv_b.key, conv_e.key, conv_f.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_admin_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that mentor user is in the correct conversations
    expected_keys = set([conv_a.key, conv_c.key, conv_d.key, conv_f.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_mentor_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that mentor/student user is in the correct conversations
    expected_keys = set([conv_a.key, conv_d.key, conv_e.key, conv_f.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_mentor_student_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that winner user is in the correct conversations
    expected_keys = set(
        [conv_d.key, conv_e.key, conv_f.key, conv_h.key, conv_j.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_winner_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Add all three users to all conversations
    self.conv_utils.addUser(conversation=conv_b.key, user=user_mentor_key)
    self.conv_utils.addUser(
        conversation=conv_b.key, user=user_mentor_student_key)
    self.conv_utils.addUser(conversation=conv_c.key, user=user_admin_key)
    self.conv_utils.addUser(
        conversation=conv_c.key, user=user_mentor_student_key)
    self.conv_utils.addUser(conversation=conv_d.key, user=user_admin_key)
    self.conv_utils.addUser(conversation=conv_e.key, user=user_mentor_key)
    self.conv_utils.addUser(
        conversation=conv_h.key, user=user_mentor_student_key)
    self.conv_utils.addUser(conversation=conv_h.key, user=user_mentor_key)
    self.conv_utils.addUser(conversation=conv_h.key, user=user_admin_key)
    self.conv_utils.addUser(
        conversation=conv_i.key, user=user_mentor_student_key)
    self.conv_utils.addUser(conversation=conv_i.key, user=user_mentor_key)
    self.conv_utils.addUser(conversation=conv_i.key, user=user_admin_key)
    self.conv_utils.addUser(
        conversation=conv_j.key, user=user_mentor_student_key)
    self.conv_utils.addUser(conversation=conv_j.key, user=user_mentor_key)
    self.conv_utils.addUser(conversation=conv_j.key, user=user_admin_key)
    self.conv_utils.addUser(conversation=conv_a.key, user=user_winner_key)
    self.conv_utils.addUser(conversation=conv_b.key, user=user_winner_key)
    self.conv_utils.addUser(conversation=conv_c.key, user=user_winner_key)
    self.conv_utils.addUser(conversation=conv_i.key, user=user_winner_key)

    # Test that admin user is in all conversations except for G
    expected_keys = set([
        conv_a.key, conv_b.key, conv_c.key, conv_d.key, conv_e.key, conv_f.key,
        conv_h.key, conv_i.key, conv_j.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_admin_key)))

    self.assertEqual(expected_keys, actual_keys)

    # Test that mentor user is in all conversations except for G
    expected_keys = set([
        conv_a.key, conv_b.key, conv_c.key, conv_d.key, conv_e.key, conv_f.key,
        conv_h.key, conv_i.key, conv_j.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_mentor_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that mentor/student user is in all conversations except for G
    expected_keys = set([
        conv_a.key, conv_b.key, conv_c.key, conv_d.key, conv_e.key, conv_f.key,
        conv_h.key, conv_i.key, conv_j.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_mentor_student_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that winner user is in all conversations except for G
    expected_keys = set([
        conv_a.key, conv_b.key, conv_c.key, conv_d.key, conv_e.key, conv_f.key,
        conv_h.key, conv_i.key, conv_j.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_winner_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Refresh each user's conversations. Because we just added all users to
    # all conversations, refreshing each user should actually remove them from
    # conversations they don't belong to.
    run_update_task(user_admin_key, self.program_key)
    run_update_task(user_mentor_key, self.program_key)
    run_update_task(user_mentor_student_key, self.program_key)
    run_update_task(user_winner_key, self.program_key)

    # Test that admin user is in the correct conversations
    expected_keys = set([conv_a.key, conv_b.key, conv_e.key, conv_f.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_admin_key)))

    self.assertEqual(expected_keys, actual_keys)

    # Test that mentor user is in the correct conversations
    expected_keys = set([conv_a.key, conv_c.key, conv_d.key, conv_f.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_mentor_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that mentor/student user is in the correct conversations
    expected_keys = set([conv_a.key, conv_d.key, conv_e.key, conv_f.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_mentor_student_key)))
    self.assertEqual(expected_keys, actual_keys)

    # Test that winner user is in the correct conversations
    expected_keys = set(
        [conv_d.key, conv_e.key, conv_f.key, conv_h.key, conv_j.key])
    actual_keys = set(map(
        lambda conv_user: conv_user.conversation,
        gciconversation_logic.queryForProgramAndUser(
            program=self.program_key, user=user_winner_key)))
    self.assertEqual(expected_keys, actual_keys)
