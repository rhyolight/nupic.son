# Copyright 2011 the Melange authors.
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

"""Tests for accept_proposals task."""

import httplib
import urllib

from google.appengine.ext import ndb

from melange.models import organization as org_model

from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import proposal as proposal_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic

from summerofcode.models import organization as soc_org_model

from tests import org_utils
from tests import profile_utils
from tests import program_utils
from tests import test_utils


ACCEPT_URL = '/tasks/gsoc/accept_proposals/accept'
REJECT_URL = '/tasks/gsoc/accept_proposals/reject'
MAIN_URL = '/tasks/gsoc/accept_proposals/main'

TEST_SLOT_ALLOCATION = 5

class AcceptProposalsTest(
    test_utils.GSoCDjangoTestCase, test_utils.TaskQueueTestCase):
  """Tests for accept proposals task."""

  def setUp(self):
    super(AcceptProposalsTest, self).setUp()
    self.init()

    # the organization should already be accepted and have slots allocated
    self.org.status = org_model.Status.ACCEPTED
    self.org.slot_allocation = TEST_SLOT_ALLOCATION
    self.org.put()

    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    self._createMentor()
    self._acceptProposals()

  def _createMentor(self):
    """Creates a mentor for default organization."""
    self.mentor = profile_utils.seedGSoCProfile(
        self.program, mentor_for=[self.org.key.to_old_key()])

  def _createStudent(self, email, n_proposals):
    """Creates a student with proposals."""
    student = profile_utils.GSoCProfileHelper(self.gsoc, self.dev_test)
    student.createOtherUser(email)
    student.createStudentWithProposals(
        self.org, self.mentor, n=n_proposals)
    student.notificationSettings()
    return student

  def _acceptProposals(self):
    """Set student proposals' acceptance state and make sure the organization
    has slots available.
    """
    self.student1 = self._createStudent(
        'student1@example.com', n_proposals=2)
    self.student1_proposals = proposal_model.GSoCProposal.all().ancestor(
        self.student1.profile)
    self.student2 = self._createStudent(
        'student2@example.com', n_proposals=3)
    self.student2_proposals = proposal_model.GSoCProposal.all().ancestor(
        self.student2.profile)

    self.assertEqual(self.student1_proposals.count(), 2)
    self.assertEqual(self.student2_proposals.count(), 3)

    # accept 1 of 2 proposal of student1
    proposal1 = self.student1_proposals[0]
    proposal1.accept_as_project = True
    proposal1.put()

    proposal2 = self.student1_proposals[1]
    proposal2.accept_as_project = False
    proposal2.put()

    # reject all proposals of student2
    for proposal in self.student2_proposals:
      proposal.accept_as_project = False
      proposal.put()

    self.timeline_helper.studentsAnnounced()

  def testConvertProposals(self):
    """Tests convert proposal task runs successfully."""
    post_data = {'program_key': self.gsoc.key().name()}
    response = self.post(MAIN_URL, post_data)
    self.assertEqual(response.status_code, httplib.OK)

    # assert accept task started for first org
    self.assertTasksInQueue(n=1, url=ACCEPT_URL)

    # assert main task started for next org
    self.assertTasksInQueue(n=1, url=MAIN_URL)

    # assert parameters to tasks
    for task in self.get_tasks():
      if task['url'] == ACCEPT_URL:
        expected_params = {
            'org_key': urllib.quote_plus(self.org.key.id())
            }
        self.assertEqual(expected_params, task['params'])

      elif task['url'] == MAIN_URL:
        query = soc_org_model.SOCOrganization.query(
            soc_org_model.SOCOrganization.program ==
                ndb.Key.from_old_key(self.program.key()),
            soc_org_model.SOCOrganization.status == org_model.Status.ACCEPTED)
        _, next_cursor, _ = query.fetch_page(1)

        expected_params = {
            'org_cursor': urllib.quote_plus(next_cursor.urlsafe()),
            'program_key': urllib.quote_plus(self.gsoc.key().name())
            }

        # as we can't know XSRF token, ignore it
        self.assertNotEqual(task['params'].get('xsrf_token'), None)
        task_params = task['params'].copy()
        del task_params['xsrf_token']

        self.assertEqual(expected_params, task_params)

  def testAcceptProposals(self):
    """Tests accept task for an organization."""
    program_utils.seedGSoCProgramMessages(program_key=self.gsoc.key())

    # assert current status of proposal to be accepted
    self.assertEqual(self.student1_proposals[0].status, 'pending')

    post_data = {'org_key': self.org.key.id(),
                 'program_key': self.gsoc.key().name()}
    response = self.post(ACCEPT_URL, post_data)

    # assert accepted student got proper emails
    self.assertEqual(response.status_code, httplib.OK)
    self.assertEmailSent(
        to=self.student1.profile.email, subject='Congratulations!')
    self.assertEmailSent(
        to=self.student1.profile.email,
        subject='Welcome to %s' % self.gsoc.name)
    # TODO(daniel): add assertEmailNotSent to DjangoTestCase
    # self.assertEmailNotSent(to=self.student2.profile.email)

    # assert post status of proposal to be accepted
    self.assertEqual(
        self.student1_proposals[0].status, proposal_model.STATUS_ACCEPTED)

    # assert a project created and associated with accepted student
    projects = project_model.GSoCProject.all().ancestor(self.student1.profile)
    self.assertEqual(projects.count(), 1)
    project = projects.get()
    self.assertEqual(project.status, project_model.STATUS_ACCEPTED)

    # assert reject task is queued
    self.assertTasksInQueue(n=1, url=REJECT_URL)

    # assert parameters to task
    for task in self.get_tasks():
      if task['url'] == REJECT_URL:
        expected_params = {
            'org_key': urllib.quote_plus(self.org.key.id()),
            'program_key': urllib.quote_plus(self.gsoc.key().name())
            }

        # ignore xsrf token
        self.assertNotEqual(task['params'].get('xsrf_token'), None)
        task_params = task['params'].copy()
        del task_params['xsrf_token']

        self.assertEqual(expected_params, task_params)

    # test reject proposals
    post_data = {'org_key': self.org.key.id(),
                 'program_key': self.gsoc.key().name()}
    response = self.post(REJECT_URL, post_data)
    self.assertEqual(response.status_code, httplib.OK)

    # assert post status of proposals
    self.assertEqual(
        self.student1_proposals[0].status, proposal_model.STATUS_ACCEPTED)
    self.assertEqual(
        self.student1_proposals[1].status, proposal_model.STATUS_REJECTED)
    self.assertEqual(
        self.student2_proposals[0].status, proposal_model.STATUS_REJECTED)
    self.assertEqual(
        self.student2_proposals[1].status, proposal_model.STATUS_REJECTED)
    self.assertEqual(
        self.student2_proposals[2].status, proposal_model.STATUS_REJECTED)

    # assert student2 got a reject email
    self.assertEmailSent(
        to=self.student2.profile.email,
        subject='Thank you for applying to %s' % self.gsoc.name)
    # assert student2 got no accept email
    # TODO(daniel): add assertEmailNotSent to DjangoTestCase
    #self.assertEmailNotSent(to=self.student2.profile.email,
    #    subject='Congratulations!')
    # assert student1 got a reject email (already got an accept mail)
    self.assertEmailSent(
        to=self.student1.profile.email,
        subject='Thank you for applying to %s' % self.gsoc.name)

    # assert no projects are created for rejected student
    projects = project_model.GSoCProject.all().ancestor(self.student2.profile)
    self.assertEqual(projects.count(), 0)


