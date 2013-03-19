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

"""Tests for project_detail views.
"""


from tests.profile_utils import GSoCProfileHelper
from tests.test_utils import GSoCDjangoTestCase

from soc.modules.gsoc.models.project import GSoCProject

class ProjectDetailsTest(GSoCDjangoTestCase):
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
        response, 'v2/modules/gsoc/project_details/base.html')

  def createProject(self):
    mentor_helper = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor_helper.createOtherUser('mentor@example.com')
    mentor = mentor_helper.createMentor(self.org)
    student_helper = GSoCProfileHelper(self.gsoc, self.dev_test)
    student_helper.createOtherUser('student@example.com')
    student_helper.createStudentWithProject(self.org, mentor)
    print GSoCProject.all().fetch(100)
    project = GSoCProject.all().get()
    project.is_featured = False
    project.status = 'accepted'
    project.put()
    return project

  def testProjectDetails(self):
    self.data.createStudent()
    self.timeline.studentsAnnounced()

    project = self.createProject()

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        project.parent().user.key().name(),
        project.key().id())

    # test project details GET
    url = '/gsoc/project/' + suffix
    response = self.get(url)
    self.assertProjectDetailsTemplateUsed(response)

  def testFeaturedProjectButton(self):
    self.timeline.studentsAnnounced()

    student = GSoCProfileHelper(self.gsoc, self.dev_test)
    student.createOtherUser('student@example.com')
    student.createStudent()

    self.data.createOrgAdmin(self.org)

    project = self.createProject()

    suffix = "%s/%s/%d" % (
        self.gsoc.key().name(),
        project.parent().user.key().name(),
        project.key().id())

    url = '/gsoc/project/featured/' + suffix
    postdata = {'value': 'unchecked'}
    response = self.post(url, postdata)

    self.assertResponseOK(response)

    project = GSoCProject.all().get()
    self.assertEqual(project.is_featured, True)


class ProjectDetailsUpdateTest(GSoCDjangoTestCase):
  """Unit tests project details update page."""

  def setUp(self):
    super(ProjectDetailsUpdateTest, self).setUp()
    self.init()

  def _createProjectForMentor(self, mentor=None):
    """Returns a newly created GSoCProject for the specified mentor.
    If a new mentor instance is not provided, a new profile is created.

    Args:
      mentor: the specified GSoCProfile mentor instance to mentor the project

    Returns:
      the newly created GSoCProject instance
    """
    if not mentor:
      mentor_helper = GSoCProfileHelper(self.gsoc, self.dev_test)
      mentor_helper.createOtherUser('mentor@example.com')
      mentor = mentor_helper.createMentor(self.org)

    student_helper = GSoCProfileHelper(self.gsoc, self.dev_test)
    student_helper.createOtherUser('student@example.com')
    student_helper.createStudentWithProject(self.org, mentor)
    project = GSoCProject.all().get()
    project.is_featured = False
    project.status = 'accepted'
    project.put()
    return project

  def _createProjectForStudent(self, student=None):
    """Returns a newly created GSoCProject for the specified student.
    If a new student instance is not provided, a new profile is created.

    Args:
      student: the specified GSoCProfile student instance to mentor the project

    Returns:
      the newly created GSoCProject instance
    """
    if not student:
      student_helper = GSoCProfileHelper(self.gsoc, self.dev_test)
      student_helper.createOtherUser('student@example.com')
      student = student_helper.createStudent()

    mentor_helper = GSoCProfileHelper(self.gsoc, self.dev_test)
    mentor_helper.createOtherUser('mentor@example.com')
    mentor_helper.createMentorWithProject(self.org, student)

    project = GSoCProject.all().get()
    project.is_featured = False
    project.status = 'accepted'
    project.put()
    return project

  def _getProjectUpdateUrl(self, project):
    return '/gsoc/project/update/%s/%s' % (
        project.parent_key().name(), project.key().id())

  def testLoneUserAccessForbidden(self):
    self.timeline.studentsAnnounced()
    project = self._createProjectForMentor()

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testMentorAccessForbidden(self):
    self.timeline.studentsAnnounced()

    mentor = self.data.createMentor(self.org)
    project = self._createProjectForMentor(mentor=mentor)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testOrgAdminAccessGranted(self):
    self.timeline.studentsAnnounced()

    self.data.createOrgAdmin(self.org)
    project = self._createProjectForMentor()

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertResponseOK(response)

  def testOrgAdminForAnotherOrgForbidden(self):
    self.timeline.studentsAnnounced()

    another_org = self.createOrg()
    self.data.createOrgAdmin(another_org)
    project = self._createProjectForMentor()

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)

  def testHostAccessGranted(self):
    self.timeline.studentsAnnounced()

    self.data.createHost()
    project = self._createProjectForMentor()

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertResponseOK(response)

  def testStudentAccessTheirProjectGranted(self):
    self.timeline.studentsAnnounced()

    student = self.data.createStudent()
    project = self._createProjectForStudent(student=student)

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertResponseOK(response)

  def testStudentAccessOtherProjectForbidden(self):
    self.timeline.studentsAnnounced()

    student = self.data.createStudent()
    project = self._createProjectForStudent()

    url = self._getProjectUpdateUrl(project)
    response = self.get(url)
    self.assertErrorTemplatesUsed(response)
    self.assertResponseForbidden(response)
