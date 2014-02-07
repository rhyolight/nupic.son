# Copyright 2014 the Melange authors.
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

"""Tests for mentor evaluation views."""

from tests import profile_utils
from tests import survey_utils
from tests import test_utils
from tests.utils import project_utils


def _getMentorEvaluationTakePageUrl(program, evaluation, project):
  """Returns the URL to Mentor Evaluation Take page.

  Args:
    program: Program entity.
    evaluation: Survey entity.
    project: Project entity.

  Returns:
    A string containing the URL to Mentor Evaluation Take page.
  """
  return '/gsoc/eval/mentor/%s/%s/%s/%s' % (
      program.key().name(), evaluation.link_id,
      project.parent_key().parent().name(), str(project.key().id()))


class GSoCMentorEvaluationTakePageTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for GSoCMentorEvaluationTakePage class."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    self.init()
    self.evaluation_helper = survey_utils.SurveyHelper(self.gsoc, self.dev_test)

  def assertEvaluationTakeTemplateUsed(self, response):
    """Asserts that all the evaluation take templates were used."""
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/form_base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_form.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_evaluation_take.html')

  def testPageLoads(self):
    """Tests that the page loads properly."""
    evaluation = self.evaluation_helper.createMentorEvaluation()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    student = profile_utils.seedSOCStudent(self.program)
    project = project_utils.seedProject(
        student, self.program.key(), org_key=self.org.key,
        mentor_key=mentor.key)

    # test mentor evaluation show GET for a mentor of the project
    response = self.get(
        _getMentorEvaluationTakePageUrl(self.program, evaluation, project))
    self.assertResponseOK(response)
    self.assertEvaluationTakeTemplateUsed(response)
