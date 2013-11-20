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

"""Module containing the RequestData object that will be created for each
request.
"""

from google.appengine.api import users
from google.appengine.ext import db

from django import http
from django.core import urlresolvers

from melange import types
from melange.appengine import system
from melange.logic import settings as settings_logic
from melange.models import connection as connection_model
from melange.request import exception
from melange.request import links
from melange.utils import time
from melange.views.helper import urls

from soc.logic import program as program_logic
from soc.logic import site as site_logic
from soc.logic import user as user_logic
from soc.models import document as document_model
from soc.models import site as site_model
from soc.models import sponsor as sponsor_model
from soc.models import user as user_model
from soc.views.helper import access_checker


VIEW_AS_USER_DOES_NOT_EXIST = ('The requested user does not exist. Please go '
    'to <a href="%s">User Settings</a> page and change the value.')

class TimelineHelper(object):
  """Helper class for the determination of the currently active period.

  Methods ending with "On", "Start", or "End" return a date.
  Methods ending with "Between" return a tuple with two dates.
  Methods ending with neither return a Boolean.
  """

  def __init__(self, timeline, org_app):
    self.timeline = timeline
    self.org_app = org_app

  def currentPeriod(self):
    """Return where we are currently on the timeline."""
    pass

  def nextDeadline(self):
    """Determines the next deadline on the timeline."""
    pass

  def orgsAnnouncedOn(self):
    return self.timeline.accepted_organization_announced_deadline

  def beforeProgramStart(self):
    """Returns a bool indicating whether the program start date has passed
    or not.

    Returns:
      True if he current data is before program start date; False otherwise
    """
    return time.isBefore(self.timeline.program_start)

  def afterProgramStart(self):
    """Returns a bool indicating whether the program start date has passed
    or not.

    Returns:
      True if the current date is after program start date; False otherwise
    """
    return time.isAfter(self.timeline.program_start)

  def programActiveBetween(self):
    return (self.timeline.program_start, self.timeline.program_end)

  def orgSignupStart(self):
    return self.org_app.survey_start if self.org_app else None

  def orgSignupEnd(self):
    return self.org_app.survey_end if self.org_app else None

  def orgSignupBetween(self):
    return (self.org_app.survey_start, self.org_app.survey_end) if \
        self.org_app else (None, None)

  def studentSignupStart(self):
    return self.timeline.student_signup_start

  def beforeStudentSignup(self):
    """Returns a bool indicating whether the student signup start date
    has already passed or not.

    Returns:
      True if he current data is before student signup date; False otherwise
    """
    return time.isBefore(self.studentSignupStart())

  def studentSignupEnd(self):
    return self.timeline.student_signup_end

  def stopAllWorkDeadline(self):
    return self.timeline.stop_all_work_deadline

  def studentsSignupBetween(self):
    return (self.timeline.student_signup_start,
            self.timeline.student_signup_end)

  def programActive(self):
    start, end = self.programActiveBetween()
    return time.isBetween(start, end)

  def beforeOrgSignupStart(self):
    return not self.org_app or time.isBefore(self.orgSignupStart())

  def afterOrgSignupStart(self):
    return self.org_app and time.isAfter(self.orgSignupStart())

  def orgSignup(self):
    if not self.org_app:
      return False
    start, end = self.orgSignupBetween()
    return time.isBetween(start, end)

  def orgsAnnounced(self):
    return time.isAfter(self.orgsAnnouncedOn())

  def beforeStudentSignupStart(self):
    return time.isBefore(self.studentSignupStart())

  def afterStudentSignupStart(self):
    return time.isAfter(self.studentSignupStart())

  def studentSignup(self):
    start, end = self.studentsSignupBetween()
    return time.isBetween(start, end)

  def afterStudentSignupEnd(self):
    return time.isAfter(self.studentSignupEnd())

  def afterStopAllWorkDeadline(self):
    return time.isAfter(self.stopAllWorkDeadline())

  def surveyPeriod(self, survey):
    start = survey.survey_start
    end = survey.survey_end
    return time.isAfter(start) and time.isBefore(end)

  def afterSurveyStart(self, survey):
    return time.isAfter(survey.survey_start)

  def afterSurveyEnd(self, survey):
    return time.isAfter(survey.survey_end)


