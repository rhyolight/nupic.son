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

from melange.logic import contact as contact_logic
from melange.logic import organization as org_logic
from melange.logic import profile as profile_logic
from melange.models import connection as connection_model
from melange.request import access
from melange.request import exception
from melange.request import links
from melange.utils import lists as melange_lists
from melange.views import connection as connection_view

from soc.logic import cleaning

from soc.views import readonly_template
from soc.views import template
from soc.views.helper import url_patterns
from soc.views.helper import surveys
from soc.views.helper import lists

from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper import url_patterns as soc_url_patterns

from summerofcode.views.helper import urls


ORG_ID_HELP_TEXT = translation.ugettext(
    'Organization ID is used as part of various URL links throughout '
    ' the site. You may reuse the same id for different years of the program. '
    '<a href="http://en.wikipedia.org/wiki/ASCII">ASCII</a> alphanumeric '
    'characters, digits, and underscores only.')

ORG_NAME_HELP_TEXT = translation.ugettext(
    'Complete, formal name of the organization.')

DESCRIPTION_HELP_TEXT = translation.ugettext(
    'Description of the organization to be displayed on a public profile page.')

IDEAS_PAGE_HELP_TEXT = translation.ugettext(
    'The URL to a page with list of ideas for projects for this organization.')

LOGO_URL_HELP_TEXT = translation.ugettext(
    'URL to the logo of the organization. Please ensure that the provided '
    'image is smaller than 65px65px.')

MAILING_LIST_HELP_TEXT = translation.ugettext(
    'Mailing list email address, URL to sign-up page, etc.')

WEB_PAGE_HELP_TEXT = translation.ugettext(
    'Main website of the organization.')

IRC_CHANNEL_HELP_TEXT = translation.ugettext(
    'Public IRC channel which may be used to get in touch with developers.')

FEED_URL_HELP_TEXT = translation.ugettext(
    'The URL should be a valid ATOM or RSS feed. Feed entries are shown on '
    'the organization home page in Melange.')

GOOGLE_PLUS_HELP_TEXT = translation.ugettext(
    'URL to the Google+ page of the organization.')

TWITTER_HELP_TEXT = translation.ugettext(
    'URL of the Twitter page of the organization.')

BLOG_HELP_TEXT = translation.ugettext(
    'URL to the blog page of the organization.')

BACKUP_ADMIN_HELP_TEXT = translation.ugettext(
    'Username of the user who will also serve as administrator for this '
    'organization. Please note that the user must have created '
    'a profile for the current program in order to be eligible. '
    'The organization will be allowed to assign more administrators upon '
    'acceptance into the program.')

ORG_ID_LABEL = translation.ugettext('Organization ID')

ORG_NAME_LABEL = translation.ugettext('Organization name')

DESCRIPTION_LABEL = translation.ugettext('Description')

IDEAS_PAGE_LABEL = translation.ugettext('Ideas list')

LOGO_URL_LABEL = translation.ugettext('Logo URL')

MAILING_LIST_LABEL = translation.ugettext('Mailing list')

WEB_PAGE_LABEL = translation.ugettext('Organization website')

IRC_CHANNEL_LABEL = translation.ugettext('IRC Channel')

FEED_URL_LABEL = translation.ugettext('Feed URL')

GOOGLE_PLUS_LABEL = translation.ugettext('Google+ URL')

TWITTER_LABEL = translation.ugettext('Twitter URL')

BLOG_LABEL = translation.ugettext('Blog page')

BACKUP_ADMIN_LABEL = translation.ugettext('Backup administrator')

ORG_APP_TAKE_PAGE_NAME = translation.ugettext(
    'Take organization application')

ORG_APP_UPDATE_PAGE_NAME = translation.ugettext(
    'Update organization application')

NO_ORG_APP = translation.ugettext(
    'The organization application for the program %s does not exist.')

PROFILE_DOES_NOT_EXIST = translation.ugettext(
    'No profile exists for username %s.')

OTHER_PROFILE_IS_THE_CURRENT_PROFILE = translation.ugettext(
    'The currently logged in profile cannot be specified as '
    'the other organization administrator.')

GENERAL_INFO_GROUP_TITLE = translation.ugettext('General Info')

ORGANIZATION_LIST_DESCRIPTION = 'List of organizations'

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


def cleanBackupAdmin(username, request_data):
  """Cleans backup_admin field.

  Args:
    username: Username of the user to assign as the backup administrator.
    request_data: request_data.RequestData for the current request.

  Raises:
    django_forms.ValidationError if no profile exists for at least one
    of the submitted usernames.
  """
  username = username.strip()
  profile = profile_logic.getProfileForUsername(
      username, request_data.program.key(), models=request_data.models)
  if not profile:
    raise django_forms.ValidationError(PROFILE_DOES_NOT_EXIST % username)
  elif profile.key() == request_data.profile.key():
    raise django_forms.ValidationError(OTHER_PROFILE_IS_THE_CURRENT_PROFILE)
  else:
    return profile


