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
import json

from google.appengine.ext import ndb

from django import forms as django_forms
from django import http
from django.utils import translation

from melange.logic import contact as contact_logic
from melange.logic import organization as org_logic
from melange.logic import profile as profile_logic
from melange.models import connection as connection_model
from melange.models import organization as org_model
from melange.request import access
from melange.request import exception
from melange.request import links
# TODO(daniel): Was survey_response_list accidentally left out of a commit?
from melange.templates import survey_response_list  # pylint: disable=no-name-in-module
from melange.utils import lists as melange_lists
from melange.utils import time as time_utils
from melange.views import connection as connection_view
from melange.views.helper import form_handler

from soc.logic import cleaning
from soc.models import licenses
from soc.models import program as program_model

from soc.views import readonly_template
from soc.views import template
from soc.views.helper import url as url_helper
from soc.views.helper import url_patterns
from soc.views.helper import lists

from soc.modules.gsoc.logic import conversation_updater
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
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

TAGS_HELP_TEXT = translation.ugettext(
    'Comma separated list of organization tags. Each tag must be shorter '
    'than %s characters.')

IDEAS_PAGE_HELP_TEXT = translation.ugettext(
    'The URL to a page with list of ideas for projects for this organization.')

IDEAS_PAGE_HELP_TEXT_WITH_FAQ = translation.ugettext(
    'The URL to a page with list of ideas for projects for this organization.'
    'This is the most important part of your application. You can read about '
    'ideas lists on the <a href="%s">FAQs</a>')

LICENSE_HELP_TEXT = translation.ugettext(
    'The main license which is used by this organization.')

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

IS_VETERAN_HELP_TEXT = translation.ugettext(
    'Check this field if the organization has participated in a previous '
    'instance of the program.')

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

MAX_SCORE_HELP_TEXT = translation.ugettext(
    'The maximum number of points that can be given to a proposal by '
    'one mentor. Please keep in mind changing this value does not have impact '
    'on the existing scores. In particular, scores, which have been higher '
    'than the updated maximum value, are still considered valid.')

ORG_ID_LABEL = translation.ugettext('Organization ID')

ORG_NAME_LABEL = translation.ugettext('Organization name')

DESCRIPTION_LABEL = translation.ugettext('Description')

TAGS_LABEL = translation.ugettext('Tags')

IDEAS_PAGE_LABEL = translation.ugettext('Ideas list')

LICENSE_LABEL = translation.ugettext('Main license')

LOGO_URL_LABEL = translation.ugettext('Logo URL')

MAILING_LIST_LABEL = translation.ugettext('Mailing list')

WEB_PAGE_LABEL = translation.ugettext('Organization website')

IRC_CHANNEL_LABEL = translation.ugettext('IRC Channel')

FEED_URL_LABEL = translation.ugettext('Feed URL')

GOOGLE_PLUS_LABEL = translation.ugettext('Google+ URL')

TWITTER_LABEL = translation.ugettext('Twitter URL')

BLOG_LABEL = translation.ugettext('Blog page')

FACEBOOK_LABEL = translation.ugettext('Facebook URL')

IS_VETERAN_LABEL = translation.ugettext('Veteran organization')

BACKUP_ADMIN_LABEL = translation.ugettext('Backup administrator')

SLOTS_REQUEST_MIN_LABEL = translation.ugettext('Min slots requested')

SLOTS_REQUEST_MAX_LABEL = translation.ugettext('Max slots requested')

MAX_SCORE_LABEL = translation.ugettext('Max score')

# TODO(daniel): list of countries should be program-specific
ELIGIBLE_COUNTRY_LABEL = translation.ugettext(
    'I hereby declare that the applying organization is not located in '
    'any of the countries which are not eligible to participate in the '
    'program: Iran, Syria, Cuba, Sudan, North Korea and Myanmar (Burma).')

ORG_APPLICATION_SUBMIT_PAGE_NAME = translation.ugettext(
    'Submit application')

ORG_APPLICATION_SHOW_PAGE_NAME = translation.ugettext(
    'Organization application - %s')

ORG_SURVEY_RESPONSE_SHOW_PAGE_NAME = translation.ugettext(
    'Organization questionnaire - %s')

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

TAG_TOO_LONG = translation.ugettext('Tag %s is too long: %s')

