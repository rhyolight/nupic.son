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

"""Tests for project_detail views."""

from tests import profile_utils
from tests import program_utils
from tests import test_utils

from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.views import project_details


def _createProjectForStudent(program, org, dev_test, student=None):
  """Returns a newly created GSoCProject for the specified student.
  If a new student instance is not provided, a new profile is created.

  Args:
    program: GSoCProgram instance for which the project is to be created
    org: GSoCOrganization instance for which the project is to be created
    dev_test: whether it is dev test environment
    student: the specified GSoCProfile student instance to mentor the project

  Returns:
    the newly created GSoCProject instance
  """
  if not student:
    student_helper = profile_utils.GSoCProfileHelper(program, dev_test)
    student_helper.createOtherUser('student@example.com')
    student = student_helper.createStudent()

  mentor_helper = profile_utils.GSoCProfileHelper(program, dev_test)
  mentor_helper.createOtherUser('mentor@example.com')
  mentor_helper.createMentorWithProject(org, student)

  project = project_model.GSoCProject.all().get()
  project.is_featured = False
  project.status = project_model.STATUS_ACCEPTED
  project.put()

  return project


def _createProjectForMentor(program, org, dev_test, mentor=None):
  """Returns a newly created GSoCProject for the specified mentor.
  If a new mentor instance is not provided, a new profile is created.

  Args:
    program: GSoCProgram instance for which the project is to be created
    org: GSoCOrganization instance for which the project is to be created
    dev_test: whether it is dev test environment
    mentor: the specified GSoCProfile mentor instance to mentor the project

  Returns:
    the newly created GSoCProject instance
  """
  if not mentor:
    mentor_helper = profile_utils.GSoCProfileHelper(program, dev_test)
    mentor_helper.createOtherUser('mentor@example.com')
    mentor = mentor_helper.createMentor(org)

  student_helper = profile_utils.GSoCProfileHelper(program, dev_test)
  student_helper.createOtherUser('student@example.com')
  student_helper.createStudentWithProject(org, mentor)
  project = project_model.GSoCProject.all().get()
  project.is_featured = False
  project.status = project_model.STATUS_ACCEPTED
  project.put()
  return project