class OrgAppForm(gsoc_forms.SurveyTakeForm):
  """Form to submit organization application by prospective organization
  administrators.
  """

  org_id = django_forms.CharField(
      required=True, label=ORG_ID_LABEL, help_text=ORG_ID_HELP_TEXT)

  name = django_forms.CharField(
      required=True, label=ORG_NAME_LABEL, help_text=ORG_NAME_HELP_TEXT)

  # TODO(daniel): make sure this field is escaped properly
  description = django_forms.CharField(
      widget=django_forms.Textarea, required=True, label=DESCRIPTION_LABEL,
      help_text=DESCRIPTION_HELP_TEXT)

  logo_url = django_forms.URLField(
      required=False, label=LOGO_URL_LABEL, help_text=LOGO_URL_HELP_TEXT)

  ideas_page = django_forms.URLField(
      required=True, label=IDEAS_PAGE_LABEL, help_text=IDEAS_PAGE_HELP_TEXT)

  mailing_list = django_forms.CharField(
      required=False, label=MAILING_LIST_LABEL,
      help_text=MAILING_LIST_HELP_TEXT)

  web_page = django_forms.URLField(
      required=True, label=WEB_PAGE_LABEL, help_text=WEB_PAGE_HELP_TEXT)

  irc_channel = django_forms.CharField(
      required=False, label=IRC_CHANNEL_LABEL, help_text=IRC_CHANNEL_HELP_TEXT)

  feed_url = django_forms.URLField(
      required=False, label=FEED_URL_LABEL, help_text=FEED_URL_HELP_TEXT)

  google_plus = django_forms.URLField(
      required=False, label=GOOGLE_PLUS_LABEL, help_text=GOOGLE_PLUS_HELP_TEXT)

  twitter = django_forms.URLField(
      required=False, label=TWITTER_LABEL, help_text=TWITTER_HELP_TEXT)

  blog = django_forms.URLField(
      required=False, label=BLOG_LABEL, help_text=BLOG_HELP_TEXT)

  backup_admin = django_forms.CharField(
      required=True, label=BACKUP_ADMIN_LABEL,
      help_text=BACKUP_ADMIN_HELP_TEXT)

  Meta = object

  def __init__(self, request_data=None, **kwargs):
    """Initializes a new form.

    Args:
      request_data: request_data.RequestData for the current request.
    """
    super(OrgAppForm, self).__init__(**kwargs)
    self.request_data = request_data

  def clean_org_id(self):
    """Cleans org_id field.

    Returns:
      Cleaned value for org_id field.

    Raises:
      django_forms.ValidationError if the submitted value is not valid.
    """
    return cleanOrgId(self.cleaned_data['org_id'])

  def clean_backup_admin(self):
    """Cleans backup_admin field.

    Returns:
      Profile entity corresponding to the backup administrator.

    Raises:
      django_forms.ValidationError if the submitted value is not valid.
    """
    return cleanBackupAdmin(
        self.cleaned_data['backup_admin'], self.request_data)

  def getContactProperties(self):
    """Returns properties of the contact information that were submitted in
    the form.

    Returns:
      A dict mapping contact properties to the corresponding values.
    """
    properties = {}
    if 'blog' in self.cleaned_data:
      properties['blog'] = self.cleaned_data['blog']
    if 'feed_url' in self.cleaned_data:
      properties['feed_url'] = self.cleaned_data['feed_url']
    if 'google_plus' in self.cleaned_data:
      properties['google_plus'] = self.cleaned_data['google_plus']
    if 'irc_channel' in self.cleaned_data:
      properties['irc_channel'] = self.cleaned_data['irc_channel']
    if 'mailing_list' in self.cleaned_data:
      properties['mailing_list'] = self.cleaned_data['mailing_list']
    if 'twitter' in self.cleaned_data:
      properties['twitter'] = self.cleaned_data['twitter']
    if 'web_page' in self.cleaned_data:
      properties['web_page'] = self.cleaned_data['web_page']
    return properties

  def getOrgProperties(self):
    """Returns properties of the organization that were submitted in this form.

    Returns:
      A dict mapping organization properties to the corresponding values.
    """
    properties = {}
    if 'description' in self.cleaned_data:
      properties['description'] = self.cleaned_data['description']
    if 'ideas_page' in self.cleaned_data:
      properties['ideas_page'] = self.cleaned_data['ideas_page']
    if 'logo_url' in self.cleaned_data:
      properties['logo_url'] = self.cleaned_data['logo_url']
    if 'name' in self.cleaned_data:
      properties['name'] = self.cleaned_data['name']
    if 'org_id' in self.cleaned_data:
      properties['org_id'] = self.cleaned_data['org_id']
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

  # other organization admins are set only when app response is created
  del form.fields['backup_admin']

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
    form = _formToTakeOrgApp(
        request_data=data, survey=data.org_app, data=data.POST or None)

    return {
        'page_name': ORG_APP_TAKE_PAGE_NAME,
        'description': data.org_app.content,
        'forms': [form],
        'error': bool(form.errors)
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = _formToTakeOrgApp(
        request_data=data, survey=data.org_app, data=data.POST)

    if not form.is_valid():
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)
    else:
      contact_properties = form.getContactProperties()
      result = contact_logic.createContact(**contact_properties)

      if not result:
        raise exception.BadRequest(message=result.extra)
      else:
        org_properties = form.getOrgProperties()
        org_properties['contact'] = result.extra

        # org_id is a special property
        org_id = org_properties['org_id']
        del org_properties['org_id']

        app_properties = form.getApplicationResponseProperties()

        result = createOrganizationWithApplicationTxn(
            org_id, data.program.key(), data.org_app.key(),
            org_properties, app_properties, data.models)

        if not result:
          # TODO(nathaniel): problematic self-use.
          # TODO(daniel): I would like to be able to forward the error
          # message so that it is printed to the user.
          return self.get(data, check, mutator)
        else:
          # NOTE: this should rather be done within a transaction along with
          # creating the organization. At least one admin is required for
          # each organization: what if the code above fails and there are none?
          # However, it should not be a practical problem.
          admin_keys = [
              data.profile.key(), form.cleaned_data['backup_admin'].key()]
          for admin_key in admin_keys:
            connection_view.createConnectionTxn(
                data, admin_key, result.extra,
                org_role=connection_model.ORG_ADMIN_ROLE,
                user_role=connection_model.ROLE)
  
          url = links.LINKER.organization(
            result.extra.key, urls.UrlNames.ORG_APP_UPDATE)
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

    if data.url_ndb_org.contact:
      form_data.update(data.url_ndb_org.contact.to_dict())

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
      contact_properties = form.getContactProperties()
      result = contact_logic.createContact(**contact_properties)

      if not result:
        raise exception.BadRequest(message=result.extra)
      else:
        org_properties = form.getOrgProperties()
        org_properties['contact'] = result.extra

        app_response_properties = form.getApplicationResponseProperties()

        updateOrganizationWithApplicationTxn(
            data.url_ndb_org.key, org_properties, app_response_properties)

        url = links.LINKER.organization(
            data.url_ndb_org.key, urls.UrlNames.ORG_APP_UPDATE)
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


