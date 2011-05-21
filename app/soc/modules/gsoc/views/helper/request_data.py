#!/usr/bin/env python2.5
#
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

"""Module containing the RequestData object that will be created for each
request in the GSoC module.
"""

__authors__ = [
  '"Daniel Hans" <daniel.m.hans@gmail.com>',
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
]


import datetime

from google.appengine.api import users
from google.appengine.ext import db

from django.core.urlresolvers import reverse

from soc.models import role
from soc.models.org_app_survey import OrgAppSurvey
from soc.logic import system
from soc.logic.exceptions import NotFound
from soc.logic.models.host import logic as host_logic
from soc.logic.models.site import logic as site_logic
from soc.logic.models.user import logic as user_logic
from soc.views.helper.access_checker import isSet
from soc.views.helper.request_data import RequestData

from soc.modules.gsoc.models.profile import GSoCProfile

from soc.modules.gsoc.logic.models.mentor import logic as mentor_logic
from soc.modules.gsoc.logic.models.organization import logic as org_logic
from soc.modules.gsoc.logic.models.org_admin import logic as org_admin_logic
from soc.modules.gsoc.logic.models.program import logic as program_logic
from soc.modules.gsoc.logic.models.student import logic as student_logic


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
  """Returns True iff utcnow() is between start and end.
  """
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
    """Return where we are currently on the timeline.
    """
    if not self.programActive():
      return 'offseason'

    if self.beforeOrgSignupStart():
      return 'kickoff_period'

    if self.studentsAnnounced():
      return 'coding_period'

    if self.afterStudentSignupStart():
      return 'student_signup_period'

    if self.afterOrgSignupStart():
      return 'org_signup_period'

    return 'offseason'

  def nextDeadline(self):
    """Determines the next deadline on the timeline.

    Returns:
      A two-tuple containing deadline text and the datetime object for
      the next deadline
    """
    if self.beforeOrgSignupStart():
      return ("Org Application Starts", self.orgSignupStart())

    # we do not have deadlines for any of those programs that are not active
    if not self.programActive():
      return ("", None)

    if self.orgSignup():
      return ("Org Application Deadline", self.orgSignupEnd())

    if isBetween(self.orgSignupEnd(), self.orgsAnnouncedOn()):
      return ("Accepted Orgs Announced In", self.orgsAnnouncedOn())

    if self.orgsAnnounced() and self.beforeStudentSignupStart():
      return ("Student Application Opens", self.studentSignupStart())

    if self.studentSignup():
      return ("Student Application Deadline", self.studentSignupEnd())

    if isBetween(self.studentSignupEnd(), self.applicationMatchedOn()):
      return ("Proposal Matched Deadline", self.applicationMatchedOn())

    if isBetween(self.applicationMatchedOn(), self.applicationReviewEndOn()):
      return ("Proposal Scoring Deadline", self.applicationReviewEndOn())

    if isBetween(self.applicationReviewEndOn(), self.studentsAnnouncedOn()):
      return ("Accepted Students Announced", self.studentsAnnouncedOn())

    return ('', None)

  def orgsAnnouncedOn(self):
    return self.timeline.accepted_organization_announced_deadline

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

  def studentsSignupBetween(self):
    return (self.timeline.student_signup_start,
            self.timeline.student_signup_end)

  def studentsAnnouncedOn(self):
    return self.timeline.accepted_students_announced_deadline

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

  def studentsAnnounced(self):
    return isAfter(self.studentsAnnouncedOn())

  def mentorSignup(self):
    return self.programActiveBetween() and self.orgsAnnounced()

  def beforeStudentsAnnounced(self):
    return isBefore(self.studentsAnnouncedOn())

  def applicationReviewEndOn(self):
    return self.timeline.application_review_deadline

  def applicationMatchedOn(self):
    return self.timeline.student_application_matched_deadline