GENERAL_INFO_GROUP_TITLE = translation.ugettext('General Info')
CONTACT_GROUP_TITLE = translation.ugettext('Contact')

ORGANIZATION_LIST_DESCRIPTION = 'List of organizations'

_CONTACT_PROPERTIES_FORM_KEYS = [
    'blog', 'facebook', 'feed_url', 'google_plus', 'irc_channel',
    'mailing_list', 'twitter', 'web_page']

_ORG_PREFERENCES_PROPERTIES_FORM_KEYS = [
    'max_score', 'slot_request_max', 'slot_request_min']

_ORG_PROFILE_PROPERTIES_FORM_KEYS = [
    'description', 'ideas_page', 'logo_url', 'name', 'org_id', 'tags',
    'license', 'is_veteran']

TAG_MAX_LENGTH = 30
MAX_SCORE_MIN_VALUE = 1
MAX_SCORE_MAX_VALUE = 12

_LICENSE_CHOICES = ((_license, _license) for _license in licenses.LICENSES)

_SET_STATUS_BUTTON_ID = 'save'


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
  elif profile.key == request_data.ndb_profile.key:
    raise django_forms.ValidationError(OTHER_PROFILE_IS_THE_CURRENT_PROFILE)
  else:
    return profile


def cleanTags(tags):
  """Cleans tags field.

  Args:
    tags: The submitted value, which is a comma separated string with tags.

  Returns:
    A list of submitted tags.

  Raises:
    django_forms.ValidationError if at least one of the tags is not valid.
  """
  tag_list = []
  for tag in [tag for tag in tags.split(',') if tag]:
    if len(tag) > TAG_MAX_LENGTH:
      raise django_forms.ValidationError(TAG_TOO_LONG % (tag, len(tag)))
    tag_list.append(tag.strip())
  return tag_list


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

  tags = django_forms.CharField(
      required=False, label=TAGS_LABEL,
      help_text=TAGS_HELP_TEXT % TAG_MAX_LENGTH)

  license = django_forms.CharField(
      required=True, label=LICENSE_LABEL, help_text=LICENSE_HELP_TEXT,
      widget=django_forms.Select(choices=_LICENSE_CHOICES))

  logo_url = django_forms.URLField(
      required=False, label=LOGO_URL_LABEL, help_text=LOGO_URL_HELP_TEXT)

  ideas_page = django_forms.URLField(
      required=True, label=IDEAS_PAGE_LABEL)

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

  is_veteran = django_forms.BooleanField(
      required=False, label=IS_VETERAN_LABEL, help_text=IS_VETERAN_HELP_TEXT)

  backup_admin = django_forms.CharField(
      required=True, label=BACKUP_ADMIN_LABEL,
      help_text=BACKUP_ADMIN_HELP_TEXT)

  eligible_country = django_forms.BooleanField(
      required=True, label=ELIGIBLE_COUNTRY_LABEL)

  Meta = object

  def __init__(self, request_data=None, **kwargs):
    """Initializes a new form.

    Args:
      request_data: request_data.RequestData for the current request.
    """
    super(_OrgProfileForm, self).__init__(**kwargs)
    self.request_data = request_data

    # set help text for ideas page.
    help_page_key = program_model.Program.help_page.get_value_for_datastore(
        self.request_data.program)
    if help_page_key:
      self.fields['ideas_page'].help_text = (
          IDEAS_PAGE_HELP_TEXT_WITH_FAQ %
              self.request_data.redirect.document(help_page_key).url())
    else:
      self.fields['ideas_page'].help_text = IDEAS_PAGE_HELP_TEXT

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

  def clean_tags(self):
    """Cleans tags field.

    Returns:
      A list of submitted tags.

    Raises:
      django_forms.ValidationError if at least one of the tags is not valid.
    """
    return cleanTags(self.cleaned_data['tags'])

  def getContactProperties(self):
    """Returns properties of the contact information that were submitted in
    the form.

    Returns:
      A dict mapping contact properties to the corresponding values.
    """
    return self._getPropertiesForFields(_CONTACT_PROPERTIES_FORM_KEYS)

  def getOrgProperties(self):
    """Returns properties of the organization that were submitted in this form.

    Returns:
      A dict mapping organization properties to the corresponding values.
    """
    return self._getPropertiesForFields(_ORG_PROFILE_PROPERTIES_FORM_KEYS)


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

  # the declaration is submitted only when organization profile is created
  del form.fields['eligible_country']

  return form


