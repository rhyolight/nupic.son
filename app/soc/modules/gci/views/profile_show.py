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

"""Module for displaying the GCI profile read-only page."""

import logging

from django import http
from django.utils import translation

from melange.request import access
from melange.request import exception
from soc.views import profile_show
from soc.views.helper import access_checker
from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.views import base
from soc.modules.gci.views import readonly_template
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url

NON_STUDENT_ERR_MSG = translation.ugettext(
    'There cannot be a post request for student form verification on '
    'non-student profiles.')


class StudentFormsTemplate(Template):
  """Template to provide links to student forms."""

  def __init__(self, profile, data):
    super(StudentFormsTemplate, self).__init__(data)
    self.profile = profile

  def context(self):
    base_url = self.data.redirect.profile(self.profile.link_id).urlOf(
        url_names.GCI_STUDENT_FORM_DOWNLOAD)
    consent_form_url = '%s?%s' % (base_url, url_names.CONSENT_FORM_GET_PARAM)
    student_id_form_url = '%s?%s' % (
        base_url, url_names.ENROLLMENT_FORM_GET_PARAM)

    student_info = self.profile.student_info
    return {
        'consent_form': student_info.consent_form,
        'consent_form_verified': student_info.consent_form_verified,
        'consent_form_url': consent_form_url,
        'student_id_form': student_info.student_id_form,
        'student_id_form_verified': student_info.student_id_form_verified,
        'student_id_form_url': student_id_form_url,
        }

  def templatePath(self):
    return 'modules/gci/profile_show/_student_forms.html'


class GCIProfileReadOnlyTemplate(readonly_template.GCIModelReadOnlyTemplate):
  """Template to construct read-only GCIProfile data."""

  class Meta:
    model = GCIProfile
    css_prefix = 'gci_profile_show'
    fields = ['public_name', 'given_name', 'surname', 'im_network',
              'im_handle', 'home_page', 'blog', 'photo_url', 'email',
              'res_street', 'res_street_extra', 'res_city', 'res_state',
              'res_country', 'res_postalcode', 'phone', 'ship_name',
              'ship_street', 'ship_street_extra', 'ship_city', 'ship_state',
              'ship_country', 'ship_postalcode', 'birth_date',
              'tshirt_style', 'tshirt_size', 'gender', 'program_knowledge']


class GCIUserReadOnlyTemplate(profile_show.UserReadOnlyTemplate):
  """Template to construct read-only User data to be displayed on Summer
  Of Code view.
  """
  template_path = readonly_template.GCIModelReadOnlyTemplate.template_path


class GCIProfileShowPage(profile_show.ProfileShowPage, base.GCIRequestHandler):
  """View to display the read-only profile page."""

  def djangoURLPatterns(self):
    """See base.GCIRequestHandler.djangoURLPatterns for specification."""
    return [
        url(r'profile/show/%s$' % url_patterns.PROGRAM,
         self, name=url_names.GCI_PROFILE_SHOW),
    ]

  def context(self, data, check, mutator):
    """See base.GCIRequestHandler.context for specification."""
    context = super(GCIProfileShowPage, self).context(data, check, mutator)

    profile = self._getProfile(data)
    if profile.student_info:
      context['student_forms_template'] = StudentFormsTemplate(profile, data)

    return context

  def templatePath(self):
    """See base.GCIRequestHandler.templatePath for specification."""
    return 'modules/gci/profile_show/base.html'

  def _getProfileReadOnlyTemplate(self, profile):
    """See profile_show.ProfileShowPage._getProfileReadOnlyTemplate
    for specification.
    """
    return GCIProfileReadOnlyTemplate(profile)

  def _getUserReadOnlyTemplate(self, user):
    """See profile_show.ProfileShowPage._getUserReadOnlyTemplate
    for specification.
    """
    return GCIUserReadOnlyTemplate(user)


class GCIProfileShowAdminPage(GCIProfileShowPage):
  """View to display the read-only profile page for admin."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url(r'profile/show/%s$' % url_patterns.PROFILE,
         self, name=url_names.GCI_PROFILE_SHOW_ADMIN),
    ]

  def context(self, data, check, mutator):
    context = super(GCIProfileShowAdminPage, self).context(data, check, mutator)
    assert access_checker.isSet(data.url_profile.student_info)

    profile = data.url_profile
    student_info = profile.student_info
    if student_info:
      if student_info.consent_form_verified:
        context['verify_consent_form_init'] = 'unchecked'
      else:
        context['verify_consent_form_init'] = 'checked'

      if student_info.student_id_form_verified:
        context['verify_student_id_form_init'] = 'unchecked'
      else:
        context['verify_student_id_form_init'] = 'checked'

      # TODO(nathaniel): Eliminate this state-setting call.
      data.redirect.profile(profile.link_id)
      context['student_task_link'] = data.redirect.urlOf(
          url_names.GCI_STUDENT_TASKS)

      context['user'] = self._getUserReadOnlyTemplate(data.url_user)

    return context

  def post(self, data, check, mutator):
    """Handles student form verification by host."""
    if not data.url_profile.student_info:
      # TODO(nathaniel): Is this user error? If so, should it be
      # logged at server warning level, or even at all?
      logging.warn(NON_STUDENT_ERR_MSG)
      raise exception.MethodNotAllowed()

    post_data = data.POST
    button_id = post_data.get('id')
    value = post_data.get('value')

    if button_id == 'verify-consent-form':
      self._verifyConsentForm(data, value)
    elif button_id == 'verify-student-id-form':
      self._verifyStudentIDForm(data, value)

    return http.HttpResponse()

  def _verifyConsentForm(self, data, value):
    """Mark the parental consent form as verified or not verified.

    Args:
      data: A RequestData describing the current request.
      value: The value of the checkbox field - checked or unchecked
    """
    student_info = data.url_profile.student_info
    student_info.consent_form_verified = value == 'checked'
    student_info.put()

  def _verifyStudentIDForm(self, data, value):
    """Mark the student id form as verified or not verified.

    Args:
      data: A RequestData describing the current request.
      value: The value of the checkbox field - checked or unchecked
    """
    student_info = data.url_profile.student_info
    student_info.student_id_form_verified = value == 'checked'
    student_info.put()

  def _getProfile(self, data):
    """See soc.views.profile_show.ProfileShowPage for the documentation."""
    assert access_checker.isSet(data.url_profile)
    return data.url_profile