class RequestData(object):
  """Object containing data we query for each request.

  Fields:
    site: the singleton site.Site entity
    user: the user entity (if logged in)
    profile: the profile entity
    program: the program entity
    request: the request object (as provided by django)
    args: the request args (as provided by djang)
    kwargs: the request kwargs (as provided by django)
    path: the url of the current query, encoded as utf-8 string
    full_path: same as path, but including any GET args
    GET: the GET dictionary (from the request object)
    POST: the POST dictionary (from the request object)
    is_developer: is the current user a developer
    is_host: is the current user a host of the program
    gae_user: the Google Appengine user object
    timeline: the timeline helper
    models: types.Models implementation defining model classes

  Optional fields (may not be specified for all requests):
    url_connection: connection entity for the data in kwargs.
    url_org: organization entity for the data in kwargs.
    url_profile: profile entity for the data in kwargs.
    url_user: user entity for the data in kwargs.
  """

  # class attribute which is assigned to all fields which have not been set
  _unset = object()


  def __init__(self, request, args, kwargs):
    """Constructs a new RequestData object.

    Args:
      request: Django HTTPRequest object.
      args: The args that Django sends along with the request.
      kwargs: The kwargs that Django sends along with the request.
    """

    self.request = request
    self.args = args
    self.kwargs = kwargs
    self.models = types.MELANGE_MODELS

    self._redirect = self._unset
    self._site = self._unset
    self._sponsor = self._unset
    self._user = self._unset
    self._profile = self._unset
    self._program = self._unset

    self._GET = self._unset
    self._POST = self._unset
    # TODO(daniel): check if this field is really used
    self._path = self._unset
    self._is_developer = self._unset
    self._is_host = self._unset
    self._gae_user = self._unset
    self._ds_write_disabled = self._unset
    self._timeline = self._unset

    self._url_connection = self._unset
    self._url_org = self._unset
    self._url_ndb_org = self._unset
    self._url_profile = self._unset
    self._url_student_info = self._unset
    self._url_user = self._unset
    self._document = self._unset

    # explicitly copy POST and GET dictionaries so they can be modified
    # the default QueryDict objects used by Django are immutable, but their
    # copies may be modified
    # TODO(daniel): these dictionaries should not be modified in the first
    # place, so these copying must be eventually eliminated
    if self.request:
      self.request.POST = self.request.POST.copy()
      self.request.GET = self.request.GET.copy()

  def _isSet(self, value):
    """Checks whether the specified field has been set or not.

    Args:
      value: the specified value of one of the fields supported by this class.

    Returns:
      True if the value is set or False otherwise.
    """
    return value is not self._unset

  @property
  def css_path(self):
    """Returns the css_path property."""
    # TODO(daniel): this should not return gsoc in module
    # I believe css_path is needed in the main module because of a few sites
    # that are not specific to any module, like site or host
    return 'gsoc'

  @property
  def gae_user(self):
    """Returns the gae_user property."""
    if not self._isSet(self._gae_user):
      self._gae_user = users.get_current_user()
    return self._gae_user

  @property
  def is_developer(self):
    """Returns the is_developer field."""
    if not self._isSet(self._is_developer):
      if users.is_current_user_admin():
        self._is_developer = True
      elif self.user and self.user.is_developer:
        self._is_developer = True
      else:
        self._is_developer = False
    return self._is_developer

  @property
  def is_host(self):
    """Returns the is_host field."""
    if not self._isSet(self._is_host):
      if not self.user:
        self._is_host = False
      elif 'sponsor' in self.kwargs:
        key = db.Key.from_path('Sponsor', self.kwargs.get('sponsor'))
        self._is_host = key in self.user.host_for
      else:
        key = program_logic.getSponsorKey(self.program)
        self._is_host = key in self.user.host_for
    return self._is_host

  @property
  def path(self):
    """Returns the path field."""
    if not self._isSet(self._path):
      self._path = self.request.path.encode('utf-8')
    return self._path

  @property
  def redirect(self):
    """Returns the redirect helper."""
    if not self._isSet(self._redirect):
      self._redirect = RedirectHelper(self)
    return self._redirect

  @property
  def site(self):
    """Returns the site field."""
    if not self._isSet(self._site):
      # XSRF middleware might have already retrieved it for us
      if not hasattr(self.request, 'site'):
        # populate site.Site singleton to request field
        self.request.site = site_logic.singleton()

      self._site = self.request.site
    return self._site

  @property
  def sponsor(self):
    """Returns the sponsor field."""
    if not self._isSet(self._sponsor):
      if self.kwargs.get('sponsor'):
        sponsor_key = db.Key.from_path('Sponsor', self.kwargs['sponsor'])
      else:
        # In this case sponsor was not in the URL. Anyway, it may be still
        # possible to retrieve a reasonable sponsor, if a default program
        # is set for the site.
        # It is not the most efficient way to access the sponsor itself,
        # because it requires a program to be fetched first. It seems to
        # be acceptable, because there is a great chance that program has
        # to also be provided at some point of request's life cycle.
        sponsor_key = program_logic.getSponsorKey(self.program)

      self._sponsor = sponsor_model.Sponsor.get(sponsor_key)

    return self._sponsor

  @property
  def user(self):
    """Returns the user field."""
    if not self._isSet(self._user):
      self._user = user_logic.current()

      # developer may view the page as another user
      if self._user and user_logic.isDeveloper(user=self._user):
        settings = settings_logic.getUserSettings(self._user.key())
        if settings.view_as is not None:
          user = user_model.User.get(settings.view_as.to_old_key())
          if user:
            self._user = user
          else:
            # TODO(daniel): use main LINKER object when merged
            linker = links.Linker()
            user_settings_url = linker.user(
                self._user, urls.UrlNames.USER_SETTINGS)
            raise exception.BadRequest(
                message=VIEW_AS_USER_DOES_NOT_EXIST % user_settings_url)

    return self._user

  @property
  def profile(self):
    """Returns the profile property."""
    if not self._isSet(self._profile):
      if not self.user or not self.program:
        self._profile = None
      else:
        key_name = '%s/%s' % (self.program.key().name(), self.user.link_id)
        self._profile = self.models.profile_model.get_by_key_name(
            key_name, parent=self.user)
    return self._profile

  @property
  def program(self):
    """Returns the program field."""
    if not self._isSet(self._program):
      self._getProgramWideFields()
    return self._program

  @property
  def GET(self):
    """Returns the GET dictionary associated with the processed request."""
    if not self._isSet(self._GET):
      self._GET = self.request.GET
    return self._GET

  @property
  def POST(self):
    """Returns the POST dictionary associated with the processed request."""
    if not self._isSet(self._POST):
      self._POST = self.request.POST
    return self._POST

  @property
  def ds_write_disabled(self):
    """Memoizes and returns whether datastore writes are disabled."""
    if not self._isSet(self._ds_write_disabled):
      if self.request.method == 'GET':
        value = self.request.GET.get('dsw_disabled', '')

        if value.isdigit() and int(value) == 1:
          self._ds_write_disabled = True

      if not self._isSet(self._ds_write_disabled):
        self._ds_write_disabled = not db.WRITE_CAPABILITY.is_enabled()
    return self._ds_write_disabled

  @property
  def timeline(self):
    """Returns the timeline field."""
    if not self._isSet(self._timeline):
      self._timeline = TimelineHelper(self.program_timeline, None)
    return self._timeline

  @property
  def url_connection(self):
    """Returns url_connection property.

    This property represents connection entity corresponding to profile whose
    identifier is a part of the URL of the processed request. Numerical
    identifier of the connection is also a part of the URL.

    Returns:
      Retrieved connection entity.

    Raises:
      exception.BadRequest: if some data is missing in the current request.
      exception.NotFound: if no entity is found.
    """
    if not self._isSet(self._url_connection):
      try:
        connection_key = db.Key.from_path('Connection', int(self.kwargs['id']),
            parent=self._getUrlProfileKey())
      except KeyError:
        raise exception.BadRequest(
            message='The request does not contain connection id.')

      self._url_connection = connection_model.Connection.get(connection_key)
      if not self._url_connection:
        raise exception.NotFound(
            message='Requested connection does not exist.')
    return self._url_connection

  @property
  def url_profile(self):
    """Returns url_profile property.

    This property represents profile entity for a person whose identifier
    is a part of the URL of the processed request for the program whose
    identifier is also a part of the URL.

    Returns:
      Retrieved profile entity.

    Raises:
      exception.UserError: if no profile entity is found.
    """
    if not self._isSet(self._url_profile):
      self._url_profile = self.models.profile_model.get(
          self._getUrlProfileKey())
      if not self._url_profile:
        raise exception.NotFound(message='Requested profile does not exist.')
    return self._url_profile

  @property
  def url_student_info(self):
    if not self._isSet(self._url_student_info):
      self._url_student_info = self.url_profile.student_info
      if not self._url_student_info:
        raise exception.NotFound(message='Requested profile is not a student.')
    return self._url_student_info

  @property
  def url_org(self):
    """Returns url_org property.

    This property represents organization entity whose identifier is a part
    of the URL of the processed request.

    Returns:
      Retrieved organization entity.

    Raises:
      exception.BadRequest: if the current request does not contain any
        organization data.
      exception.NotFound: if the organization is not found.
    """
    if not self._isSet(self._url_org):
      try:
        fields = ['sponsor', 'program', 'organization']
        key_name = '/'.join(self.kwargs[i] for i in fields)
      except KeyError:
        raise exception.BadRequest(
            message='The request does not contain full organization data.')

      self._url_org = self.models.org_model.get_by_key_name(key_name)

      if not self._url_org:
        raise exception.NotFound(
            message='Requested organization does not exist.')
    return self._url_org

  # TODO(daniel): rename this to url_org when Organization is converted to NDB
  @property
  def url_ndb_org(self):
    """Returns url_org property.

    This property represents organization entity whose identifier is a part
    of the URL of the processed request.

    Returns:
      Retrieved organization entity.

    Raises:
      exception.BadRequest: if the current request does not contain any
        organization data.
      exception.NotFound: if the organization is not found.
    """
    if not self._isSet(self._url_ndb_org):
      try:
        fields = ['sponsor', 'program', 'organization']
        entity_id = '/'.join(self.kwargs[i] for i in fields)
      except KeyError:
        raise exception.BadRequest(
            message='The request does not contain full organization data.')

      self._url_ndb_org = self.models.ndb_org_model.get_by_id(entity_id)

      if not self._url_ndb_org:
        raise exception.NotFound(
            message='Requested organization does not exist.')
    return self._url_ndb_org

  @property
  def url_user(self):
    """Returns url_user property.

    This property represents user entity for a person whose identifier
    is a part of the URL of the processed request.

    Returns:
      Retrieved user entity.

    Raises:
      exception.BadRequest: if the current request does not contain
        any user data.
      exception.NotFound: if the user is not found.
    """
    if not self._isSet(self._url_user):
      key_name = self.kwargs.get('user')
      if not key_name:
        raise exception.BadRequest(
            message='The request does not contain user data.')

      self._url_user = user_model.User.get_by_key_name(key_name)

      if not self._url_user:
        raise exception.NotFound(message='Requested user does not exist.')
    return self._url_user

  # TODO(daniel): rename it to url_document
  @property
  def document(self):
    """Returns document property."""
    if not self._isSet(self._document):
      fields = []
      kwargs = self.kwargs.copy()

      prefix = kwargs.pop('prefix', None)
      fields.append(prefix)

      if prefix in ['gsoc_program', 'gsoc_org', 'gci_program', 'gci_org']:
        fields.append(kwargs.pop('sponsor', None))
        fields.append(kwargs.pop('program', None))

      if prefix in ['gsoc_org', 'gci_org']:
        fields.append(kwargs.pop('organization', None))

      fields.append(kwargs.pop('document', None))

      if any(kwargs.values()):
        raise exception.BadRequest(message="Unexpected value for document url")

      if not all(fields):
        raise exception.BadRequest(message="Missing value for document url")

      # TODO(daniel): remove key_name from it.
      self.key_name = '/'.join(fields)
      self._document = document_model.Document.get_by_key_name(self.key_name)
    return self._document

  def _getUrlProfileKey(self):
    """Returns db.Key that represents profile for the data specified in
    the URL of the current request.

    Returns:
      db.Key of the profile for data specified in the URL of the
      current request.

    Raises:
      exception.BadRequest: if some data is missing in the current request.
    """
    try:
      fields = ['sponsor', 'program', 'user']
      profile_key_name = '/'.join(self.kwargs[i] for i in fields)
      return db.Key.from_path(
          'User', self.kwargs['user'], self.models.profile_model.kind(),
          profile_key_name)
    except KeyError:
      raise exception.BadRequest(
          message='The request does not contain full profile data.')

  def _getProgramWideFields(self):
    """Fetches program wide fields in a single database round-trip."""
    keys = []

    # add program's key
    if self.kwargs.get('sponsor') and self.kwargs.get('program'):
      program_key_name = "%s/%s" % (
          self.kwargs['sponsor'], self.kwargs['program'])
      program_key = db.Key.from_path(
          self.models.program_model.kind(), program_key_name)
    else:
      program_key = site_model.Site.active_program.get_value_for_datastore(
          self.site)
      program_key_name = program_key.name()
    keys.append(program_key)

    # add timeline's key
    keys.append(db.Key.from_path(
        self.models.timeline_model.kind(), program_key_name))

    # add org_app's key
    org_app_key_name = '%s/%s/orgapp' % (
        self.models.program_model.prefix, program_key_name)
    keys.append(db.Key.from_path('OrgAppSurvey', org_app_key_name))

    self._program, self._program_timeline, self._org_app = db.get(keys)

    # raise an exception if no program is found
    if not self._program:
      raise exception.NotFound(
          message="There is no program for url '%s'" % program_key_name)


