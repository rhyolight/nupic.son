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

"""Module containing the views for Summer Of Code organization application."""

import collections

from google.appengine.ext import ndb

from django import forms as django_forms
from django import http
from django.utils import translation

from melange.logic import organization as org_logic
from melange.request import access
from melange.request import exception
from melange.request import links

from soc.logic import cleaning

from soc.views import readonly_template
from soc.views.helper import url_patterns
from soc.views.helper import surveys

from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.helper import url_patterns as soc_url_patterns

from summerofcode.views.helper import urls


ORG_ID_HELP_TEXT = translation.ugettext(
    'Organization ID is used as part of various URL links throughout '
    ' the site. You may reuse the same id for different years of the program. '
    '<a href="http://en.wikipedia.org/wiki/ASCII">ASCII</a> alphanumeric '
    'characters, digits, and underscores only.')

ORG_NAME_HELP_TEXT = translation.ugettext(
    'Complete, formal name of the organization.')

ORG_ID_LABEL = translation.ugettext('Organization ID')

ORG_NAME_LABEL = translation.ugettext('Organization name')

ORG_APP_TAKE_PAGE_NAME = translation.ugettext(
    'Take organization application')

ORG_APP_UPDATE_PAGE_NAME = translation.ugettext(
    'Update organization application')

NO_ORG_APP = translation.ugettext(
    'The organization application for the program %s does not exist.')

GENERAL_INFO_GROUP_TITLE = translation.ugettext('General Info')

OTHER_OPTION_FIELD_ID = '%s-other'


def cleanOrgId(org_id):
  """Cleans org_id field.

  Args:
    org_id: The submitted organization ID.

  Returns:
    Cleaned value for org_id field.

  Raises:
    django_forms.ValidationError if the submitted value is not valid.
  """
  if not org_id:
    raise django_forms.ValidationError('This field is required.')

  cleaning.cleanLinkID(org_id)

  return org_id


class OrgAppForm(gsoc_forms.SurveyTakeForm):
  """Form to submit organization application by prospective organization
  administrators.
  """

  org_id = django_forms.CharField(
      required=True, label=ORG_ID_LABEL, help_text=ORG_ID_HELP_TEXT)

  name = django_forms.CharField(
      required=True, label=ORG_NAME_LABEL, help_text=ORG_NAME_HELP_TEXT)

  Meta = object

  def clean_org_id(self):
    """Cleans org_id field.

    Returns:
      Cleaned value for org_id field.

    Raises:
      django_forms.ValidationError if the submitted value is not valid.
    """
    return cleanOrgId(self.cleaned_data['org_id'])

  def getOrgProperties(self):
    """Returns properties of the organization that were submitted in this form.

    Returns:
      A dict mapping organization properties to the corresponding values.
    """
    properties = {}
    if 'name' in self.cleaned_data:
      properties['name'] = self.cleaned_data['name']
    if 'org_id' in self.cleaned_data:
      properties['org_id'] = self.cleaned_data['name']
    return properties

  def getApplicationResponseProperties(self):
    """Returns answers to the application response that were submitted
    in this form.

    Returns:
      A dict mapping organization application questsions to
      corresponding responses.
    """
    # list of field IDs that belong to the organization application
    field_ids = [field.field_id for field in surveys.SurveySchema(self.survey)]

    properties = {}
    for field_id, value in self.cleaned_data.iteritems():
      if field_id in field_ids:
        properties[field_id] = value

        # add possible value of 'other' option
        other_option_field_id = OTHER_OPTION_FIELD_ID % field_id
        if other_option_field_id in self.cleaned_data:
          properties[other_option_field_id] = self.cleaned_data[
              other_option_field_id]

    return properties


def _formToTakeOrgApp(**kwargs):
  """Returns a Django form to submit a new organization application.

  Returns:
    OrgAppForm adjusted to submit a new organization application.
  """
  return OrgAppForm(**kwargs)


def _formToEditOrgApp(**kwargs):
  """Returns a django form to update an existing organization application.

  Returns:
    OrgAppForm adjusted to update an existing organization application.
  """
  form = OrgAppForm(**kwargs)

  # organization ID property is not editable
  del form.fields['org_id']

  return form