class _OrgPreferencesForm(gsoc_forms.GSoCModelForm):
  """Form to set preferences of organization by organization administrators."""

  slot_request_min = django_forms.IntegerField(
      label=SLOTS_REQUEST_MIN_LABEL, help_text=SLOTS_REQUEST_MIN_HELP_TEXT,
      required=True)

  slot_request_max = django_forms.IntegerField(
      label=SLOTS_REQUEST_MAX_LABEL, help_text=SLOTS_REQUEST_MAX_HELP_TEXT,
      required=True)

  max_score = django_forms.IntegerField(
      label=MAX_SCORE_LABEL, help_text=MAX_SCORE_HELP_TEXT,
      min_value=MAX_SCORE_MIN_VALUE, max_value=MAX_SCORE_MAX_VALUE)

  Meta = object

  def getOrgProperties(self):
    """Returns properties of the organization that were submitted in this form.

    Returns:
      A dict mapping organization preferences properties to
      the corresponding values.
    """
    return self._getPropertiesForFields(_ORG_PREFERENCES_PROPERTIES_FORM_KEYS)


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

  access_checker = access.ConjuctionAccessChecker([
      access.NON_STUDENT_PROFILE_ACCESS_CHECKER,
      access.ORG_SIGNUP_ACTIVE_ACCESS_CHECKER])

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'summerofcode/organization/org_profile_edit.html'

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
        'description': data.org_app.content,
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
            data, org_id, data.program.key(), org_properties,
            [data.ndb_profile.key, form.cleaned_data['backup_admin'].key],
            data.models)

        if not result:
          raise exception.BadRequest(message=result.extra)
        else:
          url = links.LINKER.organization(
              result.extra.key, urls.UrlNames.ORG_APPLICATION_SUBMIT)
          return http.HttpResponseRedirect(url)


class OrgProfileEditPage(base.GSoCRequestHandler):
  """View to edit organization profile."""

  access_checker = access.IS_USER_ORG_ADMIN_FOR_NDB_ORG

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

    # initialize list of tags as comma separated list of values
    form_data['tags'] = ', '.join(form_data['tags'])

    if data.url_ndb_org.contact:
      form_data.update(data.url_ndb_org.contact.to_dict())

    form = _formToEditOrgProfile(request_data=data, data=data.POST or form_data)

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
    form = _formToEditOrgProfile(request_data=data, data=data.POST)
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


ORG_PREFERENCES_EDIT_PAGE_ACCESS_CHECKER = access.ConjuctionAccessChecker([
    access.IS_USER_ORG_ADMIN_FOR_NDB_ORG,
    access.UrlOrgStatusAccessChecker([org_model.Status.ACCEPTED])])