class RequestData(RequestData):
  """Object containing data we query for each request in the GSoC module.

  The only view that will be exempt is the one that creates the program.

  Fields:
    site: The Site entity
    user: The user entity (if logged in)
    program: The GSoC program entity that the request is pointing to
    programs: All GSoC programs.
    program_timeline: The GSoCTimeline entity
    timeline: A TimelineHelper entity
    is_host: is the current user a host of the program
    is_mentor: is the current user a mentor in the program
    is_student: is the current user a student in the program
    is_org_admin: is the current user an org admin in the program
    org_map: map of retrieved organizations
    org_admin_for: the organizations the current user is an admin for
    mentor_for: the organizations the current user is a mentor for
    student_info: the StudentInfo for the current user and program

  Raises:
    out_of_band: 404 when the program does not exist
  """

  def __init__(self):
    """Constructs an empty RequestData object.
    """
    super(RequestData, self).__init__()
    # program wide fields
    self._programs = None
    self.program = None
    self.program_timeline = None
    self.org_app = None

    # user profile specific fields
    self.profile = None
    self.is_host = False
    self.is_mentor = False
    self.is_student = False
    self.is_org_admin = False
    self.org_map = {}
    self.mentor_for = []
    self.org_admin_for = []
    self.student_info = None

  @property
  def programs(self):
    """Memoizes and returns a list of all programs.
    """
    from soc.modules.gsoc.models.program import GSoCProgram
    if not self._programs:
      self._programs = list(GSoCProgram.all())

    return self._programs

  def getOrganization(self, org_key):
    """Retrieves the specified organization.
    """
    if org_key not in self.org_map:
      org = db.get(org_key)
      self.org_map[org_key] = org

    return self.org_map[org_key]

  def orgAdminFor(self, organization):
    """Returns true iff the user is admin for the specified organization.

    Organization may either be a key or an organization instance.
    """
    if self.is_host:
      return True
    if isinstance(organization, db.Model):
      organization = organization.key()
    return organization in [i.key() for i in self.org_admin_for]

  def mentorFor(self, organization):
    """Returns true iff the user is mentor for the specified organization.

    Organization may either be a key or an organization instance.
    """
    if self.is_host:
      return True
    if isinstance(organization, db.Model):
      organization = organization.key()
    return organization in [i.key() for i in self.mentor_for]

  def _requestQuery(self, organization):
    """Returns a query to retrieve a Request for this user.
    """
    if isinstance(organization, db.Model):
      organization = organization.key()

    from soc.models.request import Request
    query = Request.all()
    query.filter('user', self.user)
    query.filter('group', organization)

    return query

  def appliedTo(self, organization):
    """Returns true iff the user has applied for the specified organization.

    Organization may either be a key or an organization instance.
    """
    query = self._requestQuery(organization)
    query.filter('type', 'Request')
    return bool(query.get())

  def invitedTo(self, organization):
    """Returns the role the user has bene invoted to,.

    Organization may either be a key or an organization instance.
    Returns None if no invite was sent.
    """
    query = self._requestQuery(organization)
    query.filter('type', 'Invitation')
    invite = query.get()
    return invite.role if invite else None

  def isPossibleMentorForProposal(self, mentor_profile=None):
    """Checks if the user is a possible mentor for the proposal in the data.
    """
    assert isSet(self.profile)
    assert isSet(self.proposal)

    profile = mentor_profile if mentor_profile else self.profile

    return profile.key() in self.proposal.possible_mentors

  def populate(self, redirect, request, args, kwargs):
    """Populates the fields in the RequestData object.

    Args:
      request: Django HTTPRequest object.
      args & kwargs: The args and kwargs django sends along.
    """
    super(RequestData, self).populate(redirect, request, args, kwargs)

    if kwargs.get('sponsor') and kwargs.get('program'):
      program_key_name = "%s/%s" % (kwargs['sponsor'], kwargs['program'])
      program_key = db.Key.from_path('GSoCProgram', program_key_name)
    else:
      from soc.models.site import Site
      program_key = Site.active_program.get_value_for_datastore(self.site)
      program_key_name = program_key.name()

    timeline_key = db.Key.from_path('GSoCTimeline', program_key_name)

    org_app_key_name = 'gsoc_program/%s/orgapp' % program_key_name
    org_app_key = db.Key.from_path('OrgAppSurvey', org_app_key_name)

    keys = [program_key, timeline_key, org_app_key]

    self.program, self.program_timeline, self.org_app = db.get(keys)

    if not self.program:
      raise NotFound("There is no program for url '%s'" % program_key_name)

    self.timeline = TimelineHelper(self.program_timeline, self.org_app)

    if kwargs.get('organization'):
      org_keyfields = {
          'link_id': kwargs.get('organization'),
          'scope_path': self.program.key().id_or_name(),
          }
      self.organization = org_logic.getFromKeyFieldsOr404(org_keyfields)

    if self.user:
      key_name = '%s/%s' % (self.program.key().name(), self.user.link_id)
      self.profile = GSoCProfile.get_by_key_name(
          key_name, parent=self.user)

      from soc.modules.gsoc.models.program import GSoCProgram
      host_key = GSoCProgram.scope.get_value_for_datastore(self.program)
      self.is_host = host_key in self.user.host_for

    if self.profile:
      org_keys = set(self.profile.mentor_for + self.profile.org_admin_for)

      prop = GSoCProfile.student_info
      student_info_key = prop.get_value_for_datastore(self.profile)

      if student_info_key:
        self.student_info = db.get(student_info_key)
        self.is_student = True
      else:
        orgs = db.get(org_keys)

        org_map = self.org_map = dict((i.key(), i) for i in orgs)

        self.mentor_for = org_map.values()
        self.org_admin_for = [org_map[i] for i in self.profile.org_admin_for]

    self.is_org_admin = self.is_host or bool(self.org_admin_for)
    self.is_mentor = self.is_org_admin or bool(self.mentor_for)


