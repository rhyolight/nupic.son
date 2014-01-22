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

"""Tests for the view with a list of projects."""

from tests import profile_utils
from tests import test_utils
from tests.utils import project_utils


class ProjectListTest(test_utils.GSoCDjangoTestCase):
  """Tests project list page."""

  def setUp(self):
    self.init()

  def assertProjectTemplatesUsed(self, response):
    """Asserts that all the templates from the dashboard were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gsoc/projects_list/base.html')
    self.assertTemplateUsed(
        response, 'modules/gsoc/projects_list/_project_list.html')

  def testListProjects(self):
    self.timeline_helper.studentsAnnounced()
    url = '/gsoc/projects/list/' + self.gsoc.key().name()
    response = self.get(url)
    self.assertResponseOK(response)
    self.assertProjectTemplatesUsed(response)

    response = self.getListResponse(url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(0, len(data))

    student = profile_utils.seedSOCStudent(self.program)
    project_utils.seedProject(student, self.program.key(), org_key=self.org.key)

    response = self.getListResponse(url, 0)
    self.assertIsJsonResponse(response)
    data = response.context['data']['']
    self.assertEqual(1, len(data))
    columns = response.context['data'][''][0]['columns']
    self.assertIn('key', columns)
    self.assertIn('title', columns)
    self.assertIn('mentors', columns)
    self.assertIn('student', columns)
    self.assertIn('org', columns)