TEST_NUMBER_OF_ORGS = 5

class ConvertProposalsTest(
    test_utils.GSoCDjangoTestCase, test_utils.TaskQueueTestCase):
  """Unit tests for convertProposals function."""

  def setUp(self):
    super(ConvertProposalsTest, self).setUp()
    self.init()

    # seed a new program
    self.program = program_utils.seedGSoCProgram()

    # seed a few organizations
    self.org_keys = [
        org_utils.seedSOCOrganization(
            self.program.key(), status=org_model.Status.ACCEPTED).key
        for _ in range(TEST_NUMBER_OF_ORGS)]

    # create post data that will be sent to tasks
    self.post_data = {
        'program_key': self.program.key().name()
        }

  def testNoProgramKey(self):
    # program_key is missing in POST params
    response = self.post(MAIN_URL, {})

    # assert no task started
    self.assertTasksInQueue(n=0, url=ACCEPT_URL)

  def testTaskExecutedForAllOrgs(self):
    # this set will store key names of organizations for which accept
    # proposals task has been enqueued
    org_key_names = set()

    post_data = self.post_data
    while post_data is not None:
      response = self.post(MAIN_URL, post_data)

      # assert task completed with OK status
      self.assertEqual(response.status_code, httplib.OK)

      # try getting a convert task for the next organization
      convert_tasks = self.get_tasks(url=MAIN_URL)

      if convert_tasks:
        # assert that exactly one task was enqueued
        self.assertEqual(len(convert_tasks), 1)

        # this task should be executed next so take its POST data
        post_data = convert_tasks[0]['params'].copy()

        # this is necessary, as get_tasks returns quoted strings
        # the program_key has to be "fixed" here
        post_data.update({
            'program_key': urllib.unquote(post_data['program_key'])
            })

        # assert there is an accept proposals task another organization
        self.assertTasksInQueue(n=1, url=ACCEPT_URL)

        # get an accept proposals task for the organization
        accept_tasks = self.get_tasks(url=ACCEPT_URL)
        params = accept_tasks[0]['params']

        # org_key must be in its params
        self.assertIn('org_key', params)

        # add key to set of enqueued key names
        org_key_names.add(urllib.unquote(params['org_key']))

      else:
        post_data = None

      # remove all the enqueued tasks
      self.clear_task_queue()

    # there should be key name for every organization in the set
    self.assertEqual(len(org_key_names), TEST_NUMBER_OF_ORGS)

    # there should be an entry for every org
    expected_org_key_names = set(org_key.id() for org_key in self.org_keys)
    self.assertEqual(expected_org_key_names, org_key_names)
