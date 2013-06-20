# Copyright 2012 the Melange authors.
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


"""Tests the view for GCI student form uploads.
"""

from tests.profile_utils import GCIProfileHelper
from tests.test_utils import GCIDjangoTestCase


class StudentFormUploadTest(GCIDjangoTestCase):
  """Tests the Student form upload page.
  """

  def setUp(self):
    self.init()
    self.url = '/gci/student/forms/' + self.gci.key().name()

  def assertStudentFormUploadTemplatesUsed(self, response):
    """Asserts that all the templates from student form upload page are used.
    """
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/student_forms/base.html')

  def testStudentFormUpload(self):
    """Tests the studentsInfoList component of the dashboard.
    """
    profile_helper = GCIProfileHelper(self.gci, self.dev_test)
    student = profile_helper.createStudent()

    response = self.get(self.url)
    self.assertStudentFormUploadTemplatesUsed(response)
    self.assertResponseOK(response)

    self.assertContains(
        response, 'To download the sample form or one of its translations')
