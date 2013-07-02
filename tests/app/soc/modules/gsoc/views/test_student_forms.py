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

"""Unit tests for student forms view."""

from tests import profile_utils
from tests import test_utils


class FormPageTest(test_utils.GSoCDjangoTestCase):
  """Test student form page."""

  def setUp(self):
    self.init()

  def testLoneUserAccessForbidden(self):
    self._assertAccessForbiddenForUrl(self._getEnrollmentFormUrl())
    self._assertAccessForbiddenForUrl(self._getTaxFormUrl())

  def testMentorAccessForbidden(self):
    self.profile_helper.createMentor(self.org)

    self._assertAccessForbiddenForUrl(self._getEnrollmentFormUrl())
    self._assertAccessForbiddenForUrl(self._getTaxFormUrl())

  def testOrgAdminAccessForbidden(self):
    self.profile_helper.createOrgAdmin(self.org)

    self._assertAccessForbiddenForUrl(self._getEnrollmentFormUrl())
    self._assertAccessForbiddenForUrl(self._getTaxFormUrl())

  def testHostAccessForbidden(self):
    self.profile_helper.createHost()

    self._assertAccessForbiddenForUrl(self._getEnrollmentFormUrl())
    self._assertAccessForbiddenForUrl(self._getTaxFormUrl())

  def testStudentAccessForbidden(self):
    # access should be forbidden because at this point students are not
    # permitted to upload their forms
    self.timeline_helper.studentsAnnounced()

    mentor = self._createNewMentor()
    self.profile_helper.createStudentWithProject(self.org, mentor)

    self._assertAccessForbiddenForUrl(self._getEnrollmentFormUrl())
    self._assertAccessForbiddenForUrl(self._getTaxFormUrl())

  def testStudentAccessGranted(self):
    self.timeline_helper.formSubmission()

    mentor = self._createNewMentor()
    self.profile_helper.createStudentWithProject(self.org, mentor)

    # check for enrollment form
    url = self._getEnrollmentFormUrl()
    response = self.get(url)
    self._assertStudentFormsTemplatesUsed(response)

    # check for tax form
    url = self._getTaxFormUrl()
    response = self.get(url)
    self._assertStudentFormsTemplatesUsed(response)

  def _getEnrollmentFormUrl(self):
    """Returns URL for the student enrollment form upload."""
    return '/gsoc/student_forms/enrollment/' + self.gsoc.key().name()

  def _getTaxFormUrl(self):
    """Returns URL for the student tax form upload."""
    return '/gsoc/student_forms/tax/' + self.gsoc.key().name()

  def _assertAccessForbiddenForUrl(self, url):
    """Asserts that GET request will return forbidden response
    for the specified URL."""
    response = self.get(url)
    self.assertResponseForbidden(response)
    self.assertErrorTemplatesUsed(response)

  def _assertStudentFormsTemplatesUsed(self, response):
    """Asserts that all the templates from the student forms were used.
    """
    self.assertGSoCTemplatesUsed(response)
    self.assertTemplateUsed(response,
        'modules/gsoc/student_forms/base.html')
    self.assertTemplateUsed(response, 'modules/gsoc/_form.html')

  def _createNewMentor(self):
    """Returns a newly created mentor."""
    profile_helper = profile_utils.GSoCProfileHelper(self.gsoc, self.dev_test)
    profile_helper.createOtherUser('mentor@example.com')
    return profile_helper.createMentor(self.org)