class OrgAppTakePage(base.GSoCRequestHandler):
  """View to take organization application."""

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        soc_url_patterns.url(
            r'org/application/take/%s$' % url_patterns.PROGRAM,
            self, name=urls.UrlNames.ORG_APP_TAKE)]

  # TODO(daniel): replace it with a new style access checker
  def checkAccess(self, data, check, mutator):
    """See base.RequestHandler.checkStyle for specification."""
    if not data.org_app:
      raise exception.NotFound(message=NO_ORG_APP % data.program.name)

    check.isSurveyActive(data.org_app)
    check.canTakeOrgApp()

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'modules/gsoc/org_app/take.html'

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    form = _formToTakeOrgApp(survey=data.org_app, data=data.POST or None)

    return {
        'page_name': ORG_APP_TAKE_PAGE_NAME,
        'description': data.org_app.content,
        'forms': [form],
        'error': bool(form.errors)
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = _formToTakeOrgApp(survey=data.org_app, data=data.POST)

    if not form.is_valid():
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)
    else:
      org_id = form.cleaned_data['org_id']
      org_properties = {'name': form.cleaned_data['name']}
      app_properties = form.getApplicationResponseProperties()
      
      result = createOrganizationWithApplicationTxn(
          org_id, data.program.key(), data.org_app.key(), org_properties,
          app_properties, data.models)

      if not result:
        # TODO(nathaniel): problematic self-use.
        # TODO(daniel): I would like to be able to forward the error
        # message so that it is printed to the user.
        return self.get(data, check, mutator)
      else:
        url = links.LINKER.organization(
          result.extra, urls.UrlNames.ORG_APP_UPDATE)
        return http.HttpResponseRedirect(url)


class OrgAppUpdatePage(base.GSoCRequestHandler):
  """View to update organization application response."""

  # TODO(daniel): implement actual access checker
  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'modules/gsoc/org_app/take.html'

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        soc_url_patterns.url(
            r'org/application/update/%s$' % url_patterns.ORG,
            self, name=urls.UrlNames.ORG_APP_UPDATE)]

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    form_data = data.url_ndb_org.to_dict()
    form_data.update(
        org_logic.getApplicationResponse(data.url_ndb_org.key).to_dict())

    form = _formToEditOrgApp(survey=data.org_app, data=data.POST or form_data)

    return {
        'page_name': ORG_APP_UPDATE_PAGE_NAME,
        'description': data.org_app.content,
        'forms': [form],
        'error': bool(form.errors)
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = _formToEditOrgApp(survey=data.org_app, data=data.POST)
    if not form.is_valid():
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)
    else:
      org_properties = form.getOrgProperties()
      app_response_properties = form.getApplicationResponseProperties()
      updateOrganizationWithApplicationTxn(
          data.url_ndb_org.key, org_properties, app_response_properties)

      url = links.LINKER.organization(
          data.url_ndb_org, urls.UrlNames.ORG_APP_UPDATE)
      return http.HttpResponseRedirect(url)


class OrgAppShowPage(base.GSoCRequestHandler):
  """Page to display organization application response."""

  # TODO(daniel): implement actual access checker
  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    # TODO(daniel): remove 2 when the old view is removed.
    return [
        soc_url_patterns.url(
            r'org/application/show2/%s$' % url_patterns.ORG,
            self, name=urls.UrlNames.ORG_APP_SHOW)]

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'modules/gsoc/org_app/show.html'

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    groups = []

    fields = collections.OrderedDict()
    fields[data.models.ndb_org_model.org_id._verbose_name] = (
        data.url_ndb_org.org_id)
    fields[data.models.ndb_org_model.name._verbose_name] = (
        data.url_ndb_org.name)
    groups.append(
        readonly_template.Group(GENERAL_INFO_GROUP_TITLE, fields.items()))

    app_response = org_logic.getApplicationResponse(data.url_ndb_org.key)
    groups.append(
        readonly_template.SurveyResponseGroup(data.org_app, app_response))

    response_template = readonly_template.SurveyResponseReadOnlyTemplate(
        'summerofcode/_readonly_template.html', groups)

    return {'record': response_template}


@ndb.transactional
def createOrganizationWithApplicationTxn(
    org_id, program_key, app_key, org_properties, app_properties, models):
  """Creates a new organization and saves a corresponding survey response
  for the specified data.

  This function simply calls organization logic's function to do actual job
  but ensures that the entire operation is executed within a transaction.

  Args:
    org_id: Identifier of the new organization. Must be unique on
      'per program' basis.
    program_key: Program key.
    app_key: Organization application key.
    org_properties: A dict mapping organization properties to their values.
    app_properties: A dict mapping organization application questions to
      corresponding responses.
    models: 

  Returns:
    RichBool whose value is set to True if organization and application
    response have been successfully created. In that case, extra part points to
    the newly created organization entity. Otherwise, RichBool whose value is
    set to False and extra part is a string that represents the reason why
    the action could not be completed.
  """
  return org_logic.createOrganizationWithApplication(
      org_id, program_key, app_key, org_properties, app_properties, models)


@ndb.transactional
def updateOrganizationWithApplicationTxn(
    org_key, org_properties, app_response_properties):
  """Updates properties of the specified organization as well as application
  response for that organization.

  This function simply calls organization logic's function to do actual job
  but ensures that the entire operation is executed within a transaction.

  Args:
    org_key: Organization key.
    org_properties: A dict containing properties to be updated.
    app_response_properties: A dict containing organization application
      questions to be updated.
  """
  org = org_key.get()
  org_logic.updateOrganizationWithApplication(
      org, org_properties, app_response_properties)