class OrgPreferencesEditPage(base.GSoCRequestHandler):
  """View to edit organization preferences."""

  access_checker = ORG_PREFERENCES_EDIT_PAGE_ACCESS_CHECKER

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

  access_checker = access.ConjuctionAccessChecker([
      access.IS_USER_ORG_ADMIN_FOR_NDB_ORG,
      access.UrlOrgStatusAccessChecker(
          [org_model.Status.APPLYING, org_model.Status.PRE_ACCEPTED,
          org_model.Status.PRE_REJECTED])])

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
  """Page to display organization application response for program
  administrators.
  """

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

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

    # General Info group
    fields = collections.OrderedDict()
    fields[ORG_ID_LABEL] = data.url_ndb_org.org_id
    fields[ORG_NAME_LABEL] = data.url_ndb_org.name
    fields[IS_VETERAN_LABEL] = data.url_ndb_org.is_veteran
    fields[DESCRIPTION_LABEL] = data.url_ndb_org.description
    fields[TAGS_LABEL] = ', '.join(data.url_ndb_org.tags)
    fields[LICENSE_LABEL] = data.url_ndb_org.license
    fields[LOGO_URL_LABEL] = data.url_ndb_org.logo_url
    fields[IDEAS_PAGE_LABEL] = data.url_ndb_org.ideas_page
    groups.append(
        readonly_template.Group(GENERAL_INFO_GROUP_TITLE, fields.items()))

    # Contact group
    fields = collections.OrderedDict()
    fields[MAILING_LIST_LABEL] = data.url_ndb_org.contact.mailing_list
    fields[WEB_PAGE_LABEL] = data.url_ndb_org.contact.web_page
    fields[IRC_CHANNEL_LABEL] = data.url_ndb_org.contact.irc_channel
    fields[FEED_URL_LABEL] = data.url_ndb_org.contact.feed_url
    fields[GOOGLE_PLUS_LABEL] = data.url_ndb_org.contact.google_plus
    fields[TWITTER_LABEL] = data.url_ndb_org.contact.twitter
    fields[BLOG_LABEL] = data.url_ndb_org.contact.blog
    fields[FACEBOOK_LABEL] = data.url_ndb_org.contact.facebook
    groups.append(
        readonly_template.Group(CONTACT_GROUP_TITLE, fields.items()))

    app_response = org_logic.getApplicationResponse(data.url_ndb_org.key)
    groups.append(
        readonly_template.SurveyResponseGroup(data.org_app, app_response))

    response_template = readonly_template.SurveyResponseReadOnlyTemplate(
        'summerofcode/_readonly_template.html', groups)

    return {
        'page_name': ORG_APPLICATION_SHOW_PAGE_NAME % data.url_ndb_org.name,
        'record': response_template
        }


class SurveyResponseShowPage(base.GSoCRequestHandler):
  """Page to display survey response."""

  access_checker = access.IS_USER_ORG_ADMIN_FOR_NDB_ORG

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        soc_url_patterns.url(
            r'org/survey_response/show/%s$' % url_patterns.ORG,
            self, name=urls.UrlNames.ORG_SURVEY_RESPONSE_SHOW)]

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'modules/gsoc/org_app/show.html'

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    app_response = org_logic.getApplicationResponse(data.url_ndb_org.key)
    groups = [readonly_template.SurveyResponseGroup(data.org_app, app_response)]

    response_template = readonly_template.SurveyResponseReadOnlyTemplate(
        'summerofcode/_readonly_template.html', groups)

    return {
        'page_name': ORG_SURVEY_RESPONSE_SHOW_PAGE_NAME % data.url_ndb_org.name,
        'record': response_template
        }


# TODO(daniel): replace this class with new style list
class PublicOrganizationList(template.Template):
  """Public list of organizations participating in a specified program."""

  def __init__(self, data):
    """See template.Template.__init__ for specification."""
    super(PublicOrganizationList, self).__init__(data)
    self._list_config = lists.ListConfiguration()
    self._list_config.addPlainTextColumn(
        'name', 'Name', lambda e, *args: e.name.strip())
    self._list_config.addPlainTextColumn(
        'tags', 'Tags', lambda e, *args: ', '.join(e.tags))
    self._list_config.addPlainTextColumn('ideas', 'Ideas',
        lambda e, *args: url_helper.urlize(e.ideas, name='[ideas page]'),
        hidden=True)

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

_STATUS_APPLYING_ID = translation.ugettext('Needs review')
_STATUS_PRE_ACCEPTED_ID = translation.ugettext('Pre-accepted')
_STATUS_PRE_REJECTED_ID = translation.ugettext('Pre-rejected')
_STATUS_ACCEPTED_ID = translation.ugettext('Accepted')
_STATUS_REJECTED_ID = translation.ugettext('Rejected')

_STATUS_ID_TO_ENUM_LINK = (
    (_STATUS_APPLYING_ID, org_model.Status.APPLYING),
    (_STATUS_PRE_ACCEPTED_ID, org_model.Status.PRE_ACCEPTED),
    (_STATUS_PRE_REJECTED_ID, org_model.Status.PRE_REJECTED),
    (_STATUS_ACCEPTED_ID, org_model.Status.ACCEPTED),
    (_STATUS_REJECTED_ID, org_model.Status.REJECTED),
    )
_STATUS_ID_TO_ENUM_MAP = dict(_STATUS_ID_TO_ENUM_LINK)
_STATUS_ENUM_TO_ID_MAP = dict(
    (v, k) for (k, v) in _STATUS_ID_TO_ENUM_LINK)

