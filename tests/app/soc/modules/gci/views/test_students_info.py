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

"""Tests the view for GCI Dashboard."""

from google.appengine.ext import ndb

from soc.modules.gci.models.score import GCIScore

from tests import forms_to_submit_utils
from tests import profile_utils
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
    self.profile_helper.createStudent()
    response = self.get(self.url)
    self.assertResponseForbidden(response)

    self.profile_helper.createMentor(self.org)
    response = self.get(self.url)
    self.assertResponseForbidden(response)

    # check for an organization administrator
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user,
        admin_for=[ndb.Key.from_old_key(self.org.key())])

    response = self.get(self.url)
    self.assertResponseForbidden(response)

    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)
    response = self.get(self.url)
    self.assertResponseOK(response)

  def testStudentsInfoList(self):
    """Tests the studentsInfoList component of the dashboard."""
    forms_helper = forms_to_submit_utils.FormsToSubmitHelper()
    student_data_properties = {
        'consent_form': forms_helper.createBlobStoreForm()
        }
    student = profile_utils.seedNDBStudent(
        self.program, student_data_properties=student_data_properties)

    score_properties = {
        'points': 5,
        'program': self.program,
        'parent': student.key.to_old_key()
        }
    score = GCIScore(**score_properties)
    score.put()

    # set the current user to be the host.
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)
    response = self.get(self.url)
    self.assertStudentsInfoTemplatesUsed(response)

    idx = 1
    response = self.getListResponse(self.url, idx)
    self.assertIsJsonResponse(response)

    data = self.getListData(self.url, idx)
    self.assertEqual(len(data), 1)

    # Only the consent form has been submitted.
    self.assertEqual(data[0]['columns']['consent_form'], 'Yes')
    self.assertEqual(data[0]['columns']['enrollment_form'], 'No')

    # Case when both the forms have been submitted.
    student.student_data.enrollment_form = forms_helper.createBlobStoreForm()
    student.put()

    data = self.getListData(self.url, idx)
    self.assertEqual(len(data), 1)
    self.assertEqual(data[0]['columns']['consent_form'], 'Yes')
    self.assertEqual(data[0]['columns']['enrollment_form'], 'Yes')

    # Case when none of the two forms have been submitted.
    student.student_data.enrollment_form = None
    student.student_data.consent_form = None
    student.put()

    data = self.getListData(self.url, idx)
    self.assertEqual(len(data), 1)
    list_fields = data[0]['columns']
    self.assertEqual(list_fields['consent_form'], 'No')
    self.assertEqual(list_fields['enrollment_form'], 'No')
    self.assertEqual(list_fields['public_name'], student.public_name)
    self.assertEqual(list_fields['profile_id'], student.profile_id)
    self.assertEqual(list_fields['email'], student.contact.email)
