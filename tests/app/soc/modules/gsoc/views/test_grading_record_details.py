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

"""Tests for grading record details views.
"""


from soc.modules.gsoc.logic import grading_record
from soc.modules.gsoc.models import grading_survey_group as gsg_model
from soc.modules.gsoc.models import project as project_model

from tests import profile_utils
from tests import survey_utils
from tests import test_utils


GRADING_SURVEY_GROUP_NAME = 'Test Grading Survey Group'


class GradingGroupCreateTest(test_utils.GSoCDjangoTestCase):
  """Test GradingGroupSurvey creation page.
  """

  def setUp(self):
    self.init()
    self.profile_helper.createHost()

    evaluation_helper = survey_utils.SurveyHelper(self.gsoc, self.dev_test)
    midterm_prop = {'link_id': 'midterm'}
    self.grading_survey = evaluation_helper.createMentorEvaluation(
            override=midterm_prop)
    self.student_survey = evaluation_helper.createStudentEvaluation(
            override=midterm_prop)

  def testCreateGradingSurveyGroupGet(self):
    """Tests the GET request to the create page.
    """
    response = self.get(self.getUrl())
    self.assertResponseOK(response)
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(
        response, 'modules/gsoc/grading_record/create_group.html')

  def testCreateGradingSurveyGroup(self):
    """Tests the request to create a group.
    """
    # Create a group for the midterm eval.
    response = self.buttonPost(self.getUrl(), 'midterm')

    group = gsg_model.GSoCGradingSurveyGroup.all().get()
    self.assertResponseRedirect(response, self.getOverviewUrl(group))

    expected_name = '%s - Midterm Evaluation' %self.program.name
    self.assertEqual(group.name, expected_name)
    self.assertEqual(group.program.key(), self.program.key())
    self.assertEqual(group.grading_survey.key(), self.grading_survey.key())
    self.assertEqual(group.student_survey.key(), self.student_survey.key())

  def testCreateGradingSurveyGroupRedirectsWhenExists(self):
    """Tests that the create page redirects when the group already exists.
    """
    properties = {
        'name': GRADING_SURVEY_GROUP_NAME,
        'program': self.program,
        'grading_survey': self.grading_survey,
        'student_survey': self.student_survey,
    }
    group = self.seed(gsg_model.GSoCGradingSurveyGroup, properties)

    response = self.buttonPost(self.getUrl(), 'midterm')
    self.assertResponseRedirect(response, self.getOverviewUrl(group))

  def testCreateGradingSurveyGroupErrorsWhenEvalDoesNotExist(self):
    """Tests that the create page returns an error when the group can not be
    created.
    """
    response = self.buttonPost(self.getUrl(), 'final')
    self.assertResponseRedirect(response, self.getUrl() + '?err=1')

  def testCreateGradingSurveyGroupBadRequestOnInvalidInput(self):
    """Tests that a BadRequest response is returned on invalid input data.
    """
    response = self.buttonPost(self.getUrl(), 'notARealButton')
    self.assertResponseBadRequest(response)

  def getUrl(self):
    return '/gsoc/grading_records/group/%s' % self.program.key().name()

  def getOverviewUrl(self, group):
    return '/gsoc/grading_records/overview/%s/%d' % (
        self.program.key().name(), group.key().id())


class GradingRecordsOverviewTest(test_utils.GSoCDjangoTestCase):
  """Test grading records overview list page.
  """

  def setUp(self):
    self.init()
    self.profile_helper.createHost()
    self.timeline_helper.studentsAnnounced()

  def createGradingSurveyGroup(self):
    """Create the grading survey group used to manager evaluations.
    """
    evaluation_helper = survey_utils.SurveyHelper(self.gsoc, self.dev_test)
    properties = {
        'name': GRADING_SURVEY_GROUP_NAME,
        'program': self.program,
        'grading_survey': evaluation_helper.createMentorEvaluation(),
        'student_survey': evaluation_helper.createStudentEvaluation(),
    }
    return self.seed(gsg_model.GSoCGradingSurveyGroup, properties)

  def assertGradingRecordsOverviewTemplatesUsed(self, response):
    """Asserts that all templates from the withdraw projects page were used
    and all contexts were passed
    """
    self.assertIn('base_layout', response.context)
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response,
        'modules/gsoc/grading_record/overview.html')

  def testGradingRecordsOverviewGet(self):
    grading_survey_group = self.createGradingSurveyGroup()
    url = '/gsoc/grading_records/overview/%s/%d' % (
        self.program.key().name(), grading_survey_group.key().id())
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertGradingRecordsOverviewTemplatesUsed(response)

    # list response without any projects
    response = self.getListResponse(url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(0, len(data))

    # list response with projects
    mentor = profile_utils.seedGSoCProfile(
        self.program, mentor_for=[self.org.key.to_old_key()])

    self.profile_helper.createStudentWithProposal(self.org, mentor)
    self.profile_helper.createStudentWithProject(self.org, mentor)

    student_profile_helper = profile_utils.GSoCProfileHelper(
        self.gsoc, self.dev_test)
    student_profile_helper.createStudentWithProposal(self.org, mentor)
    student_profile_helper.createStudentWithProject(self.org, mentor)

    project = project_model.GSoCProject.all().ancestor(
        self.profile_helper.profile).get()
    grading_record.updateOrCreateRecordsFor(grading_survey_group, [project])

    response = self.getListResponse(url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(1, len(data))