# TODO(daniel): replace this class with new style list
class PublicOrganizationList(template.Template):
  """Public list of organizations participating in a specified program."""

  def __init__(self, data):
    """See template.Template.__init__ for specification."""
    super(PublicOrganizationList, self).__init__(data)
    self._list_config = lists.ListConfiguration()
    self._list_config.addPlainTextColumn(
        'name', 'Name', lambda e, *args: e.name.strip())

  def templatePath(self):
    """See template.Template.templatePath for specification."""
    return 'modules/gsoc/admin/_accepted_orgs_list.html'

  def context(self):
    """See template.Template.context for specification."""
    description = ORGANIZATION_LIST_DESCRIPTION

    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)

    return {
        'lists': [list_configuration_response],
    }


class PublicOrganizationListRowRedirect(melange_lists.RedirectCustomRow):
  """Class which provides redirects for rows of public organization list."""

  def __init__(self, data):
    """Initializes a new instance of the row redirect.

    See lists.RedirectCustomRow.__init__ for specification.

    Args:
      data: request_data.RequestData for the current request.
    """
    super(PublicOrganizationListRowRedirect, self).__init__()
    self.data = data

  def getLink(self, item):
    """See lists.RedirectCustomRow.getLink for specification."""
    org_key = ndb.Key(
        self.data.models.ndb_org_model._get_kind(), item['columns']['key'])
    return links.LINKER.organization(org_key, url_names.GSOC_ORG_HOME)


class PublicOrganizationListPage(base.GSoCRequestHandler):
  """View to list all participating organizations in the program."""

  # TODO(daniel): the page should be accessible after orgs are announced
  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def templatePath(self):
    """See base.GSoCRequestHandler.templatePath for specification."""
    return 'modules/gsoc/accepted_orgs/base.html'

  def djangoURLPatterns(self):
    """See base.GSoCRequestHandler.djangoURLPatterns for specification."""
    return [
        # TODO(daniel): remove "new", when the old view is not needed anymore
        soc_url_patterns.url(
            r'org/list/public/%s$' % url_patterns.PROGRAM, self,
            name=urls.UrlNames.ORG_PUBLIC_LIST)]


  def jsonContext(self, data, check, mutator):
    """See base.GSoCRequestHandler.jsonContext for specification."""
    query = data.models.ndb_org_model.query()

    response = melange_lists.JqgridResponse(
        melange_lists.ORGANIZATION_LIST_ID,
        row=PublicOrganizationListRowRedirect(data))
    return response.getData(query)

  def context(self, data, check, mutator):
    """See base.GSoCRequestHandler.context for specification."""
    return {
        'page_name': "Accepted organizations for %s" % data.program.name,
        'accepted_orgs_list': PublicOrganizationList(data),
    }


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
