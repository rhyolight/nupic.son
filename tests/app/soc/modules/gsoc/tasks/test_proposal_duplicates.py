# Copyright 2011 the Melange authors.
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

import httplib
import urllib

from tests.test_utils import GSoCDjangoTestCase
from tests.test_utils import TaskQueueTestCase

from melange.models import organization as org_model

from soc.modules.gsoc.logic import duplicates as duplicates_logic
from soc.modules.gsoc.models.proposal_duplicates import GSoCProposalDuplicate

from tests import profile_utils
from tests.utils import proposal_utils


_FIRST_STUDENT_NUMBER_OF_DUPLICATES = 2

class ProposalDuplicatesTest(GSoCDjangoTestCase, TaskQueueTestCase):
  """Tests for the tasks that calculates duplicates.
  """

  CALCULATE_URL = '/tasks/gsoc/proposal_duplicates/calculate'
  START_URL = '/tasks/gsoc/proposal_duplicates/start'

  def setUp(self):
    super(ProposalDuplicatesTest, self).setUp()
    self.init()

    self.timeline_helper.studentSignup()

    # set the organization as accepted and allocate some slots
    self.org.status = org_model.Status.ACCEPTED
    self.org.slot_allocation = 10
    self.org.put()

    # the first student has a two duplicates and one non-accepted proposal
    self.student1 = profile_utils.seedNDBStudent(self.program)
    for _ in range(_FIRST_STUDENT_NUMBER_OF_DUPLICATES):
      proposal_utils.seedProposal(
          self.student1.key, self.program.key(), org_key=self.org.key,
          accept_as_project=True)
    proposal_utils.seedProposal(
        self.student1.key, self.program.key(), org_key=self.org.key,
        accept_as_project=False)

    # the other student has two proposals; one of them is to be accepted.
    self.student2 = profile_utils.seedNDBStudent(self.program)
    proposal_utils.seedProposal(
        self.student2.key, self.program.key(), org_key=self.org.key,
        accept_as_project=True)
    proposal_utils.seedProposal(
        self.student2.key, self.program.key(), org_key=self.org.key,
        accept_as_project=False)

  def testStartFailsWhenMissingProgram(self):
    """Test whether start fails to enqueue a calculate task when program is
    missing.
    """
    post_data = {'repeat': 'yes'}

    response = self.post(self.START_URL, post_data)

    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(n=0)

  def testStartFailsWhenMissingRepeat(self):
    """Test that start fails to enqueue a calculate task when repeat is missing.
    """
    post_data = {'program_key': self.gsoc.key().id_or_name()}

    response = self.post(self.START_URL, post_data)

    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(n=0)

  def testStartEnqueuesWhenRepeatIsFalse(self):
    """Test that start enqueues 1 calculate task when repeat is false.
    """
    post_data = {'program_key': self.gsoc.key().id_or_name(),
                 'repeat': 'no'}

    response = self.post(self.START_URL, post_data)

    self.assertEqual(response.status_code, httplib.OK)
    # Assert that there is only 1 task in the queue and check whether the URL
    # matches.
    self.assertTasksInQueue(1)
    self.assertTasksInQueue(n=1, url=self.CALCULATE_URL)

    tasks = self.get_tasks()
    task = tasks[0]
    expected_params = {'program_key':
                       urllib.quote_plus(self.gsoc.key().id_or_name())}
    self.assertEqual(task['params'], expected_params)

    status = duplicates_logic.getOrCreateStatusForProgram(self.gsoc)
    self.assertEqual(status.status, 'processing')


  def testStartEnqueuesWhenRepeatIsTrue(self):
    """Test that start enqueues 1 calculate task and 1 start task when repeat
    is set to true.
    """
    post_data = {'program_key': self.gsoc.key().id_or_name(),
                 'repeat': 'yes'}

    response = self.post(self.START_URL, post_data)

    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(2)
    self.assertTasksInQueue(n=1, url=self.CALCULATE_URL)
    self.assertTasksInQueue(n=1, url=self.START_URL)

    for task in self.get_tasks():
      expected_params = {'program_key':
                         urllib.quote_plus(self.gsoc.key().id_or_name())}
      if task['url'] == self.START_URL:
        expected_params['repeat'] = 'yes'

      self.assertEqual(task['params'], expected_params)

    status = duplicates_logic.getOrCreateStatusForProgram(self.gsoc)
    self.assertEqual(status.status, 'processing')


  def testCalculateFailsWhenMissingProgram(self):
    """Tests that calculates fails when a Program is not present in the POST
    data.
    """
    post_data = {}

    response = self.post(self.CALCULATE_URL, post_data)

    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(n=0)
    self.assertEqual(GSoCProposalDuplicate.all().count(1), 0)

  def testCalculateDuplicatesForSingleOrg(self):
    """Test that calculates properly creates GSoCProposalDuplicate entities for
    a single organization.
    """
    # skip the initialization step
    status = duplicates_logic.getOrCreateStatusForProgram(self.program)
    status.status = 'processing'
    status.put()

    post_data = {'program_key': self.program.key().id_or_name()}

    response = self.post(self.CALCULATE_URL, post_data)

    # must have enqueued itself again successfully
    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(n=1)
    self.assertTasksInQueue(n=1, url=self.CALCULATE_URL)

    # the new task should have a query cursor present
    params = self.get_tasks()[0]['params']
    self.assertTrue(params.has_key('org_cursor'))
    self.assertEqual(params['program_key'],
                     urllib.quote_plus(self.program.key().id_or_name()))

    # 2 duplicates should have been created since there are 2 students
    duplicates = GSoCProposalDuplicate.all().fetch(1000)
    self.assertEqual(len(duplicates), 2)
    for dup in duplicates:
      student_key = GSoCProposalDuplicate.student.get_value_for_datastore(dup)
      if student_key == self.student1.key.to_old_key():
        self.assertTrue(dup.is_duplicate)
      else:
        self.assertFalse(dup.is_duplicate)

    status = duplicates_logic.getOrCreateStatusForProgram(self.program)
    self.assertEqual(status.status, 'processing')


  def testCalculateDuplicatesTerminates(self):
    """Test that calculates terminates properly after going through all orgs.
    """
    # skip the initialization step
    status = duplicates_logic.getOrCreateStatusForProgram(self.gsoc)
    status.status = 'processing'
    status.put()

    post_data = {'program_key': self.gsoc.key().id_or_name()}

    response = self.post(self.CALCULATE_URL, post_data)

    # must have enqueued itself again successfully
    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(n=1)
    self.assertTasksInQueue(n=1, url=self.CALCULATE_URL)

    # this data should be used for the second iteration
    params = self.get_tasks()[0]['params']
    for key, value in params.iteritems():
      params[key] = urllib.unquote_plus(value)

    # clean the queue
    self.clear_task_queue()

    response = self.post(self.CALCULATE_URL, params)

    # only 1 org in test data so task should terminate now
    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(n=0)

    # 1 duplicate should be left after task termination
    duplicates = GSoCProposalDuplicate.all().fetch(1000)
    self.assertEqual(len(duplicates), 1)
    dup = duplicates[0]
    self.assertTrue(dup.is_duplicate)

    student_key = GSoCProposalDuplicate.student.get_value_for_datastore(dup)
    self.assertEqual(student_key, self.student1.key.to_old_key())
    self.assertEqual(len(dup.duplicates), _FIRST_STUDENT_NUMBER_OF_DUPLICATES)

    status = duplicates_logic.getOrCreateStatusForProgram(self.program)
    self.assertEqual(status.status, 'idle')