class OrgApplicationList(template.Template):
  """List of organization applications that have been submitted for the program.
  """

  def __init__(self, data, survey, idx=0, description=None):
    """Creates a new OrgApplicationList template.

    Args:
      data: request_data.RequestData object for the current request.
      survey: Survey entity to show the responses for
      idx: The index of the list to use.
      description: The (optional) description of the list.
    """
    super(OrgApplicationList, self).__init__(data)

    self.idx = idx
    self.description = description or ''
    self.list_config = lists.ListConfiguration()

    self.list_config.addPlainTextColumn(
        'key', 'Key', lambda entity, *args: entity.key.parent().id(),
        hidden=True)
    self.list_config.addSimpleColumn(
        'created_on', 'Created On', column_type=lists.DATE)
    self.list_config.addSimpleColumn(
        'modified_on', 'Last Modified On', column_type=lists.DATE)
    self.list_config.addPlainTextColumn(
        'name', 'Name', lambda entity, *args: entity.key.parent().get().name)
    self.list_config.addPlainTextColumn(
        'org_id', 'Organization ID',
        lambda entity, *args: entity.key.parent().get().org_id)
    self.list_config.addPlainTextColumn(
        'new_or_veteran', 'New/Veteran',
        lambda entity, *args:
            'Veteran' if entity.key.parent().get().is_veteran else 'New')
    self.list_config.addPlainTextColumn(
        'description', 'Description',
        lambda entity, *args: entity.key.parent().get().description)
    self.list_config.addPlainTextColumn(
        'license', 'License',
        lambda entity, *args: entity.key.parent().get().license)
    self.list_config.addPlainTextColumn(
        'ideas_page', 'Ideas Page',
        lambda entity, *args: entity.key.parent().get().ideas_page)

    survey_response_list.addColumnsForSurvey(self.list_config, survey)

    # TODO(ljvderijk): Poke Mario during all-hands to see if we can separate
    # "search options" and in-line selection options.
    options = [
        ('', 'All'),
        ('(%s)' % _STATUS_APPLYING_ID, _STATUS_APPLYING_ID),
        ('(%s)' % _STATUS_PRE_ACCEPTED_ID, _STATUS_PRE_ACCEPTED_ID),
        ('(%s)' % _STATUS_PRE_REJECTED_ID, _STATUS_PRE_REJECTED_ID),
        # TODO(daniel): figure out how ignored state is used.
        # ('(ignored)', 'ignored'),
    ]

    self.list_config.addPlainTextColumn(
        'status', 'Status',
        lambda entity, *args:
            _STATUS_ENUM_TO_ID_MAP[entity.key.parent().get().status],
        options=options)
    self.list_config.setColumnEditable('status', True, 'select')
    self.list_config.addPostEditButton(_SET_STATUS_BUTTON_ID, 'Save')

    self.list_config.setRowAction(
        lambda entity, *args: links.LINKER.organization(
            entity.key.parent(), urls.UrlNames.ORG_APP_SHOW))

  def templatePath(self):
    """See template.Template.templatePath for specification."""
    return 'summerofcode/organization/_org_application_list.html'

  def context(self):
    """See template.Template.context for specification."""
    description = ORGANIZATION_LIST_DESCRIPTION

    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self.list_config, 0, description)

    return {'lists': [list_configuration_response]}

  def getListData(self):
    """Returns data for the list."""
    query = org_logic.getApplicationResponsesQuery(self.data.org_app.key())

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self.list_config, query, lists.keyStarter,
        prefetcher=None)
    return response_builder.buildNDB()


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
    return links.LINKER.organization(org_key, urls.UrlNames.ORG_HOME)


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
    query = data.models.ndb_org_model.query(
        org_model.Organization.program ==
            ndb.Key.from_old_key(data.program.key()),
        org_model.Organization.status == org_model.Status.ACCEPTED)

    response = melange_lists.JqgridResponse(
        melange_lists.ORGANIZATION_LIST_ID,
        row=PublicOrganizationListRowRedirect(data))

    start = data.GET.get('start')

    return response.getData(query, start=start)

  def context(self, data, check, mutator):
    """See base.GSoCRequestHandler.context for specification."""
    return {
        'page_name': "Accepted organizations for %s" % data.program.name,
        'accepted_orgs_list': PublicOrganizationList(data),
    }


