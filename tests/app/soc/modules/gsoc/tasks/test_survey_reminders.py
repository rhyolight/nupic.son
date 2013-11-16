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

"""Test for sending Survey reminders."""

from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.models.project_survey import ProjectSurvey

from tests import profile_utils
from tests import test_utils
from tests import timeline_utils


class SurveyRemindersTest(
    test_utils.GSoCDjangoTestCase, test_utils.TaskQueueTestCase):
  """Tests for accept_proposals task.
  """

  SPAWN_URL = '/tasks/gsoc/surveys/send_reminder/spawn'
  SEND_URL = '/tasks/gsoc/surveys/send_reminder/send'

  def setUp(self):
    super(SurveyRemindersTest, self).setUp()
    self.init()
    self.createMentor()
    self.createStudent()
    self.createSurveys()

  def createMentor(self):
    """Creates a new mentor."""
    self.mentor = profile_utils.seedGSoCProfile(
        self.program, mentor_for=[self.org.key()])

  def createStudent(self):
    """Creates a Student with a project.
    """
    profile_helper = profile_utils.GSoCProfileHelper(self.gsoc, self.dev_test)
    profile_helper.createOtherUser('student@example.com')
    self.student = profile_helper.createStudentWithProject(self.org,
                                                           self.mentor)
    self.project = GSoCProject.all().ancestor(self.student).get()

  def createSurveys(self):
    """Creates the surveys and records required for the tests in the old
    format.
    """
    user = profile_utils.seedUser()
    survey_values = {
        'author': user,
        'title': 'Title',
        'modified_by': user,
        'link_id': 'link_id',
        'scope': self.gsoc,
        'survey_start': timeline_utils.past(),
        'survey_end': timeline_utils.past(),
    }

    self.project_survey = ProjectSurvey(key_name='key_name',
                                        **survey_values)
    self.project_survey.put()

    self.grading_survey = GradingProjectSurvey(key_name='key_name',
                                               **survey_values)
    self.grading_survey.put()

  def createWithdrawnProject(self):
    """Creates a project that is withdrawn.
    """
    # list response with projects
    mentor = profile_utils.seedGSoCProfile(
        self.program, mentor_for=[self.org.key()])

    # Create a student with the project.
    student_profile_helper = profile_utils.GSoCProfileHelper(
        self.gsoc, self.dev_test)
    student_profile = student_profile_helper.createStudentWithProject(
        self.org, mentor)

    # Retrieve the project, corresponding proposal.
    project = GSoCProject.all().ancestor(student_profile).get()
    proposal = project.proposal

    # Update the properties for withdrawing the project.
    student_profile.student_info.number_of_projects -= 1
    student_profile.student_info.project_for_orgs.remove(self.org.key())
    project.status = 'withdrawn'
    proposal.status = 'withdrawn'

    # Update the entities.
    student_profile.student_info.put()
    project.put()
    proposal.put()

  def testSpawnSurveyRemindersForProjectSurvey(self):
    """Test spawning reminder tasks for a ProjectSurvey.
    """
    post_data = {
        'program_key': self.gsoc.key().id_or_name(),
        'survey_key': self.project_survey.key().id_or_name(),
        'survey_type': 'project'}

    response = self.post(self.SPAWN_URL, post_data)

    self.assertResponseOK(response)
    self.assertTasksInQueue(n=2)
    self.assertTasksInQueue(n=1, url=self.SPAWN_URL)
    self.assertTasksInQueue(n=1, url=self.SEND_URL)

  def testSpawnSurveyRemindersForGradingSurvey(self):
    """Test spawning reminder tasks for a GradingProjectSurvey.
    """
    post_data = {
        'program_key': self.gsoc.key().id_or_name(),
        'survey_key': self.grading_survey.key().id_or_name(),
        'survey_type': 'grading'}

    response = self.post(self.SPAWN_URL, post_data)

    self.assertResponseOK(response)
    self.assertTasksInQueue(n=2)
    self.assertTasksInQueue(n=1, url=self.SPAWN_URL)
    self.assertTasksInQueue(n=1, url=self.SEND_URL)

  def testSendSurveyReminderForProjectSurvey(self):
    """Test sending out a reminder for a ProjectSurvey.
    """
    post_data = {
        'survey_key': self.project_survey.key().id_or_name(),
        'survey_type': 'project',
        'project_key': str(self.project.key())}

    response = self.post(self.SEND_URL, post_data)

    self.assertResponseOK(response)
    # URL explicitly added since the email task is in there
    self.assertTasksInQueue(n=0, url=self.SEND_URL)
    self.assertEmailSent(to=self.student.email)
    # TODO(daniel): add assertEmailNotSent to DjangoTestCase
    #self.assertEmailNotSent(to=self.mentor.email)

  def testSendSurveyReminderForGradingSurvey(self):
    """Test sending out a reminder for a GradingProjectSurvey.
    """
    post_data = {
        'survey_key': self.grading_survey.key().id_or_name(),
        'survey_type': 'grading',
        'project_key': str(self.project.key())}

    response = self.post(self.SEND_URL, post_data)

    self.assertResponseOK(response)
    # URL explicitly added since the email task is in there
    self.assertTasksInQueue(n=0, url=self.SEND_URL)
    self.assertEmailSent(to=self.mentor.email)
    # TODO(daniel): add assertEmailNotSent to DjangoTestCase
    #self.assertEmailNotSent(to=self.student.email)

  def testDoesNotSpawnProjectSurveyReminderForWithdrawnProject(self):
    """Test withdrawn projects don't spawn reminder tasks for
    student evaluation.

    This covers all the evaluations created (midterm and final).
    """
    self.createWithdrawnProject()
    post_data = {
        'program_key': self.gsoc.key().id_or_name(),
        'survey_key': self.project_survey.key().id_or_name(),
        'survey_type': 'project'}

    response = self.post(self.SPAWN_URL, post_data)

    self.assertResponseOK(response)
    self.assertTasksInQueue(n=2)
    self.assertTasksInQueue(n=1, url=self.SPAWN_URL)
    # We have two projects in datastore and one is withdrawn, so we expect
    # to spawn the task for only one project.
    self.assertTasksInQueue(n=1, url=self.SEND_URL)

  def testDoesNotGradingProjectSurveyReminderForWithdrawnProject(self):
    """Test withdrawn projects don't spawn reminder tasks for
    mentor evaluation.

    This covers all the evaluations created (midterm and final).
    """
    self.createWithdrawnProject()
    self.project.put()
    post_data = {
        'program_key': self.gsoc.key().id_or_name(),
        'survey_key': self.grading_survey.key().id_or_name(),
        'survey_type': 'grading'}

    response = self.post(self.SPAWN_URL, post_data)

    self.assertResponseOK(response)
    self.assertTasksInQueue(n=2)
    self.assertTasksInQueue(n=1, url=self.SPAWN_URL)
    # We have two projects in datastore and one is withdrawn, so we expect
    # to spawn the task for only one project.
    self.assertTasksInQueue(n=1, url=self.SEND_URL)
