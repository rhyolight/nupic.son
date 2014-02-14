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

"""Unit tests for project manage view."""

from datetime import date

from soc.modules.gsoc.models import project_survey as project_survey_model

from summerofcode.logic import survey as survey_logic
from summerofcode.views import project_manage as project_manage_view

from tests import profile_utils
from tests import survey_utils
from tests import test_utils
from tests.utils import project_utils


class ManageProjectProgramAdminViewTest(test_utils.GSoCDjangoTestCase):
  """Unit tests for ManageProjectAdminView class."""

  def setUp(self):
    self.init()

  def _seedProjectData(self):
    # create a mentor
    self.mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])

    # create a student with a project
    self.student = profile_utils.seedSOCStudent(self.program)
    self.project = project_utils.seedProject(
        self.student, self.program.key(), org_key=self.org.key,
        mentor_key=self.mentor.key)

  def _getUrl(self, project):
    return '/gsoc/project/manage/admin/%s/%s' % (
        project.parent_key().name(), project.key().id())

  def testLoneUserAccessForbidden(self):
    """Tests that users without profiles cannot access the page."""
    self.profile_helper.createUser()
    self._seedProjectData()

    response = self.get(self._getUrl(self.project))
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testStudentAccessForbidden(self):
    """Tests that students cannot access the page."""
    # try to access the page as a student who owns a project
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedNDBStudent(self.program, user=user)

    # create a project
    project = project_utils.seedProject(
        student, self.program.key(), org_key=self.org.key)

    response = self.get(self._getUrl(project))
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testMentorAccessForbidden(self):
    """Tests that mentors cannot access the page."""
    # try to access the page as a mentor who mentor a project
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    # create a student with a project
    student = profile_utils.seedNDBStudent(self.program)
    project = project_utils.seedProject(
        student, self.program.key(), org_key=self.org.key,
        mentor_key=mentor.key)

    response = self.get(self._getUrl(project))
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testOrgAdminAccessForbidden(self):
    """Tests that org admins cannot access the page."""
    # try to access the page as org admin for organization project
    self._seedProjectData()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    response = self.get(self._getUrl(self.project))
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def testProgramAdminAccessGranted(self):
    """Tests that program hosts can access the page."""
    self._seedProjectData()

    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    response = self.get(self._getUrl(self.project))
    self.assertResponseOK(response)

  def testExtensionForms(self):
    """Tests that the response contains extension adequate forms."""
    self._seedProjectData()

    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    # check that no forms are present if there are no evaluations
    response = self.get(self._getUrl(self.project))
    self.assertListEqual(response.context['extension_forms'], [])

    # check that only mideterm form is present for midterm evaluation
    properties = {'link_id': project_survey_model.MIDTERM_EVAL}
    survey = survey_utils.SurveyHelper(
        self.gsoc, False).createStudentEvaluation(override=properties)
    response = self.get(self._getUrl(self.project))
    self.assertIn(project_manage_view.MIDTERM_EXTENSION_FORM_NAME,
        [form.name for form in response.context['extension_forms']])
    self.assertNotIn(project_manage_view.FINAL_EXTENSION_FORM_NAME,
        [form.name for form in response.context['extension_forms']])

    # check that only final form is present for final evaluation
    survey.delete()
    properties = {'link_id': project_survey_model.FINAL_EVAL}
    survey = survey_utils.SurveyHelper(
        self.gsoc, False).createStudentEvaluation(override=properties)
    response = self.get(self._getUrl(self.project))
    self.assertNotIn(project_manage_view.MIDTERM_EXTENSION_FORM_NAME,
        [form.name for form in response.context['extension_forms']])
    self.assertIn(project_manage_view.FINAL_EXTENSION_FORM_NAME,
        [form.name for form in response.context['extension_forms']])

    # check that both forms are present for two evaluations
    properties = {'link_id': project_survey_model.MIDTERM_EVAL}
    survey_utils.SurveyHelper(
        self.gsoc, False).createStudentEvaluation(override=properties)
    response = self.get(self._getUrl(self.project))
    self.assertIn(project_manage_view.MIDTERM_EXTENSION_FORM_NAME,
        [form.name for form in response.context['extension_forms']])
    self.assertIn(project_manage_view.FINAL_EXTENSION_FORM_NAME,
        [form.name for form in response.context['extension_forms']])

  def testPersonalExtensionIsSet(self):
    """Tests that personal extension is set for an evaluation."""
    self._seedProjectData()

    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    # seed midterm evaluation
    properties = {'link_id': project_survey_model.MIDTERM_EVAL}
    survey = survey_utils.SurveyHelper(
        self.gsoc, False).createStudentEvaluation(override=properties)

    # set personal extension
    start_date = date.today()
    end_date = date.today()
    post_data = {
        project_manage_view.MIDTERM_EXTENSION_FORM_NAME: 'test button',
        'start_date': unicode(start_date),
        'end_date': unicode(end_date)
        }
    response = self.post(self._getUrl(self.project), post_data)
    self.assertResponseRedirect(response)

    # check if personal extension is set properly
    extension = survey_logic.getPersonalExtension(
        self.student.key, survey.key())
    self.assertIsNotNone(extension)
    self.assertEqual(start_date, extension.start_date.date())
    self.assertEqual(end_date, extension.end_date.date())

  def testPersonalExtensionIsSetWithEmptyDate(self):
    """Tests that personal extension is set even if a date is empty."""
    self._seedProjectData()

    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    # seed midterm evaluation
    properties = {'link_id': project_survey_model.MIDTERM_EVAL}
    survey = survey_utils.SurveyHelper(
        self.gsoc, False).createStudentEvaluation(override=properties)

    # set personal extension with no end date
    start_date = date.today()
    post_data = {
        project_manage_view.MIDTERM_EXTENSION_FORM_NAME: 'test button',
        'start_date': unicode(start_date),
        'end_date': unicode('')
        }
    response = self.post(self._getUrl(self.project), post_data)
    self.assertResponseRedirect(response)

    # check if personal extension is set properly
    extension = survey_logic.getPersonalExtension(
        self.student.key, survey.key())
    self.assertIsNotNone(extension)
    self.assertEqual(start_date, extension.start_date.date())
    self.assertIsNone(extension.end_date)

    # update the extension - this time with no start date
    end_date = date.today()
    post_data = {
        project_manage_view.MIDTERM_EXTENSION_FORM_NAME: 'test button',
        'start_date': unicode(''),
        'end_date': unicode(end_date)
        }
    response = self.post(self._getUrl(self.project), post_data)
    self.assertResponseRedirect(response)

    # check if personal extension is set properly
    updated_extension = survey_logic.getPersonalExtension(
        self.student.key, survey.key())
    self.assertIsNotNone(updated_extension)
    self.assertIsNone(updated_extension.start_date)
    self.assertEqual(end_date, updated_extension.end_date.date())

    # check that updated extension is represented by the same entity
    self.assertEqual(extension.key, updated_extension.key)
