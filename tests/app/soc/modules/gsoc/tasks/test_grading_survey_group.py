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

"""Test for the GradingSurveyGroup."""

import httplib

from soc.modules.gsoc.models import grading_project_survey as gps_model
from soc.modules.gsoc.models import grading_project_survey_record as gpsr_model
from soc.modules.gsoc.models import grading_record as gr_model
from soc.modules.gsoc.models import grading_survey_group as gsg_model
from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import project_survey as ps_model
from soc.modules.gsoc.models import project_survey_record as psr_model

from tests import profile_utils
from tests import test_utils
from tests import timeline_utils
from tests.utils import project_utils


class GradingSurveyGroupTest(
    test_utils.GSoCDjangoTestCase, test_utils.TaskQueueTestCase):
  """Tests for accept_proposals task.
  """

  UPDATE_RECORDS_URL = '/tasks/gsoc/grading_record/update_records'
  UPDATE_PROJECTS_URL = '/tasks/gsoc/grading_record/update_projects'
  SEND_URL = '/tasks/gsoc/grading_record/mail_result'

  def setUp(self):
    super(GradingSurveyGroupTest, self).setUp()
    self.init()

    self.mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    self.student = profile_utils.seedNDBStudent(self.program)
    self.project = project_utils.seedProject(
        self.student, self.program.key(), org_key=self.org.key,
        mentor_key=self.mentor.key)

    self.createSurveys()

  def createSurveys(self):
    """Creates the surveys and records required for the tests.
    """
    user = profile_utils.seedNDBUser(host_for=[self.program])
    survey_values = {
        'author': user.key.to_old_key(),
        'title': 'Title',
        'modified_by': user.key.to_old_key(),
        'link_id': 'link_id',
        'scope': self.program.key(),
        'survey_start': timeline_utils.past(),
        'survey_end': timeline_utils.past(),
    }

    self.project_survey = ps_model.ProjectSurvey(
        key_name='key_name', **survey_values)
    self.project_survey.put()

    self.grading_survey = gps_model.GradingProjectSurvey(
        key_name='key_name', **survey_values)
    self.grading_survey.put()

    record_values = {
        'user': self.student.key.parent().to_old_key(),
        'org': self.org.key.to_old_key(),
        'project': self.project,
        'survey': self.project_survey
        }
    self.project_survey_record = psr_model.GSoCProjectSurveyRecord(
        **record_values)
    self.project_survey_record.put()

    self.grading_survey = gps_model.GradingProjectSurvey(**survey_values)
    self.grading_survey.put()

    record_values = {
        'user': self.student.key.parent().to_old_key(),
        'org': self.org.key.to_old_key(),
        'project': self.project,
        'survey': self.grading_survey,
        'grade': True
        }
    self.grading_survey_record = gpsr_model.GSoCGradingProjectSurveyRecord(
        **record_values)
    self.grading_survey_record.put()

    group_values = {
        'name': 'Survey Group Name',
        'grading_survey': self.grading_survey,
        'student_survey': self.project_survey,
        'program': self.program
        }
    self.survey_group = gsg_model.GSoCGradingSurveyGroup(**group_values)
    self.survey_group.put()

    record_values = {
        'grading_survey_group': self.survey_group,
        'mentor_record': self.grading_survey_record,
        'student_record': self.project_survey_record,
        'grade_decision': 'pass'
        }
    self.grading_record = gr_model.GSoCGradingRecord(
        parent=self.project, **record_values)
    self.grading_record.put()

  def testCreateGradingRecord(self):
    """Test creating a GradingRecord."""
    self.grading_record.delete()

    post_data = {'group_key': self.survey_group.key().id_or_name()}

    response = self.post(self.UPDATE_RECORDS_URL, post_data)

    self.assertResponseOK(response)
    self.assertTasksInQueue(n=1, url=self.UPDATE_RECORDS_URL)

    record = gr_model.GSoCGradingRecord.all().get()
    self.assertFalse(record is None)
    self.assertEqual(record.grade_decision, 'pass')

  def testDoesNotCreateGradingRecordForWithdrawnProject(self):
    # create another project and mark it withdrawn
    student = profile_utils.seedNDBStudent(self.program)

    project_utils.seedProject(
        student, self.program.key(), org_key=self.org.key,
        mentor_key=self.mentor.key, status='withdrawn')

    post_data = {'group_key': self.survey_group.key().id_or_name()}

    response = self.post(self.UPDATE_RECORDS_URL, post_data)

    self.assertResponseOK(response)
    self.assertTasksInQueue(n=1, url=self.UPDATE_RECORDS_URL)

    records = gr_model.GSoCGradingRecord.all().fetch(limit=1000)

    # Only one record is expected of the two projects since no record should
    # be created for the withdrawn project
    self.assertEqual(len(records), 1)

  def testUpdateGradingRecord(self):
    """Test updating a GradingRecord.
    """
    self.grading_record.grade_decision = 'undecided'
    self.grading_record.put()

    post_data = {
        'group_key': self.survey_group.key().id_or_name()
        }

    response = self.post(self.UPDATE_RECORDS_URL, post_data)

    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(n=1, url=self.UPDATE_RECORDS_URL)

    record = gr_model.GSoCGradingRecord.all().get()
    self.assertFalse(record is None)
    self.assertEqual(record.grade_decision, 'pass')

  def testUpdateProject(self):
    """Test updating a Project with a GradingRecord's result.
    """
    post_data = {
        'group_key': self.survey_group.key().id_or_name(),
        }

    response = self.post(self.UPDATE_PROJECTS_URL, post_data)

    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(n=1, url=self.UPDATE_PROJECTS_URL)

    project = project_model.GSoCProject.all().get()
    self.assertFalse(project is None)
    self.assertEqual(project.passed_evaluations, [self.grading_record.key()])

    student = self.student.key.get()
    self.assertEqual(student.student_data.passed_evaluations, 1)

  def testUpdateProjectWithSendMail(self):
    """Test updating a Project with a GradingRecord's result and sending mail.
    """
    post_data = {
        'group_key': self.survey_group.key().id_or_name(),
        'send_mail': True,
        }

    response = self.post(self.UPDATE_PROJECTS_URL, post_data)

    self.assertEqual(response.status_code, httplib.OK)
    self.assertTasksInQueue(n=1, url=self.UPDATE_PROJECTS_URL)
    self.assertTasksInQueue(n=1, url=self.SEND_URL)

    project = project_model.GSoCProject.all().get()
    self.assertFalse(project is None)
    self.assertEqual(project.passed_evaluations, [self.grading_record.key()])

    student = self.student.key.get()
    self.assertEqual(student.student_data.passed_evaluations, 1)

  def testSendMail(self):
    """Test sending mail about a GradingRecord's result."""
    post_data = {'record_key': str(self.grading_record.key())}

    response = self.post(self.SEND_URL, post_data)

    self.assertResponseOK(response)
    # URL explicitly added since the email task is in there
    self.assertTasksInQueue(n=0, url=self.SEND_URL)
    self.assertEmailSent(to=self.student.contact.email)
