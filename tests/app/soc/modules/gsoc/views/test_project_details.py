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

from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.views import project_details
from soc.modules.gsoc.views.helper import request_data

from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import org_utils
from tests import profile_utils
from tests import test_utils
from tests.utils import project_utils


def _createProjectForStudent(program, org, dev_test, student=None):
  """Returns a newly created GSoCProject for the specified student.
  If a new student instance is not provided, a new profile is created.

  Args:
    program: GSoCProgram instance for which the project is to be created
    org: Organization entity.
    dev_test: whether it is dev test environment
    student: the specified GSoCProfile student instance to mentor the project

  Returns:
    the newly created GSoCProject instance
  """
  if not student:
    student = profile_utils.seedSOCStudent(program)

  return project_utils.seedProject(student, program.key(), org_key=org.key)


def _createProjectForMentor(program, org, dev_test, mentor=None):
  """Returns a newly created GSoCProject for the specified mentor.
  If a new mentor instance is not provided, a new profile is created.

  Args:
    program: GSoCProgram instance for which the project is to be created
    org: Organization entity.
    dev_test: whether it is dev test environment
    mentor: the specified GSoCProfile mentor instance to mentor the project

  Returns:
    the newly created GSoCProject instance
  """
  if not mentor:
    mentor = profile_utils.seedNDBProfile(
        program.key(), mentor_for=[org.key])

  student = profile_utils.seedSOCStudent(program)

  return project_utils.seedProject(
      student, program.key(), org_key=org.key, mentor_key=mentor.key)


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
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
    student = profile_utils.seedSOCStudent(self.program)

    return project_utils.seedProject(
        student, self.program.key(), org_key=self.org.key,
        mentor_key=mentor.key)

  def testProjectDetails(self):
    self.timeline_helper.studentsAnnounced()

    project = self.createProject()

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        project.parent_key().parent().name(),
        project.key().id())

    # test project details GET
    url = '/gsoc/project/' + suffix
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertProjectDetailsTemplateUsed(response)

  def testFeaturedProjectButton(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    self.timeline_helper.studentsAnnounced()

    project = self.createProject()

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        project.parent_key().parent().name(),
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

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    project = _createProjectForMentor(
        self.gsoc, self.org, self.dev_test, mentor=mentor)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testOrgAdminAccessGranted(self):
    self.timeline_helper.studentsAnnounced()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    project = _createProjectForMentor(self.gsoc, self.org, self.dev_test)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertResponseOK(response)

  def testOrgAdminForAnotherOrgForbidden(self):
    self.timeline_helper.studentsAnnounced()

    other_org = org_utils.seedSOCOrganization(self.program.key())

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[other_org.key])

    project = _createProjectForMentor(self.gsoc, self.org, self.dev_test)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testHostAccessGranted(self):
    self.timeline_helper.studentsAnnounced()

    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    project = _createProjectForMentor(self.gsoc, self.org, self.dev_test)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertResponseOK(response)

  def testStudentAccessTheirProjectGranted(self):
    self.timeline_helper.studentsAnnounced()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user=user)

    project = _createProjectForStudent(
        self.gsoc, self.org, self.dev_test, student=student)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertResponseOK(response)

  def testStudentAccessOtherProjectForbidden(self):
    self.timeline_helper.studentsAnnounced()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedSOCStudent(self.program, user=user)

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

  def testForHost(self):
    data = request_data.RequestData(None, None, None)
    data._program = self.program
    data._ndb_user = profile_utils.seedNDBUser(host_for=[self.program])
    result = project_details._isUpdateLinkVisible(data)
    self.assertTrue(result)

  def testForProjectStudent(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user=user)

    project = _createProjectForStudent(
        self.gsoc, self.org, self.dev_test, student=student)

    sponsor_id, program_id, user_id = project.parent_key().name().split('/')
    kwargs = {
        'sponsor': sponsor_id,
        'program': program_id,
        'user': user_id,
        'id': project.key().id(),
        }
    data = request_data.RequestData(None, None, kwargs)

    self.assertTrue(project_details._isUpdateLinkVisible(data))

  def testForOtherStudent(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedSOCStudent(self.program, user=user)

    project = _createProjectForStudent(self.gsoc, self.org, self.dev_test)

    sponsor_id, program_id, user_id = project.parent_key().name().split('/')
    kwargs = {
        'sponsor': sponsor_id,
        'program': program_id,
        'user': user_id,
        'id': project.key().id(),
        }
    data = request_data.RequestData(None, None, kwargs)

    self.assertFalse(project_details._isUpdateLinkVisible(data))

  def testForProjectMentor(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    mentor = profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    project = _createProjectForMentor(
        self.gsoc, self.org, self.dev_test, mentor=mentor)

    sponsor_id, program_id, user_id = project.parent_key().name().split('/')
    kwargs = {
        'sponsor': sponsor_id,
        'program': program_id,
        'user': user_id,
        'id': project.key().id(),
        }
    data = request_data.RequestData(None, None, kwargs)

    self.assertFalse(project_details._isUpdateLinkVisible(data))

  def testForOtherMentor(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    project = _createProjectForMentor(self.gsoc, self.org, self.dev_test)

    sponsor_id, program_id, user_id = project.parent_key().name().split('/')
    kwargs = {
        'sponsor': sponsor_id,
        'program': program_id,
        'user': user_id,
        'id': project.key().id(),
        }
    data = request_data.RequestData(None, None, kwargs)

    self.assertFalse(project_details._isUpdateLinkVisible(data))

  def testForProjectOrgAdmin(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    project = _createProjectForMentor(self.program, self.org, self.dev_test)

    sponsor_id, program_id, user_id = project.parent_key().name().split('/')
    kwargs = {
        'sponsor': sponsor_id,
        'program': program_id,
        'user': user_id,
        'id': project.key().id(),
        }
    data = request_data.RequestData(None, None, kwargs)

    self.assertTrue(project_details._isUpdateLinkVisible(data))

  def testForOtherOrgAdmin(self):
    other_org = org_utils.seedSOCOrganization(self.program.key())

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    project = _createProjectForMentor(self.gsoc, other_org, self.dev_test)

    sponsor_id, program_id, user_id = project.parent_key().name().split('/')
    kwargs = {
        'sponsor': sponsor_id,
        'program': program_id,
        'user': user_id,
        'id': project.key().id(),
        }
    data = request_data.RequestData(None, None, kwargs)

    self.assertFalse(project_details._isUpdateLinkVisible(data))

  def testForLoneUser(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)

    project = _createProjectForMentor(self.gsoc, self.org, self.dev_test)

    kwargs = {
        'sponsor': self.sponsor.link_id,
        'program': self.program.program_id,
        'user': user.user_id,
        'id': project.key().id(),
        }
    data = request_data.RequestData(None, None, kwargs)

    self.assertFalse(project_details._isUpdateLinkVisible(data))
