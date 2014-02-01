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

from tests import profile_utils
from tests import test_utils
from tests.utils import project_utils


class FormPageTest(test_utils.GSoCDjangoTestCase):
  """Test student form page."""

  def setUp(self):
    self.init()

  def testLoneUserAccessForbidden(self):
    self._assertAccessForbiddenForUrl(self._getEnrollmentFormUrl())
    self._assertAccessForbiddenForUrl(self._getTaxFormUrl())

  def testMentorAccessForbidden(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, mentor_for=[self.org.key])

    self._assertAccessForbiddenForUrl(self._getEnrollmentFormUrl())
    self._assertAccessForbiddenForUrl(self._getTaxFormUrl())

  def testOrgAdminAccessForbidden(self):
    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    profile_utils.seedNDBProfile(
        self.program.key(), user=user, admin_for=[self.org.key])

    self._assertAccessForbiddenForUrl(self._getEnrollmentFormUrl())
    self._assertAccessForbiddenForUrl(self._getTaxFormUrl())

  def testHostAccessForbidden(self):
    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    self._assertAccessForbiddenForUrl(self._getEnrollmentFormUrl())
    self._assertAccessForbiddenForUrl(self._getTaxFormUrl())

  def testStudentAccessForbidden(self):
    # access should be forbidden because at this point students are not
    # permitted to upload their forms
    self.timeline_helper.studentsAnnounced()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user=user)
    project_utils.seedProject(
        student, self.program.key(), org_key=self.org.key)

    self._assertAccessForbiddenForUrl(self._getEnrollmentFormUrl())
    self._assertAccessForbiddenForUrl(self._getTaxFormUrl())

  def testStudentAccessGranted(self):
    self.timeline_helper.formSubmission()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user=user)
    project_utils.seedProject(
        student, self.program.key(), org_key=self.org.key)

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

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user=user)
    project_utils.seedProject(
        student, self.program.key(), org_key=self.org.key)

    # check that there is no enrollment form at this stage
    self.assertIsNone(student.student_data.enrollment_form)

    with tempfile.NamedTemporaryFile() as test_file:
      # check for the enrollment form
      url = self._getEnrollmentFormUrl()
      postdata = {'enrollment_form': test_file}
      response = self.post(url, postdata)
      self.assertResponseRedirect(
          response, self._getEnrollmentFormUrl(validated=True))

      # check if the form has been submitted
      student = student.key.get()
      self.assertIsNotNone(student.student_data.enrollment_form)

  def testTaxFormSubmissionByStudent(self):
    """Tests that enrollment form is submitted properly by a student."""
    self.timeline_helper.formSubmission()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user=user)
    project_utils.seedProject(
        student, self.program.key(), org_key=self.org.key)

    # check that there is no tax form at this stage
    self.assertIsNone(student.student_data.tax_form)

    with tempfile.NamedTemporaryFile() as test_file:
      # check for the enrollment form
      url = self._getTaxFormUrl()
      postdata = {'tax_form': test_file}
      response = self.post(url, postdata)
      self.assertResponseRedirect(
          response, self._getTaxFormUrl(validated=True))

      # check if the form has been submitted
      student = student.key.get()
      self.assertIsNotNone(student.student_data.tax_form)

  def testEnrollmentFormSubmissionByAdmin(self):
    """Tests that enrollment form is submitted properly by an admin."""
    self.timeline_helper.formSubmission()

    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    student = profile_utils.seedSOCStudent(self.program)
    project_utils.seedProject(student, self.program.key(), org_key=self.org.key)

    # check that there is no enrollment form at this stage
    self.assertIsNone(student.student_data.enrollment_form)

    with tempfile.NamedTemporaryFile() as test_file:
      url = self._getAdminEnrollmentForm(student)
      postdata = {'enrollment_form': test_file}
      response = self.post(url, postdata)
      self.assertResponseRedirect(
          response, self._getAdminEnrollmentForm(student, validated=True))

      # check if the form has been submitted
      student = student.key.get()
      self.assertIsNotNone(student.student_data.enrollment_form)

  def testTaxFormSubmissionByAdmin(self):
    """Tests that tax form is submitted properly by an admin."""
    self.timeline_helper.formSubmission()

    user = profile_utils.seedNDBUser(host_for=[self.program])
    profile_utils.loginNDB(user)

    student = profile_utils.seedSOCStudent(self.program)
    project_utils.seedProject(student, self.program.key(), org_key=self.org.key)

    # check that there is no tax form at this stage
    self.assertIsNone(student.student_data.tax_form)

    with tempfile.NamedTemporaryFile() as test_file:
      url = self._getAdminTaxForm(student)
      postdata = {'tax_form': test_file}
      response = self.post(url, postdata)
      self.assertResponseRedirect(
          response, self._getAdminTaxForm(student, validated=True))

      # check if the form has been submitted
      student = student.key.get()
      self.assertIsNotNone(student.student_data.tax_form)

  def testSubmitAnotherForm(self):
    """Tests that another form may be resubmitted by a student."""
    self.timeline_helper.formSubmission()

    user = profile_utils.seedNDBUser()
    profile_utils.loginNDB(user)
    student = profile_utils.seedSOCStudent(self.program, user=user)
    project_utils.seedProject(
        student, self.program.key(), org_key=self.org.key)

    # set initial tax form
    blob_key = self.createBlob('initial_tax_form.pdf')
    student.student_data.tax_form = blob_key
    student.put()

    # submit a new tax form
    with tempfile.NamedTemporaryFile() as test_file:
      # check for the enrollment form
      url = self._getTaxFormUrl()
      postdata = {'tax_form': test_file}
      response = self.post(url, postdata)
      self.assertResponseRedirect(
          response, self._getTaxFormUrl(validated=True))

      # check if the form has been submitted
      student = student.key.get()
      self.assertIsNotNone(student.student_data.tax_form)
      self.assertEqual(os.path.basename(test_file.name),
          student.student_data.tax_form)

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
    url = '/gsoc/student_forms/admin/enrollment/%s' % profile.key.id()
    return url if not validated else url + '?validated'

  def _getAdminTaxForm(self, profile, validated=False):
    """Returns URL for the student tax form upload by admin."""
    url = '/gsoc/student_forms/admin/tax/%s' % profile.key.id()
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
    return profile_utils.seedNDBProfile(
        self.program.key(), mentor_for=[self.org.key])
