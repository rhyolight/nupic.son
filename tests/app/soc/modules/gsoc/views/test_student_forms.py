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

import os
import tempfile

from soc.modules.gsoc.models import profile as profile_model

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
    self.assertResponseOK(response)
    self._assertStudentFormsTemplatesUsed(response)

    # check for tax form
    url = self._getTaxFormUrl()
    response = self.get(url)
    self.assertResponseOK(response)
    self._assertStudentFormsTemplatesUsed(response)

  def testEnrollmentFormSubmissionByStudent(self):
    """Tests that enrollment form is submitted properly by a student."""
    self.timeline_helper.formSubmission()

    mentor = self._createNewMentor()
    self.profile_helper.createStudentWithProject(self.org, mentor)

    # check that there is no enrollment form at this stage
    self.assertIsNone(self.profile_helper.profile.student_info.enrollment_form)

    with tempfile.NamedTemporaryFile() as test_file:
      # check for the enrollment form
      url = self._getEnrollmentFormUrl()
      postdata = {'enrollment_form': test_file}
      response = self.post(url, postdata)
      self.assertResponseRedirect(
          response, self._getEnrollmentFormUrl(validated=True))

      # check if the form has been submitted
      student_info = profile_model.GSoCStudentInfo.get(
          self.profile_helper.profile.student_info.key())
      self.assertIsNotNone(student_info.enrollment_form)

  def testTaxFormSubmissionByStudent(self):
    """Tests that enrollment form is submitted properly by a student."""
    self.timeline_helper.formSubmission()

    mentor = self._createNewMentor()
    self.profile_helper.createStudentWithProject(self.org, mentor)

    # check that there is no tax form at this stage
    self.assertIsNone(self.profile_helper.profile.student_info.tax_form)

    with tempfile.NamedTemporaryFile() as test_file:
      # check for the enrollment form
      url = self._getTaxFormUrl()
      postdata = {'tax_form': test_file}
      response = self.post(url, postdata)
      self.assertResponseRedirect(
          response, self._getTaxFormUrl(validated=True))

      # check if the form has been submitted
      student_info = profile_model.GSoCStudentInfo.get(
          self.profile_helper.profile.student_info.key())
      self.assertIsNotNone(student_info.tax_form)

  def testEnrollmentFormSubmissionByAdmin(self):
    """Tests that enrollment form is submitted properly by an admin."""
    self.timeline_helper.formSubmission()

    self.profile_helper.createHost()

    mentor = self._createNewMentor()

    profile_helper = profile_utils.GSoCProfileHelper(self.gsoc, self.dev_test)
    profile_helper.createOtherUser('student@example.com')
    profile = profile_helper.createStudentWithProject(self.org, mentor)    

    # check that there is no enrollment form at this stage
    self.assertIsNone(profile.student_info.enrollment_form)

    with tempfile.NamedTemporaryFile() as test_file:
      url = self._getAdminEnrollmentForm(profile)
      postdata = {'enrollment_form': test_file}
      response = self.post(url, postdata)
      self.assertResponseRedirect(
          response, self._getAdminEnrollmentForm(profile, validated=True))

      # check if the form has been submitted
      student_info = profile_model.GSoCStudentInfo.get(
          profile.student_info.key())
      self.assertIsNotNone(student_info.enrollment_form)

  def testTaxFormSubmissionByAdmin(self):
    """Tests that tax form is submitted properly by an admin."""
    self.timeline_helper.formSubmission()

    self.profile_helper.createHost()

    mentor = self._createNewMentor()

    profile_helper = profile_utils.GSoCProfileHelper(self.gsoc, self.dev_test)
    profile_helper.createOtherUser('student@example.com')
    profile = profile_helper.createStudentWithProject(self.org, mentor)    

    # check that there is no tax form at this stage
    self.assertIsNone(profile.student_info.tax_form)

    with tempfile.NamedTemporaryFile() as test_file:
      url = self._getAdminTaxForm(profile)
      postdata = {'tax_form': test_file}
      response = self.post(url, postdata)
      self.assertResponseRedirect(
          response, self._getAdminTaxForm(profile, validated=True))

      # check if the form has been submitted
      student_info = profile_model.GSoCStudentInfo.get(
          profile.student_info.key())
      self.assertIsNotNone(student_info.tax_form)

  def testSubmitAnotherForm(self):
    """Tests that another form may be resubmitted by a student."""
    self.timeline_helper.formSubmission()

    mentor = self._createNewMentor()
    self.profile_helper.createStudentWithProject(self.org, mentor)

    # set initial tax form
    blob_key = self.createBlob('initial_tax_form.pdf')
    self.profile_helper.profile.student_info.tax_form = blob_key
    self.profile_helper.profile.student_info.put()

    # submit a new tax form
    with tempfile.NamedTemporaryFile() as test_file:
      # check for the enrollment form
      url = self._getTaxFormUrl()
      postdata = {'tax_form': test_file}
      response = self.post(url, postdata)
      self.assertResponseRedirect(
          response, self._getTaxFormUrl(validated=True))

      # check if the form has been submitted
      student_info = profile_model.GSoCStudentInfo.get(
          self.profile_helper.profile.student_info.key())
      self.assertIsNotNone(student_info.tax_form)
      self.assertEqual(os.path.basename(test_file.name),
          student_info.tax_form.key())

  def _getEnrollmentFormUrl(self, validated=False):
    """Returns URL for the student enrollment form upload."""
    url = '/gsoc/student_forms/enrollment/' + self.gsoc.key().name()
    return url if not validated else url + '?validated'

  def _getTaxFormUrl(self, validated=False):
    """Returns URL for the student tax form upload."""
    url = '/gsoc/student_forms/tax/' + self.gsoc.key().name()
    return url if not validated else url + '?validated'

  def _getAdminEnrollmentForm(self, profile, validated=False):
    """Returns URL for the student enrollment form upload by admin."""
    url = '/gsoc/student_forms/admin/enrollment/%s' % profile.key().name()
    return url if not validated else url + '?validated'

  def _getAdminTaxForm(self, profile, validated=False):
    """Returns URL for the student tax form upload by admin."""
    url = '/gsoc/student_forms/admin/tax/%s' % profile.key().name()
    return url if not validated else url + '?validated'

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
