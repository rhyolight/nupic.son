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

import datetime
import httplib

from google.appengine.api import users
from google.appengine.ext import db

from django import http
from django.core import urlresolvers
from django.utils import encoding

from soc.logic import program as program_logic
from soc.logic import system
from soc.logic import site as site_logic
from soc.logic import user
from soc.models import sponsor as sponsor_model
from soc.views.helper import access_checker


def isBefore(date):
  """Returns True iff date is before utcnow().

  Returns False if date is not set.
  """
  return date and datetime.datetime.utcnow() < date


def isAfter(date):
  """Returns True iff date is after utcnow().

  Returns False if date is not set.
  """
  return date and date < datetime.datetime.utcnow()


def isBetween(start, end):
  """Returns True iff utcnow() is between start and end."""
  return isAfter(start) and isBefore(end)


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
    return isBefore(self.timeline.program_start)

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

  def studentSignupEnd(self):
    return self.timeline.student_signup_end

  def stopAllWorkDeadline(self):
    return self.timeline.stop_all_work_deadline

  def studentsSignupBetween(self):
    return (self.timeline.student_signup_start,
            self.timeline.student_signup_end)

  def programActive(self):
    start, end = self.programActiveBetween()
    return isBetween(start, end)

  def beforeOrgSignupStart(self):
    return self.org_app and isBefore(self.orgSignupStart())

  def afterOrgSignupStart(self):
    return self.org_app and isAfter(self.orgSignupStart())

  def orgSignup(self):
    if not self.org_app:
      return False
    start, end = self.orgSignupBetween()
    return isBetween(start, end)

  def orgsAnnounced(self):
    return isAfter(self.orgsAnnouncedOn())

  def beforeStudentSignupStart(self):
    return isBefore(self.studentSignupStart())

  def afterStudentSignupStart(self):
    return isAfter(self.studentSignupStart())

  def studentSignup(self):
    start, end = self.studentsSignupBetween()
    return isBetween(start, end)

  def afterStudentSignupEnd(self):
    return isAfter(self.studentSignupEnd())

  def afterStopAllWorkDeadline(self):
    return isAfter(self.stopAllWorkDeadline())

  def surveyPeriod(self, survey):
    start = survey.survey_start
    end = survey.survey_end
    return isAfter(start) and isBefore(end)

  def afterSurveyStart(self, survey):
    return isAfter(survey.survey_start)

  def afterSurveyEnd(self, survey):
    return isAfter(survey.survey_end)


class RequestData(object):
  """Object containing data we query for each request.

  Fields:
    site: the singleton site.Site entity
    user: the user entity (if logged in)
    request: the request object (as provided by django)
    args: the request args (as provided by djang)
    kwargs: the request kwargs (as provided by django)
    path: the url of the current query, encoded as utf-8 string
    full_path: same as path, but including any GET args
    login_url: login url that redirects to the current path
    logout_url: logout url that redirects to the current path
    GET: the GET dictionary (from the request object)
    POST: the POST dictionary (from the request object)
    is_developer: is the current user a developer
    gae_user: the Google Appengine user object
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

    self._redirect = self._unset
    self._site = self._unset
    self._sponsor = self._unset
    self._user = self._unset
    self._GET = self._unset
    self._POST = self._unset
    # TODO(daniel): check if this field is really used
    self._path = self._unset
    self._is_developer = self._unset
    self._gae_user = self._unset
    self._css_path = self._unset
    self._login_url = self._unset
    self._logout_url = self._unset
    self._ds_write_disabled = self._unset

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
    if not self._isSet(self._css_path):
      # TODO(daniel): this should not return gsoc in module
      # I believe css_path is needed in the main module because of a few sites
      # that are not specific to any module, like site or host
      self._css_path = 'gsoc'
    return self._css_path

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
      self._user = user.current()
    return self._user

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
  def login_url(self):
    """Memoizes and returns the login_url for the current path."""
    if not self._isSet(self._login_url):
      self._login_url = users.create_login_url(
          self.request.get_full_path().encode('utf-8'))
    return self._login_url

  @property
  def logout_url(self):
    """Memoizes and returns the logout_url for the current path."""
    if not self._isSet(self._logout_url):
      self._logout_url = users.create_logout_url(
          self.request.get_full_path().encode('utf-8'))
    return self._logout_url

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

  def appliedTo(self, organization):
    """Returns true iff the user has applied for the specified organization.

    Organization may either be a key or an organization instance.
    """
    query = self._requestQuery(organization)
    query.filter('type', 'Request')
    return bool(query.get())

  def invitedTo(self, organization):
    """Returns the role the user has been invited to,.

    Organization may either be a key or an organization instance.
    Returns None if no invite was sent.
    """
    query = self._requestQuery(organization)
    query.filter('type', 'Invitation')
    invite = query.get()
    return invite.role if invite else None


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

  def sponsor(self, program=None):
    """Sets kwargs for an url_patterns.SPONSOR redirect."""
    if not program:
      assert access_checker.isSet(self._data.program)
      program = self._data.program
    self._clear()
    self.kwargs['sponsor'] = program_logic.getSponsorKey(program).name()

  def program(self, program=None):
    """Sets kwargs for an url_patterns.PROGRAM redirect."""
    if not program:
      assert access_checker.isSet(self._data.program)
      program = self._data.program
    self.sponsor(program)
    self.kwargs['program'] = program.link_id

  def organization(self, organization=None):
    """Sets the kwargs for an url_patterns.ORG redirect."""
    if not organization:
      assert access_checker.isSet(self._data.organization)
      organization = self._data.organization
    self.program()
    self.kwargs['organization'] = organization.link_id

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

  def urlOf(self, name, full=False, secure=False, extra=[]):
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

    url = self._appendGetArgs(url, extra_get_args=extra)

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
    if secure:
      protocol = 'https'
      hostname = system.getSecureHostname()
    else:
      protocol = 'http'
      hostname = system.getHostname(self._data)

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
      extra=[], anchor=None):
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

    url = self._appendGetArgs(url, validated=validated,
        extra_get_args=extra)

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

  def login(self):
    """Sets the _url to the login url."""
    self._clear()
    self._url = self._data.login_url
    return self

  def logout(self):
    """Sets the _url to the logout url."""
    self._clear()
    self._url = self._data.logout_url
    return self

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
