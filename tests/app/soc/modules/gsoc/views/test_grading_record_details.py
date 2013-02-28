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


class GradingRecordsOverviewTest(test_utils.GSoCDjangoTestCase):
  """Test grading records overview list page.
  """

  def setUp(self):
    self.init()
    self.data.createHost()
    self.timeline.studentsAnnounced()

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
    self.assertTrue('base_layout' in response.context)
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response,
        'v2/modules/gsoc/grading_record/overview.html')

  def testGradingRecordsOverviewGet(self):
    grading_survey_group = self.createGradingSurveyGroup()
    url = '/gsoc/grading_records/overview/%s/%d' % (
        self.program.key().name(), grading_survey_group.key().id(),)
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertGradingRecordsOverviewTemplatesUsed(response)

    # list response without any projects
    response = self.getListResponse(url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(0, len(data))

    # list response with projects
    mentor_profile_helper = profile_utils.GSoCProfileHelper(
        self.gsoc, self.dev_test)
    mentor_profile_helper.createOtherUser('mentor@example.com')
    mentor = mentor_profile_helper.createMentor(self.org)

    self.data.createStudentWithProposal(self.org, mentor)
    self.data.createStudentWithProject(self.org, mentor)

    student_profile_helper = profile_utils.GSoCProfileHelper(
        self.gsoc, self.dev_test)
    student_profile_helper.createStudentWithProposal(self.org, mentor)
    student_profile_helper.createStudentWithProject(self.org, mentor)

    project = project_model.GSoCProject.all().ancestor(self.data.profile).get()
    grading_record.updateOrCreateRecordsFor(grading_survey_group, [project])

    response = self.getListResponse(url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(1, len(data))
