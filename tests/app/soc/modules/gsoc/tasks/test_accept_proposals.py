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

from soc.modules.gsoc.models import program as program_model
from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.models import organization as org_model

from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import profile_utils
from tests import program_utils
from tests import test_utils


ACCEPT_URL = '/tasks/gsoc/accept_proposals/accept'
REJECT_URL = '/tasks/gsoc/accept_proposals/reject'
MAIN_URL = '/tasks/gsoc/accept_proposals/main'

class AcceptProposalsTest(
    test_utils.MailTestCase, test_utils.GSoCDjangoTestCase,
    test_utils.TaskQueueTestCase):
  """Tests for accept proposals task."""

  def setUp(self):
    super(AcceptProposalsTest, self).setUp()
    self.init()
    self._createHost()
    self._createMentor()
    self._acceptProposals()

  def _createHost(self):
    """Sets program host."""
    self.host = self.profile_helper
    self.host.createHost()
    self.host.createProfile()

  def _createMentor(self):
    """Creates a mentor for default organization."""
    self.mentor = profile_utils.GSoCProfileHelper(self.gsoc, self.dev_test)
    self.mentor.createOtherUser('mentor@example.com')
    self.mentor.createMentor(self.org)
    self.mentor.notificationSettings()

  def _createStudent(self, email, n_proposals):
    """Creates a student with proposals."""
    student = profile_utils.GSoCProfileHelper(self.gsoc, self.dev_test)
    student.createOtherUser(email)
    student.createStudentWithProposals(
        self.org, self.mentor.profile, n=n_proposals)
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

    self.org.slots = 5
    self.org.put()

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
            'org_key': urllib.quote_plus(self.org.key().id_or_name())
            }
        self.assertEqual(expected_params, task['params'])

      elif task['url'] == MAIN_URL:
        q = org_model.GSoCOrganization.all()
        q.filter('scope', self.gsoc)
        q.filter('status', 'active')
        q.get()
        expected_params = {
            'org_cursor': q.cursor(),
            'program_key': urllib.quote_plus(self.gsoc.key().name())
            }

        # as we can't know XSRF token, ignore it
        self.assertNotEqual(task['params'].get('xsrf_token'), None)
        task_params = task['params'].copy()
        del task_params['xsrf_token']

        self.assertEqual(expected_params, task_params)

  def testAcceptProposals(self):
    """Tests accept task for an organization."""
    properties = {
        'parent': self.gsoc,
    }
    self.seed(program_model.GSoCProgramMessages, properties)

    # assert current status of proposal to be accepted
    self.assertEqual(self.student1_proposals[0].status, 'pending')

    post_data = {'org_key': self.org.key().name(),
                 'program_key': self.gsoc.key().name()}
    response = self.post(ACCEPT_URL, post_data)

    # assert accepted student got proper emails
    self.assertEqual(response.status_code, httplib.OK)
    self.assertEmailSent(to=self.student1.profile.email,
                         subject='Congratulations!')
    self.assertEmailSent(to=self.student1.profile.email,
                         subject='Welcome to %s' % self.gsoc.name)
    self.assertEmailNotSent(to=self.student2.profile.email)

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
            'org_key': urllib.quote_plus(self.org.key().name()),
            'program_key': urllib.quote_plus(self.gsoc.key().name())
            }

        # ignore xsrf token
        self.assertNotEqual(task['params'].get('xsrf_token'), None)
        task_params = task['params'].copy()
        del task_params['xsrf_token']

        self.assertEqual(expected_params, task_params)

    # test reject proposals
    post_data = {'org_key': self.org.key().name(),
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
    self.assertEmailSent(to=self.student2.profile.email,
        subject='Thank you for applying to %s' % self.gsoc.name)
    # assert student2 got no accept email
    self.assertEmailNotSent(to=self.student2.profile.email,
        subject='Congratulations!')
    # assert student1 got a reject email (already got an accept mail)
    self.assertEmailSent(to=self.student1.profile.email,
        subject='Thank you for applying to %s' % self.gsoc.name)

    # assert no projects are created for rejected student
    projects = project_model.GSoCProject.all().ancestor(self.student2.profile)
    self.assertEqual(projects.count(), 0)


class ConvertProposalsTest(
    test_utils.GSoCDjangoTestCase, test_utils.TaskQueueTestCase):
  """Unit tests for convertProposals function."""

  def setUp(self):
    super(ConvertProposalsTest, self).setUp()
    self.init()

    # seed a new program
    program = self.program = program_utils.GSoCProgramHelper().createProgram()

    # seed a few organizations
    org_properties = {
        'program': program,
        'status': 'active',
        }
    self.org_keys = []
    for _ in range(5):
      self.org_keys.append(seeder_logic.seed(
          org_model.GSoCOrganization, org_properties).key())

    # create post data that will be sent to tasks
    self.post_data = {
        'program_key': program.key().name()
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
    self.assertEqual(len(org_key_names), 5)

    # there should be an entry for every org
    expected_org_key_names = set([org_key.name() for org_key in self.org_keys])
    self.assertEqual(expected_org_key_names, org_key_names)
