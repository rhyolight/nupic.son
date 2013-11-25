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
from melange.utils import time as time_utils
from melange.views import connection as connection_view

from soc.logic import cleaning

from soc.views import readonly_template
from soc.views import template
from soc.views.helper import url_patterns
from soc.views.helper import lists

from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper import url_patterns as soc_url_patterns

from summerofcode.templates import tabs
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

FACEBOOK_HELP_TEXT = translation.ugettext(
    'URL to the Facebook page of the organization.')

BLOG_HELP_TEXT = translation.ugettext(
    'URL to the blog page of the organization.')

BACKUP_ADMIN_HELP_TEXT = translation.ugettext(
    'Username of the user who will also serve as administrator for this '
    'organization. Please note that the user must have created '
    'a profile for the current program in order to be eligible. '
    'The organization will be allowed to assign more administrators upon '
    'acceptance into the program.')

SLOTS_REQUEST_MIN_HELP_TEXT = translation.ugettext(
    'Number of amazing proposals submitted to this organization that '
    'have a mentor assigned and the organization would <strong>really</strong> '
    'like to have a slot for.')

SLOTS_REQUEST_MAX_HELP_TEXT = translation.ugettext(
    'Number of slots that this organization would like to be assigned if '
    'there was an unlimited amount of slots available.')

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

FACEBOOK_LABEL = translation.ugettext('Facebook URL')

BACKUP_ADMIN_LABEL = translation.ugettext('Backup administrator')

SLOTS_REQUEST_MIN_LABEL = translation.ugettext('Min slots requested')

SLOTS_REQUEST_MAX_LABEL = translation.ugettext('Max slots requested')

ORG_APPLICATION_SUBMIT_PAGE_NAME = translation.ugettext(
    'Submit application')

ORG_PREFERENCES_EDIT_PAGE_NAME = translation.ugettext(
    'Edit organization preferences')

ORG_PROFILE_CREATE_PAGE_NAME = translation.ugettext(
    'Create organization profile')

ORG_PROFILE_EDIT_PAGE_NAME = translation.ugettext(
    'Edit organization profile')

NO_ORG_APP = translation.ugettext(
    'The organization application for the program %s does not exist.')

PROFILE_DOES_NOT_EXIST = translation.ugettext(
    'No profile exists for username %s.')

OTHER_PROFILE_IS_THE_CURRENT_PROFILE = translation.ugettext(
    'The currently logged in profile cannot be specified as '
    'the other organization administrator.')

GENERAL_INFO_GROUP_TITLE = translation.ugettext('General Info')

ORGANIZATION_LIST_DESCRIPTION = 'List of organizations'

_CONTACT_PROPERTIES_FORM_KEYS = [
    'blog', 'facebook', 'feed_url', 'google_plus', 'irc_channel',
    'mailing_list', 'twitter', 'web_page']

_ORG_PREFERENCES_PROPERTIES_FORM_KEYS = [
    'slot_request_max', 'slot_request_min']

_ORG_PROFILE_PROPERTIES_FORM_KEYS = [
    'description', 'ideas_page', 'logo_url', 'name', 'org_id']


def _getPropertiesForFields(form, field_keys):
  """Maps fields specified by their keys to the corresponding values
  that were submitted in the form data.

  Fields, for which the empty string was received as their value, will be
  mapped to None. This is because an occurrence of the empty string is
  regarded as if the user did not specify any actual value for the field.

  Not only are explicit None values more straightforward, but also
  there are more convenient to be persisted in AppEngine datastore.

  Args:
    form: A form.
    field_keys: A collection of identifiers of the form fields.

  Returns:
    A dict mapping the specified keys to their values.
  """
  return {
      field_key: field_value
      for field_key, field_value in form.cleaned_data.iteritems()
      if field_key in field_keys and field_value != ''
  }


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