# TODO(nathaniel): This should be immutable.
class RedirectHelper(object):
  """Helper for constructing redirects."""

  def __init__(self, data):
    """Initializes the redirect helper."""
    self._data = data
    self._response = http.HttpResponse()
    self._clear()

  def _clear(self):
    """Clears the internal state."""
    self._no_url = False
    self._url_name = None
    self._url = None
    self.args = []
    self.kwargs = {}

  def program(self, program=None):
    """Sets kwargs for an url_patterns.PROGRAM redirect."""
    if not program:
      assert access_checker.isSet(self._data.program)
      program = self._data.program

    self._clear()

    self.kwargs['sponsor'] = program_logic.getSponsorKey(program).name()
    self.kwargs['program'] = program.link_id

  def organization(self, organization=None):
    """Sets the kwargs for an url_patterns.ORG redirect."""
    if not organization:
      assert access_checker.isSet(self._data.organization)
      organization = self._data.organization
    self.program()
    self.kwargs['organization'] = organization.link_id

  # TODO(daniel): id built-in function should not be shadowed
  def id(self, id=None):
    """Sets the kwargs for an url_patterns.ID redirect."""
    if not id:
      assert 'id' in self._data.kwargs
      id = self._data.kwargs['id']
    self.program()
    self.kwargs['id'] = id
    return self

  def key(self, key=None):
    """Sets the kwargs for an url_patterns.KEY redirect."""
    if not key:
      assert 'key' in self._data.kwargs
      key = self._data.kwargs['key']
    self.program()
    self.kwargs['key'] = key
    return self

  def createProfile(self, role):
    """Sets args for an url_patterns.CREATE_PROFILE redirect."""
    self.program()
    self.kwargs['role'] = role
    return self

  def profile(self, user=None):
    """Sets args for an url_patterns.PROFILE redirect."""
    if not user:
      assert 'user' in self._data.kwargs
      user = self._data.kwargs['user']
    self.program()
    self.kwargs['user'] = user
    return self

  def document(self, document):
    """Sets args for an url_patterns.DOCUMENT redirect.

    If document is not set, a call to url() will return None.
    """
    self._clear()
    if not document:
      self._no_url = True
      return self

    if isinstance(document, db.Model):
      key = document.key()
    else:
      key = document

    self.args = key.name().split('/')

    return self

  def userOrg(self, user=None, organization=None):
    """Sets args for an url_patterns.USER_ORG redirect."""
    if not user:
      assert 'user' in self._data.kwargs
      user = self._data.kwargs['user']

    if not organization:
      assert access_checker.isSet(self._data.organization)
      organization = self._data.organization

    self.program()
    self.kwargs['user'] = user
    self.kwargs['organization'] = organization.link_id
    return self

  # TODO(daniel): id built-in function should not be shadowed
  def userId(self, user=None, id=None):
    """Sets args for url_patterns.USER_ID redirect."""
    if not user:
      assert 'user' in self._data.kwargs
      user = self._data.kwargs['user']

    if not id:
      assert 'id' in self._data.kwargs
      id = self._data.kwargs['id']

    self.program()
    self.kwargs['user'] = user
    self.kwargs['id'] = id
    return self

  def urlOf(self, name, full=False, secure=False, extra=None):
    """Returns the resolved url for name.

    Uses internal state for args and kwargs.
    """
    # TODO(nathaniel): Why isn't this just "url = reverse(name, args=self.args,
    # kwargs=self.kwargs)"? Current suspicion: it's because there's a
    # there's a difference in behavior between passing None and passing empty
    # dicts. It's also curious that there isn't an "if self.args and
    # self.kwargs" case at the top.
    if self.args:
      url = urlresolvers.reverse(name, args=self.args)
    elif self.kwargs:
      url = urlresolvers.reverse(name, kwargs=self.kwargs)
    else:
      url = urlresolvers.reverse(name)

    url = self._appendGetArgs(url, extra_get_args=extra if extra else [])

    return self._fullUrl(url, full, secure)

  def url(self, full=False, secure=False):
    """Returns the url of the current state."""
    if self._no_url:
      return None
    assert self._url or self._url_name
    if self._url:
      return self._fullUrl(self._url, full, secure)
    return self.urlOf(self._url_name, full=full, secure=secure)

  def _fullUrl(self, url, full, secure):
    """Returns the full version of the url iff full.

    The full version starts with http:// and includes getHostname().
    """
    if (not full) and (system.isLocal() or not secure):
      return url

    # TODO(nathaniel): consider using scheme-relative urls here?
    protocol = 'https' if secure else 'http'
    hostname = site_logic.getHostname(self._data)

    return '%s://%s%s' % (protocol, hostname, url)

  # TODO(nathaniel): Django's got to have a utility function for most of this.
  def _appendGetArgs(
      self, url, validated=False, extra_get_args=None):
    """Appends GET arguments to the specified URL."""
    get_args = extra_get_args or []

    if validated:
      get_args.append('validated')

    if get_args:
      # check if the url has already a question mark
      if url.find('?') == -1:
        url = url + '?'
      else:
        url = url + '&'

      # append all the GET arguments at the end of the URL
      if get_args:
        url = url + '&'.join(get_args)

    return url

  def to(self, name=None, validated=False, full=False, secure=False,
         extra=None, anchor=None):
    """Redirects to the resolved url for name.

    Uses internal state for args and kwargs.

    Args:
      name: Name of the URL pattern
      validated: If set to True will add &validated to GET arguments
      full: Whether the URL should include the protocol
      secure: Whether the protocol of the URL should be set to HTTPS
      extra: List of additional arguments that will be added as GET arguments

    Returns:
      An http.HttpResponse object redirecting to the appropriate url.
    """
    if self._url:
      url = self._url
    else:
      assert name or self._url_name
      url = self.urlOf(name or self._url_name)

    if anchor:
      url = '%s#%s' % (url, anchor)

    url = self._appendGetArgs(
        url, validated=validated, extra_get_args=extra if extra else [])

    return self.toUrl(url, full=full, secure=secure)

  def toUrl(self, url, full=False, secure=False):
    """Redirects to the specified url.

    Args:
      url: A URL.
      full: Whether or not to prefer use of a full URL including
        protocol. This parameter is not necessarily binding.
      secure: Whether or not to prefer use of a secure URL.

    Returns:
      An http.HttpResponse object redirecting to the given url.
    """
    url = self._fullUrl(url, full, secure)
    return http.HttpResponseRedirect(url)

  def acceptedOrgs(self):
    """Sets the _url_name to the list of all accepted orgs."""
    self.program()
    return self

  def homepage(self, program=None):
    """Sets the _url_name for the homepage of the current program.

    Args:
      program: the link_id of the program for which we need to get the homepage
    """
    self.program(program)
    return self

  def searchpage(self):
    """Sets the _url_name for the searchpage of the current program."""
    self.program()
    return self

  def orgHomepage(self, link_id):
    """Sets the _url_name for the specified org homepage."""
    self.program()
    self.kwargs['organization'] = link_id
    return self

  def dashboard(self):
    """Sets the _url_name for dashboard page of the current program."""
    self.program()
    return self

  def events(self):
    """Sets the _url_name for the events page, if it is set."""
    self.program()
    return self

  def staticContent(self, content_id):
    """Sets the args for url_patterns.STATIC_CONTENT redirect."""
    self.program()
    self.kwargs['content_id'] = content_id
    return self