class OrgApplicationListPage(base.GSoCRequestHandler):
  """View to list all applications that have been submitted in the program."""

  # TODO(daniel): This list should be active only when org application is set.
  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def templatePath(self):
    """See base.GSoCRequestHandler.templatePath for specification."""
    return 'soc/org_app/records.html'

  def djangoURLPatterns(self):
    """See base.GSoCRequestHandler.djangoURLPatterns for specification."""
    return [
        soc_url_patterns.url(
            r'org/application/list/%s$' % url_patterns.PROGRAM, self,
            name=urls.UrlNames.ORG_APPLICATION_LIST)]

  def jsonContext(self, data, check, mutator):
    """See base.GSoCRequestHandler.jsonContext for specification."""
    idx = lists.getListIndex(data.request)
    if idx == 0:
      list_data = OrgApplicationList(data, data.org_app).getListData()
      return list_data.content()
    else:
      raise exception.BadRequest(message='Invalid ID has been specified.')

  def context(self, data, check, mutator):
    """See base.GSoCRequestHandler.context for specification."""
    record_list = OrgApplicationList(data, data.org_app)

    page_name = translation.ugettext('Records - %s' % (data.org_app.title))
    context = {
        'page_name': page_name,
        'record_list': record_list,
        }
    return context

  def post(self, data, check, mutator):
    """See base.GSoCRequestHandler.post for specification."""
    button_id = data.POST.get('button_id')
    if button_id is not None:
      if button_id == _SET_STATUS_BUTTON_ID:
        handler = SetOrganizationStatusHandler(self)
        return handler.handle(data, check, mutator)
      else:
        raise exception.BadRequest(
            message='Button id %s not supported.' % button_id)
    else:
      raise exception.BadRequest(message='Invalid POST data.')


class SetOrganizationStatusHandler(form_handler.FormHandler):
  """Form handler implementation to set status of organizations based on
  data which is sent in a request.
  """

  def handle(self, data, check, mutator):
    """See form_handler.FormHandler.handle for specification."""
    post_data = data.POST.get('data')

    if not post_data:
      raise exception.BadRequest(message='Missing data.')

    parsed_data = json.loads(post_data)
    for org_key_id, properties in parsed_data.iteritems():
      org_key = ndb.Key(
          data.models.ndb_org_model._get_kind(), org_key_id)
      new_status = _STATUS_ID_TO_ENUM_MAP.get(properties.get('status'))
      if not new_status:
        raise exception.BadRequest(
            message='Missing or invalid new status in POST data.')
      else:
        organization = org_key.get()
        org_logic.setStatus(organization, data.program, data.site,
                            data.program.getProgramMessages(), new_status)
        return http.HttpResponse()


# TODO(nathaniel): remove suppression when
# https://bitbucket.org/logilab/pylint.org/issue/6/false-positive-no
# is fixed.
@ndb.transactional(xg=True)  # pylint: disable=no-value-for-parameter
def createOrganizationTxn(
    data, org_id, program_key, org_properties, admin_keys, models):
  """Creates a new organization profile based on the specified properties.

  This function simply calls organization logic's function to do actual job
  but ensures that the entire operation is executed within a transaction.

  Args:
    data: request_data.RequestData for the current request.
    org_id: Identifier of the new organization. Must be unique on
      'per program' basis.
    program_key: Program key.
    org_properties: A dict mapping organization properties to their values.
    admin_keys: List of profile keys of organization administrators for
      this organization.
    models: instance of types.Models that represent appropriate models.

  Returns:
    RichBool whose value is set to True if organization has been successfully
    created. In that case, extra part points to the newly created organization
    entity. Otherwise, RichBool whose value is set to False and extra part is
    a string that represents the reason why the action could not be completed.
  """
  result = org_logic.createOrganization(
      org_id, program_key, org_properties, models)
  if not result:
    raise exception.BadRequest(message=result.extra)

  for admin_key in admin_keys:
    connection_view.createConnectionTxn(
        data, admin_key, result.extra,
        conversation_updater.CONVERSATION_UPDATER,
        org_role=connection_model.ORG_ADMIN_ROLE,
        user_role=connection_model.ROLE)

  return result


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