class _OrgProfileForm(gsoc_forms.GSoCModelForm):
  """Form to set properties of organization profile by organization
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

  facebook = django_forms.URLField(
      required=False, label=FACEBOOK_LABEL, help_text=FACEBOOK_HELP_TEXT)

  backup_admin = django_forms.CharField(
      required=True, label=BACKUP_ADMIN_LABEL,
      help_text=BACKUP_ADMIN_HELP_TEXT)

  Meta = object

  def __init__(self, request_data=None, **kwargs):
    """Initializes a new form.

    Args:
      request_data: request_data.RequestData for the current request.
    """
    super(_OrgProfileForm, self).__init__(**kwargs)
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
    return _getPropertiesForFields(self, _CONTACT_PROPERTIES_FORM_KEYS)

  def getOrgProperties(self):
    """Returns properties of the organization that were submitted in this form.

    Returns:
      A dict mapping organization properties to the corresponding values.
    """
    return _getPropertiesForFields(self, _ORG_PROFILE_PROPERTIES_FORM_KEYS)


def _formToCreateOrgProfile(**kwargs):
  """Returns a Django form to create a new organization profile.

  Returns:
    _OrgProfileForm adjusted to create a new organization profile.
  """
  return _OrgProfileForm(**kwargs)


def _formToEditOrgProfile(**kwargs):
  """Returns a Django form to edit an existing organization profile.

  Returns:
    _OrgProfileForm adjusted to edit an existing organization profile.
  """
  form = _OrgProfileForm(**kwargs)

  # organization ID property is not editable
  del form.fields['org_id']

  # other organization admins are set only when organization profile is created
  del form.fields['backup_admin']

  return form


class _OrgPreferencesForm(gsoc_forms.GSoCModelForm):
  """Form to set preferences of organization by organization administrators."""

  slot_request_min = django_forms.IntegerField(
      label=SLOTS_REQUEST_MIN_LABEL, help_text=SLOTS_REQUEST_MIN_HELP_TEXT,
      required=True)

  slot_request_max = django_forms.IntegerField(
      label=SLOTS_REQUEST_MAX_LABEL, help_text=SLOTS_REQUEST_MAX_HELP_TEXT,
      required=True)

  Meta = object

  def getOrgProperties(self):
    """Returns properties of the organization that were submitted in this form.

    Returns:
      A dict mapping organization preferences properties to
      the corresponding values.
    """
    return _getPropertiesForFields(self, _ORG_PREFERENCES_PROPERTIES_FORM_KEYS)


class OrgApplicationReminder(object):
  """Reminder to be included in context if organization application has
  yet to be submitted.
  """

  def __init__(self, url, deadline):
    """Initializes a new instance of this class.

    Args:
      url: URL to Submit Organization Application page.
      deadline: a datetime by which the application has to be submitted.
    """
    self.url = url
    self.deadline = deadline


class OrgProfileCreatePage(base.GSoCRequestHandler):
  """View to create organization profile."""

  # TODO(daniel): implement actual access checker
  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'modules/gsoc/form_base.html'

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        soc_url_patterns.url(
            r'org/profile/create/%s$' % url_patterns.PROGRAM,
            self, name=urls.UrlNames.ORG_PROFILE_CREATE)]

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    form = _formToCreateOrgProfile(request_data=data, data=data.POST or None)

    return {
        'page_name': ORG_PROFILE_CREATE_PAGE_NAME,
        'forms': [form],
        'error': bool(form.errors)
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = _formToCreateOrgProfile(request_data=data, data=data.POST)

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

        result = createOrganizationTxn(
            org_id, data.program.key(), org_properties, data.models)

        if not result:
          raise exception.BadRequest(message=result.extra)
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
              result.extra.key, urls.UrlNames.ORG_APPLICATION_SUBMIT)
          return http.HttpResponseRedirect(url)


class OrgProfileEditPage(base.GSoCRequestHandler):
  """View to edit organization profile."""

  # TODO(daniel): implement actual access checker
  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'summerofcode/organization/org_profile_edit.html'

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        soc_url_patterns.url(
            r'org/profile/edit/%s$' % url_patterns.ORG,
            self, name=urls.UrlNames.ORG_PROFILE_EDIT)]

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    form_data = data.url_ndb_org.to_dict()

    if data.url_ndb_org.contact:
      form_data.update(data.url_ndb_org.contact.to_dict())

    form = _formToEditOrgProfile(data=data.POST or form_data)

    # add a reminder if no application has been submitted and it is still
    # before the deadline
    if (not org_logic.getApplicationResponse(data.url_ndb_org.key) and
        time_utils.isBefore(data.org_app.survey_end)):
      url = links.LINKER.organization(
          data.url_ndb_org.key, urls.UrlNames.ORG_APPLICATION_SUBMIT)
      deadline = data.org_app.survey_end
      org_application_reminder = OrgApplicationReminder(url, deadline)
    else:
      org_application_reminder = None

    return {
        'page_name': ORG_PROFILE_EDIT_PAGE_NAME,
        'forms': [form],
        'error': bool(form.errors),
        'tabs': tabs.orgTabs(data, selected_tab_id=tabs.ORG_PROFILE_TAB_ID),
        'org_application_reminder': org_application_reminder,
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = _formToEditOrgProfile(data=data.POST)
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

        updateOrganizationTxn(data.url_ndb_org.key, org_properties)

        url = links.LINKER.organization(
            data.url_ndb_org.key, urls.UrlNames.ORG_PROFILE_EDIT)
        return http.HttpResponseRedirect(url)


class OrgPreferencesEditPage(base.GSoCRequestHandler):
  """View to edit organization preferences."""

  # TODO(daniel): implement actual access checker
  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'modules/gsoc/form_base.html'

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        soc_url_patterns.url(
            r'org/preferences/edit/%s$' % url_patterns.ORG,
            self, name=urls.UrlNames.ORG_PREFERENCES_EDIT)]

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    form = _OrgPreferencesForm(data=data.POST or None)
    return {
        'error': bool(form.errors),
        'forms': [form],
        'page_name': ORG_PREFERENCES_EDIT_PAGE_NAME,
        'tabs': tabs.orgTabs(data, selected_tab_id=tabs.ORG_PREFERENCES_TAB_ID)
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = _OrgPreferencesForm(data=data.POST)
    if not form.is_valid():
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)
    else:
      org_properties = form.getOrgProperties()
      updateOrganizationTxn(data.url_ndb_org.key, org_properties)

      url = links.LINKER.organization(
          data.url_ndb_org.key, urls.UrlNames.ORG_PREFERENCES_EDIT)
      return http.HttpResponseRedirect(url)


class OrgApplicationSubmitPage(base.GSoCRequestHandler):
  """View to submit application to a program by organization representatives."""

  # TODO(daniel): implement actual access checker
  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        soc_url_patterns.url(
            r'org/application/submit/%s$' % url_patterns.ORG,
            self, name=urls.UrlNames.ORG_APPLICATION_SUBMIT)]

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'modules/gsoc/org_app/take.html'

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    application = org_logic.getApplicationResponse(data.url_ndb_org.key)
    form_data = application.to_dict() if application else None

    form = gsoc_forms.SurveyTakeForm(
        survey=data.org_app, data=data.POST or form_data)

    return {
        'page_name': ORG_APPLICATION_SUBMIT_PAGE_NAME,
        'forms': [form],
        'error': bool(form.errors),
        'tabs': tabs.orgTabs(data, selected_tab_id=tabs.ORG_APP_RESPONSE_TAB_ID)
        }

  def post(self, data, check, mutator):
    """See base.RequestHandler.post for specification."""
    form = gsoc_forms.SurveyTakeForm(survey=data.org_app, data=data.POST)
    if not form.is_valid():
      # TODO(nathaniel): problematic self-use.
      return self.get(data, check, mutator)
    else:
      properties = form.getSurveyResponseProperties()
      setApplicationResponse(
          data.url_ndb_org.key, data.org_app.key(), properties)

      url = links.LINKER.organization(
          data.url_ndb_org.key, urls.UrlNames.ORG_APPLICATION_SUBMIT)
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
def createOrganizationTxn(
    org_id, program_key, org_properties, models):
  """Creates a new organization profile based on the specified properties.

  This function simply calls organization logic's function to do actual job
  but ensures that the entire operation is executed within a transaction.

  Args:
    org_id: Identifier of the new organization. Must be unique on
      'per program' basis.
    program_key: Program key.
    org_properties: A dict mapping organization properties to their values.
    models: instance of types.Models that represent appropriate models.

  Returns:
    RichBool whose value is set to True if organization has been successfully
    created. In that case, extra part points to the newly created organization
    entity. Otherwise, RichBool whose value is set to False and extra part is
    a string that represents the reason why the action could not be completed.
  """
  return org_logic.createOrganization(
      org_id, program_key, org_properties, models)


@ndb.transactional
def updateOrganizationTxn(org_key, org_properties):
  """Updates the specified organization based on the specified properties.

  This function simply calls organization logic's function to do actual job
  but ensures that the entire operation is executed within a transaction.

  Args:
    org: Organization entity.
    org_properties: A dict containing properties to be updated.
  """
  org = org_key.get()
  org_logic.updateOrganization(org, org_properties)


@ndb.transactional
def setApplicationResponse(org_key, survey_key, properties):
  """Sets the specified properties for application of
  the specified organization.

  Args:
    org_key: Organization key.
    properties: A dict mapping organization application questions to
      corresponding responses.

  Returns:
    survey_model.SurveyResponse entity associated the application.
  """
  return org_logic.setApplicationResponse(org_key, survey_key, properties)
