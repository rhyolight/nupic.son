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

"""Module for the GCI age check."""

from django import forms

from soc.logic import exceptions
from soc.logic import validate
from soc.views.helper import url_patterns

from soc.modules.gci.views import base as gci_base
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.helper import url_patterns as gci_url_patterns


class AgeCheckForm(gci_forms.GCIModelForm):
  """Django form for the Age verification page."""

  class Meta:
    model = None
    css_prefix = 'gci_age_check'
    fields = ['birth_date']

  birth_date = forms.DateField(
      label='Date of birth (YYYY-MM-DD)', required=True)


class AgeCheck(gci_base.GCIRequestHandler):
  """View for the GCI age check."""

  def djangoURLPatterns(self):
    """The URL pattern for the view."""
    return [gci_url_patterns.url(r'age_check/%s$' % url_patterns.PROGRAM,
                                 self, name='gci_age_check')]

  def checkAccess(self):
    """Ensures that student sign up is active and the user is logged out."""
    self.check.studentSignupActive()
    self.check.isLoggedOut()

  def templatePath(self):
    """Returns the path to the template."""
    return 'v2/modules/gci/age_check/base.html'

  def context(self, data, check, mutator):
    """Handler for default HTTP GET request."""
    context = {
        'page_name': 'Age Verification for %s' % data.program.name,
        'program': data.program,
        'failed_check': False
        }

    age_check_result = data.request.COOKIES.get('age_check', None)

    if age_check_result == '0':
      context['failed_check'] = True
    elif age_check_result:
      # age check passed, redirect to create profile page
      # TODO(nathaniel): Can this be cleaned up at all? Creating and
      # discarding a response feels weird.
      response = data.redirect.createProfile('student').to(
          'create_gci_profile', secure=True)
      raise exceptions.RedirectRequest(response['Location'])

    if data.POST:
      context['form'] = AgeCheckForm(data.POST)
    else:
      context['form'] = AgeCheckForm()

    return context

  def post(self, data, check, mutator):
    """Handles POST requests."""
    form = AgeCheckForm(data.POST)

    if not form.is_valid():
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)

    program = data.program
    birth_date = form.cleaned_data['birth_date']

    # redirect to the same page and have the cookies sent across
    # TODO(nathaniel): make this .program() call unnecessary.
    data.redirect.program()

    response = data.redirect.to('gci_age_check')

    age_sufficient = validate.isAgeSufficientForProgram(birth_date, program)
    response.set_cookie('age_check', birth_date if age_sufficient else '0')

    return response
