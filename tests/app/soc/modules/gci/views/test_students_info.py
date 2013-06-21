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


"""Tests the view for GCI Dashboard.
"""

from google.appengine.ext import blobstore

from soc.modules.gci.models.score import GCIScore

from tests.profile_utils import GCIProfileHelper
from tests.test_utils import GCIDjangoTestCase


class StudentsInfoTest(GCIDjangoTestCase):
  """Tests the Students info page.
  """

  def setUp(self):
    self.init()
    self.url = '/gci/admin/students_info/' + self.gci.key().name()

  def assertStudentsInfoTemplatesUsed(self, response):
    """Asserts that all the templates from the dashboard were used.
    """
    self.assertGCITemplatesUsed(response)
    self.assertTemplateUsed(response, 'modules/gci/students_info/base.html')

  def testAccessToTheList(self):
    """Tests only the host can access the list.
    """
    self.data.createStudent()
    response = self.get(self.url)
    self.assertResponseForbidden(response)

    self.data.createMentor(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)

    self.data.createOrgAdmin(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)

    self.data.createHost()
    response = self.get(self.url)
    self.assertResponseOK(response)

  def testStudentsInfoList(self):
    """Tests the studentsInfoList component of the dashboard.
    """
    profile_helper = GCIProfileHelper(self.gci, self.dev_test)
    profile_helper.createOtherUser('pr@gmail.com')

    idx = 1

    student = profile_helper.createStudentWithConsentForms(consent_form=True)
    score_properties = {'points': 5, 'program': self.gci, 'parent': student}
    score = GCIScore(**score_properties)
    score.put()

    #Set the current user to be the host.
    self.data.createHost()
    response = self.get(self.url)
    self.assertStudentsInfoTemplatesUsed(response)

    response = self.getListResponse(self.url, idx)
    self.assertIsJsonResponse(response)

    data = self.getListData(self.url, idx)
    self.assertEqual(len(data), 1)

    #Only the consent form has been submitted.
    self.assertEqual(data[0]['columns']['consent_form'], 'Yes')
    self.assertEqual(data[0]['columns']['student_id_form'], 'No')

    #Case when both the forms have been submitted.
    student = profile_helper.createStudentWithConsentForms(
        consent_form=True, student_id_form=True)
    score_properties = {'points': 5, 'program': self.gci, 'parent': student}
    score = GCIScore(**score_properties)

    data = self.getListData(self.url, idx)
    self.assertEqual(len(data), 1)
    self.assertEqual(data[0]['columns']['consent_form'], 'Yes')
    self.assertEqual(data[0]['columns']['student_id_form'], 'Yes')

    #Case when none of the two forms have been submitted.
    student = profile_helper.createStudentWithConsentForms()
    score_properties = {'points': 5, 'program': self.gci, 'parent': student}
    score = GCIScore(**score_properties)

    data = self.getListData(self.url, idx)
    self.assertEqual(len(data), 1)
    list_fields = data[0]['columns']
    self.assertEqual(list_fields['consent_form'], 'No')
    self.assertEqual(list_fields['student_id_form'], 'No')
    self.assertEqual(list_fields['name'], student.name())
    self.assertEqual(list_fields['link_id'], student.link_id)
    self.assertEqual(list_fields['email'], student.email)