class ProjectDetailsTest(test_utils.GSoCDjangoTestCase):
  """Tests project details page.
  """

  def setUp(self):
    super(ProjectDetailsTest, self).setUp()
    self.init()

  def assertProjectDetailsTemplateUsed(self, response):
    """Asserts that all the project details were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(
        response, 'modules/gsoc/project_details/base.html')

  def createProject(self):
    mentor_helper = profile_utils.GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor_helper.createOtherUser('mentor@example.com')
    mentor = mentor_helper.createMentor(self.org)
    student_helper = profile_utils.GSoCProfileHelper(self.gsoc, self.dev_test)
    student_helper.createOtherUser('student@example.com')
    student_helper.createStudentWithProject(self.org, mentor)

    project = project_model.GSoCProject.all().get()
    project.is_featured = False
    project.status = project_model.STATUS_ACCEPTED
    project.put()
    return project

  def testProjectDetails(self):
    self.profile_helper.createStudent()
    self.timeline_helper.studentsAnnounced()

    project = self.createProject()

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        project.parent().user.key().name(),
        project.key().id())

    # test project details GET
    url = '/gsoc/project/' + suffix
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertProjectDetailsTemplateUsed(response)

  def testFeaturedProjectButton(self):
    self.timeline_helper.studentsAnnounced()

    student = profile_utils.GSoCProfileHelper(self.gsoc, self.dev_test)
    student.createOtherUser('student@example.com')
    student.createStudent()

    self.profile_helper.createOrgAdmin(self.org)

    project = self.createProject()

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        project.parent().user.key().name(),
        project.key().id())

    url = '/gsoc/project/featured/' + suffix
    postdata = {'value': 'unchecked'}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    project = project_model.GSoCProject.all().get()
    self.assertEqual(project.is_featured, True)


class ProjectDetailsUpdateTest(test_utils.GSoCDjangoTestCase):
  """Unit tests project details update page."""

  def setUp(self):
    super(ProjectDetailsUpdateTest, self).setUp()
    self.init()

  def _getProjectUpdateUrl(self, project):
    return '/gsoc/project/update/%s/%s' % (
        project.parent_key().name(), project.key().id())

  def testLoneUserAccessForbidden(self):
    self.timeline_helper.studentsAnnounced()
    project = _createProjectForMentor(self.gsoc, self.org, self.dev_test)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testMentorAccessForbidden(self):
    self.timeline_helper.studentsAnnounced()

    mentor = self.profile_helper.createMentor(self.org)
    project = _createProjectForMentor(
        self.gsoc, self.org, self.dev_test, mentor=mentor)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testOrgAdminAccessGranted(self):
    self.timeline_helper.studentsAnnounced()

    self.profile_helper.createOrgAdmin(self.org)
    project = _createProjectForMentor(self.gsoc, self.org, self.dev_test)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertResponseOK(response)

  def testOrgAdminForAnotherOrgForbidden(self):
    self.timeline_helper.studentsAnnounced()

    another_org = self.createOrg()
    self.profile_helper.createOrgAdmin(another_org)
    project = _createProjectForMentor(self.gsoc, self.org, self.dev_test)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testHostAccessGranted(self):
    self.timeline_helper.studentsAnnounced()

    self.profile_helper.createHost()
    project = _createProjectForMentor(self.gsoc, self.org, self.dev_test)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertResponseOK(response)

  def testStudentAccessTheirProjectGranted(self):
    self.timeline_helper.studentsAnnounced()

    student = self.profile_helper.createStudent()
    project = _createProjectForStudent(
        self.gsoc, self.org, self.dev_test, student=student)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertResponseOK(response)

  def testStudentAccessOtherProjectForbidden(self):
    self.timeline_helper.studentsAnnounced()

    student = self.profile_helper.createStudent()
    project = _createProjectForStudent(self.gsoc, self.org, self.dev_test)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)


class TestIsUpdateLinkVisible(test_utils.GSoCTestCase):
  """Unit tests for _isUpdateLinkVisible function."""

  def setUp(self):
    super(TestIsUpdateLinkVisible, self).setUp()
    self.init()

  class MockRequestData(object):
    """Mock class used to simulate RequestData which is passed as argument."""

    def __init__(self, is_host=False, project=None, profile=None):
      self.is_host = is_host
      self.project = project
      self.profile = profile

    def orgAdminFor(self, org_key):
      return org_key in self.profile.org_admin_for

  def testForHost(self):
    request_data = TestIsUpdateLinkVisible.MockRequestData(is_host=True)
    result = project_details._isUpdateLinkVisible(request_data)
    self.assertTrue(request_data)

  def testForProjectStudent(self):
    student = self.profile_helper.createStudent()
    project = _createProjectForStudent(
        self.gsoc, self.org, self.dev_test, student=student)

    request_data = TestIsUpdateLinkVisible.MockRequestData(
        project=project, profile=student)
    self.assertTrue(project_details._isUpdateLinkVisible(request_data))

  def testForOtherStudent(self):
    student = self.profile_helper.createStudent()
    project = _createProjectForStudent(self.gsoc, self.org, self.dev_test)

    request_data = TestIsUpdateLinkVisible.MockRequestData(
        project=project, profile=student)
    self.assertFalse(project_details._isUpdateLinkVisible(request_data))

  def testForProjectMentor(self):
    mentor = self.profile_helper.createMentor(self.org)
    project = _createProjectForMentor(
        self.gsoc, self.org, self.dev_test, mentor=mentor)

    request_data = TestIsUpdateLinkVisible.MockRequestData(
        project=project, profile=mentor)
    self.assertFalse(project_details._isUpdateLinkVisible(request_data))

  def testForOtherMentor(self):
    mentor = self.profile_helper.createMentor(self.org)
    project = _createProjectForMentor(self.gsoc, self.org, self.dev_test)

    request_data = TestIsUpdateLinkVisible.MockRequestData(
        project=project, profile=mentor)
    self.assertFalse(project_details._isUpdateLinkVisible(request_data))

  def testForProjectOrgAdmin(self):
    org_admin = self.profile_helper.createOrgAdmin(self.org)
    project = _createProjectForMentor(self.gsoc, self.org, self.dev_test)

    request_data = TestIsUpdateLinkVisible.MockRequestData(
        project=project, profile=org_admin)
    self.assertTrue(project_details._isUpdateLinkVisible(request_data))

  def testForOtherOrgAdmin(self):
    program_helper = program_utils.GSoCProgramHelper()
    another_org = program_helper.createOrg()
    org_admin = self.profile_helper.createOrgAdmin(self.org)
    project = _createProjectForMentor(self.gsoc, another_org, self.dev_test)

    request_data = TestIsUpdateLinkVisible.MockRequestData(
        project=project, profile=org_admin)
    self.assertFalse(project_details._isUpdateLinkVisible(request_data))

  def testForLoneUser(self):
    self.profile_helper.createUser()
    project = _createProjectForMentor(self.gsoc, self.org, self.dev_test)

    request_data = TestIsUpdateLinkVisible.MockRequestData(
        project=project)
    self.assertFalse(project_details._isUpdateLinkVisible(request_data))
