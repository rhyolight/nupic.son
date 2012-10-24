#!/usr/bin/env python2.5
#
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