class RedirectHelper(object):
  """Helper for constructing redirects.
  """

  def __init__(self, data, response):
    """Initializes the redirect helper.
    """
    self._data = data
    self._response = response
    self._clear()

  def _clear(self):
    """Clears the internal state.
    """
    self._no_url = False
    self._url_name = None
    self._url = None
    self.args = []
    self.kwargs = {}

  def sponsor(self, program=None):
    """Sets kwargs for an url_patterns.SPONSOR redirect.
    """
    if not program:
      assert self._data.program
      program = self._data.program
    self._clear()
    self.kwargs['sponsor'] = program.scope_path
    return self

  def program(self, program=None):
    """Sets kwargs for an url_patterns.PROGRAM redirect.
    """
    if not program:
      assert self._data.program
      program = self._data.program
    self.sponsor(program)
    self.kwargs['program'] = program.link_id
    return self

  def organization(self, organization=None):
    """Sets the kwargs for an url_patterns.ORG redirect.
    """
    if not organization:
      assert isSet(self._data.organization)
      organization = self._data.organization
    self.program()
    self.kwargs['organization'] = organization.link_id
    return self

  def id(self, id=None):
    """Sets the kwargs for an url_patterns.ID redirect.
    """
    if not id:
      assert 'id' in self._data.kwargs
      id = self._data.kwargs['id']
    self.program()
    self.kwargs['id'] = id
    return self

  def key(self, key=None):
    """Sets the kwargs for an url_patterns.KEY redirect.
    """
    if not key:
      assert 'key' in self._data.kwargs
      key = self._data.kwargs['key']
    self.program()
    self.kwargs['key'] = key
    return self

  def review(self, id=None, student=None):
    """Sets the kwargs for an url_patterns.REVIEW redirect.
    """
    if not student:
      assert 'user' in self._data.kwargs
      student = self._data.kwargs['user']
    self.id(id)
    self.kwargs['user'] = student
    return self

  def createProfile(self, role):
    """Sets args for an url_patterns.CREATE_PROFILE redirect.
    """
    self.program()
    self.kwargs['role'] = role
    return self

  def profile(self, user=None):
    """Sets args for an url_patterns.PROFILE redirect.
    """
    if not user:
      assert 'user' in self._data.kwargs
      user = self._data.kwargs['user']
    self.program()
    self.kwargs['user'] = user
    return self

  def invite(self, role=None):
    """Sets args for an url_patterns.INVITE redirect.
    """
    if not role:
      assert 'role' in self._data.kwargs
      role = self._data.kwargs['role']
    self.organization()
    self.kwargs['role'] = role
    return self

  def survey(self, survey=None):
    """Sets kwargs for an url_patterns.SURVEY redirect.
    """
    if not survey:
      assert 'survey' in self._data.kwargs
      survey = self._data.kwargs['survey']
    self.organization()
    self.kwargs['survey'] = survey

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

    prefix, rest = key.name().split('/', 1)
    scope_path, link_id = rest.rsplit('/', 1)

    self.args = [prefix, scope_path + '/', link_id]
    self._url_name = 'show_gsoc_document'
    return self

  def urlOf(self, name, full=False, secure=False):
    """Returns the resolved url for name.

    Uses internal state for args and kwargs.
    """
    if self.args:
      url = reverse(name, args=self.args)
    elif self.kwargs:
      url = reverse(name, kwargs=self.kwargs)
    else:
      url = reverse(name)

    return self._fullUrl(url, full, secure)

  def url(self, full=False, secure=False):
    """Returns the url of the current state.
    """
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

    if secure:
      protocol = 'https'
      hostname = system.getSecureHostname()
    else:
      protocol = 'http'
      hostname = system.getHostname(self._data)

    return '%s://%s%s' % (protocol, hostname, url)

  def to(self, name=None, validated=False, full=False, secure=False):
    """Redirects to the resolved url for name.

    Uses internal state for args and kwargs.
    """
    if self._url:
      url = self._url
    else:
      assert name or self._url_name
      url = self.urlOf(name or self._url_name)

    if validated:
      url = url + '?validated'

    self.toUrl(url, full=full, secure=secure)

  def toUrl(self, url, full=False, secure=False):
    """Redirects to the specified url.
    """
    from django.utils.encoding import iri_to_uri
    url = self._fullUrl(url, full, secure)
    self._response.status_code = 302
    self._response["Location"] = iri_to_uri(url)

  def login(self):
    """Sets the _url to the login url.
    """
    self._clear()
    self._url = self._data.login_url
    return self

  def logout(self):
    """Sets the _url to the logout url.
    """
    self._clear()
    self._url = self._data.logout_url
    return self

  def acceptedOrgs(self):
    """Sets the _url_name to the list all GSoC projects.
    """
    self.program()
    self._url_name = 'gsoc_accepted_orgs'
    return self

  def allProjects(self):
    """Sets the _url_name to list all GSoC projects.
    """
    self.program()
    self._url_name = 'gsoc_accepted_projects'
    return self

  def homepage(self):
    """Sets the _url_name for the homepage of the current GSOC program.
    """
    self.program()
    self._url_name = 'gsoc_homepage'
    return self

  def searchpage(self):
    """Sets the _url_name for the searchpage of the current GSOC program.
    """
    self._clear()
    self._url_name = 'search_gsoc'
    return self

  def orgHomepage(self, link_id):
    """Sets the _url_name for the specified org homepage
    """
    self.program()
    self.kwargs['organization'] = link_id
    self._url_name = 'gsoc_org_home'
    return self

  def dashboard(self):
    """Sets the _url_name for dashboard page of the current GSOC program.
    """
    self.program()
    self._url_name = 'gsoc_dashboard'
    return self

  def events(self):
    """Sets the _url_name for the events page, if it is set.
    """
    from soc.modules.gsoc.models.program import GSoCProgram
    key = GSoCProgram.events_page.get_value_for_datastore(self._data.program)

    if not key:
      self._clear()
      self._no_url = True
      return self

    self.program()
    self._url_name = 'gsoc_events'
    return self

  def request(self, request):
    """Sets the _url_name for a request.
    """
    assert request
    self.id(request.key().id())
    if request.type == 'Request':
      self._url_name = 'show_gsoc_request'
    else:
      self._url_name = 'gsoc_invitation'
    return self

  def comment(self, comment, full=False, secure=False):
    """Creates a direct link to a comment.
    """
    review = comment.parent()
    self.review(review.key().id_or_name(), review.parent().link_id)
    url = self.urlOf('review_gsoc_proposal', full=full, secure=secure)
    return "%s#c%s" % (url, comment.key().id())

  def project(self, id=None, student=None):
    """Returns the URL to the Student Project.

    Args:
      student: entity which represents the user for the student
    """
    if not student:
      assert 'user' in self._data.kwargs
      student = self._data.kwargs['user']
    self.id(id)
    self.kwargs['user'] = student
    return self
