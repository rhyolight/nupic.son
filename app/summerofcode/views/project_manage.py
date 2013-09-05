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

"""Views to manage Summer Of Code projects."""

from google.appengine.ext import db
from google.appengine.ext import ndb

from django import forms
from django.utils import translation

from melange.request import access
from melange.request import exception

from soc.modules.gsoc.models import project_survey as project_survey_model
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper import url_patterns

from summerofcode.logic import project_survey as project_survey_logic
from summerofcode.logic import survey as survey_logic
from summerofcode.views.helper import urls


MANAGE_PROJECT_ADMIN_PAGE_NAME = translation.ugettext(
    'Manage project as Program Administrator')

PERSONAL_EXTENSION_FORM_START_DATE_LABEL = translation.ugettext('Start date')
PERSONAL_EXTENSION_FORM_END_DATE_LABEL = translation.ugettext('End date')

PERSONAL_EXTENSION_FORM_BUTTON_VALUE = translation.ugettext('Set Extension')

MIDTERM_EXTENSION_FORM_NAME = 'midterm_extension_form'
FINAL_EXTENSION_FORM_NAME = 'final_extension_form'
_FORM_NAMES = [MIDTERM_EXTENSION_FORM_NAME, FINAL_EXTENSION_FORM_NAME]


def _getPersonalExtensionFormName(survey_type):
  """Returns name to be used by personal extension form for the specified
  survey type.

  Args:
    survey_type: type of the survey. May be one of MIDTERM_EVAL or FINAL_EVAL.

  Returns:
    a string containing name for the form.

  Raises:
    ValueError: if survey type is not recognized.
  """
  if survey_type == project_survey_model.MIDTERM_EVAL:
    return MIDTERM_EXTENSION_FORM_NAME
  elif survey_type == project_survey_model.FINAL_EVAL:
    return FINAL_EXTENSION_FORM_NAME
  else:
    raise ValueError('Wrong survey type: %s' % survey_type)


def _getSurveyType(post_data):
  """Returns survey type for the form name of personal extension that is
  submitted in POST data.

  Args:
    post_data: dict containing POST data.

  Returns:
    type of the survey. May be one of MIDTERM_EVAL or FINAL_EVAL.

  Raises:
    exception.BadRequest: if form name is not recoginized.
  """
  if MIDTERM_EXTENSION_FORM_NAME in post_data:
    return project_survey_model.MIDTERM_EVAL
  elif FINAL_EXTENSION_FORM_NAME in post_data:
    return project_survey_model.FINAL_EVAL
  else:
    raise exception.BadRequest(message='Form type not supported.')


def _getInitialValues(extension):
  """Returns initial values that should be populated to personal
  extension form based on the specified extension entity.

  Args:
    extension: personal extension entity.

  Returns:
    a dict mapping form fields with their initial values. If extension is
    not set, an empty dict is returned.
  """
  return {
      'start_date': extension.start_date,
      'end_date': extension.end_date
      } if extension else {}


def _setPersonalExtension(profile_key, survey_key, form):
  """Sets personal extension evaluation for the specified profile and
  the specified survey based on the data sent in the specified form.
  The extension is not set if 

  Args:
    profile_key: profile key.
    survey_key: survey key.
    form: forms.Form instance that contains data sent by the user.

  Returns:
    True, if an extension has been successfully set; False otherwise.
  """

  @ndb.transactional
  def setPersonalExtensionTxn():
    """Transaction to set personal extension."""
    start_date = form.cleaned_data['start_date']
    end_date = form.cleaned_data['end_date']
    survey_logic.createOrUpdatePersonalExtension(
        profile_key, survey_key, start_date=start_date, end_date=end_date)

  if form.is_valid():
    setPersonalExtensionTxn()
    return True
  else:
    return False


class PersonalExtensionForm(forms.Form):
  """Form type used to set personal extensions."""

  start_date = forms.DateTimeField(required=False,
      label=PERSONAL_EXTENSION_FORM_START_DATE_LABEL)
  end_date = forms.DateTimeField(required=False,
      label=PERSONAL_EXTENSION_FORM_END_DATE_LABEL)

  def __init__(self, name=None, title=None, **kwargs):
    """Initializes the form with the specified values.

    Args:
      name: name of the form that is used as an identifier.
      title: title of the form.
    """
    super(PersonalExtensionForm, self).__init__(**kwargs)
    self.name = name
    self.title = title
    self.button_value = PERSONAL_EXTENSION_FORM_BUTTON_VALUE


class ManageProjectProgramAdminView(base.GSoCRequestHandler):
  """View for Program Administrators to manage projects."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def templatePath(self):
    """See base.templatePath for specification."""
    return 'project_manage/admin_manage.html'

  def djangoURLPatterns(self):
    """See base.djangoURLPatterns for specification."""
    return [
        url_patterns.url(r'project/manage/admin/%s$' % url_patterns.PROJECT,
            self, name=urls.UrlNames.PROJECT_MANAGE_ADMIN)
    ]

  def context(self, data, check, mutator):
    """See base.context for specification."""
    mutator.projectFromKwargs()

    evaluations = project_survey_logic.getStudentEvaluations(
        data.program.key())

    extension_forms = []
    for evaluation in evaluations:
      # try getting existing extension for this evaluation
      extension = survey_logic.getPersonalExtension(
          data.project.parent_key(), evaluation.key())
      initial = _getInitialValues(extension)

      name = _getPersonalExtensionFormName(evaluation.survey_type)
      extension_forms.append(PersonalExtensionForm(data=data.POST or None,
          name=name, title=evaluation.title, initial=initial))

    context = {
        'page_name': MANAGE_PROJECT_ADMIN_PAGE_NAME,
        'extension_forms': extension_forms,
        }

    return context

  def post(self, data, check, mutator):
    """See base.post for specification."""
    mutator.projectFromKwargs()

    profile_key = data.project.parent_key()

    # get type of survey based on submitted form name
    survey_type = _getSurveyType(data.POST)
    survey_key = project_survey_logic.constructEvaluationKey(
        data.program.key(), survey_type)

    # check if the survey exists
    if not db.get(survey_key):
      raise exception.BadRequest(message='Survey of type %s not found.' %
          survey_type)

    # try setting a personal extension
    form = PersonalExtensionForm(data=data.POST)
    result = _setPersonalExtension(profile_key, survey_key, form)

    if result:
      # redirect to somewhere
      data.redirect.project()
      return data.redirect.to(
          urls.UrlNames.PROJECT_MANAGE_ADMIN, validated=True)
    else:
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)
