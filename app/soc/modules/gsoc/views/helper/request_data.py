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


import logging

from google.appengine.ext import db

from soc.logic.exceptions import NotFound
from soc.views.helper.access_checker import isSet
from soc.views.helper import request_data

from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.models import program as program_model
from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.views.helper import url_names


class TimelineHelper(request_data.TimelineHelper):
  """Helper class for the determination of the currently active period.

  Methods ending with "On", "Start", or "End" return a date.
  Methods ending with "Between" return a tuple with two dates.
  Methods ending with neither return a Boolean.
  """

  def currentPeriod(self):
    """Return where we are currently on the timeline.
    """
    if not self.programActive():
      return 'offseason'

    if self.beforeOrgSignupStart():
      return 'kickoff_period'

    if self.orgSignup():
      return 'org_signup_period'

    if self.studentSignup():
      return 'student_signup_period'

    if self.studentsAnnounced():
      return 'coding_period'

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

    if request_data.isBetween(self.orgSignupEnd(), self.orgsAnnouncedOn()):
      return ("Accepted Orgs Announced In", self.orgsAnnouncedOn())

    if self.orgsAnnounced() and self.beforeStudentSignupStart():
      return ("Student Application Opens", self.studentSignupStart())

    if self.studentSignup():
      return ("Student Application Deadline", self.studentSignupEnd())

    if request_data.isBetween(self.studentSignupEnd(),
                              self.applicationMatchedOn()):
      return ("Proposal Matched Deadline", self.applicationMatchedOn())

    if request_data.isBetween(self.applicationMatchedOn(),
                              self.applicationReviewEndOn()):
      return ("Proposal Scoring Deadline", self.applicationReviewEndOn())

    if request_data.isBetween(self.applicationReviewEndOn(),
                              self.studentsAnnouncedOn()):
      return ("Accepted Students Announced", self.studentsAnnouncedOn())

    return ('', None)

  def studentsAnnouncedOn(self):
    return self.timeline.accepted_students_announced_deadline

  def studentsAnnounced(self):
    return request_data.isAfter(self.studentsAnnouncedOn())

  def beforeStudentsAnnounced(self):
    return request_data.isBefore(self.studentsAnnouncedOn())

  def applicationReviewEndOn(self):
    return self.timeline.application_review_deadline

  def applicationMatchedOn(self):
    return self.timeline.student_application_matched_deadline

  def mentorSignup(self):
    return self.programActive() and self.orgsAnnounced()

  def afterFirstSurveyStart(self, surveys):
    """Returns True if we are past at least one survey has start date.

    Args:
      surveys: List of survey entities for which we need to determine if
        at least one of them have started
    """
    first_survey_start = min([s.survey_start for s in surveys])
    return request_data.isAfter(first_survey_start)


class RequestData(request_data.RequestData):
  """Object containing data we query for each request in the GSoC module.

  The only view that will be exempt is the one that creates the program.

  Fields:
    site: The Site entity
    user: The user entity (if logged in)
    css_path: a part of the css to fetch the GSoC specific CSS resources
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
    organization: the GSoCOrganization for the current url

  Raises:
    out_of_band: 404 when the program does not exist
  """

  def __init__(self):
    """Constructs an empty RequestData object.
    """
    super(RequestData, self).__init__()

    # program wide fields
    self._program = self._unset
    self._program_timeline = self._unset
    self._programs = self._unset
    self._org_app = self._unset
    self._timeline = self._unset

    # user profile specific fields
    self._profile = self._unset
    self._is_host = self._unset
    self._is_mentor = self._unset
    self._is_student = self._unset
    self._is_org_admin = self._unset
    self._org_map = self._unset
    self._mentor_for = self._unset
    self._org_admin_for = self._unset
    self._student_info = self._unset
    self.organization = None

  @property
  def css_path(self):
    """Returns the css_path property."""
    if not self._isSet(self._css_path):
      self._css_path = 'gsoc'
    return self._css_path

  @property
  def is_host(self):
    """Returns the is_host field."""
    if not self._isSet(self._is_host):
      if not self.user:
        self._is_host = False
      else:
        key = program_model.GSoCProgram.scope.get_value_for_datastore(
            self.program)
        self._is_host = key in self.user.host_for
    return self._is_host

  @property
  def is_mentor(self):
    """Returns the is_mentor field."""
    if not self._isSet(self._is_mentor):
      if not self.profile:
        self._is_mentor = False
      else:
        self._is_mentor = bool(self.profile.mentor_for) or self.is_org_admin
    return self._is_mentor

  @property
  def is_org_admin(self):
    """Returns the is_org_admin field."""
    if not self._isSet(self._is_org_admin):
      if not self.profile:
        self._is_org_admin = False
      else:
        self._is_org_admin = bool(self.profile.org_admin_for) or self.is_host
    return self._is_org_admin

  @property
  def is_student(self):
    """Returns the is_student field."""
    if not self._isSet(self._is_student):
      if not self.profile:
        self._is_student = False
      else:
        self._is_student = bool(profile_model.GSoCProfile.student_info \
            .get_value_for_datastore(self.profile))
    return self._is_student

  @property
  def mentor_for(self):
    """Returns the mentor_for field."""
    if not self._isSet(self._mentor_for):
      if self.profile:
        self._initOrgMap()
        self._mentor_for = self._org_map.values()
      else:
        self._mentor_for = []
    return self._mentor_for

  @property
  def org_admin_for(self):
    """Returns the org_admin_for field."""
    if not self._isSet(self._org_admin_for):
      if self.profile:
        self._initOrgMap()
        self._org_admin_for = [
            self._org_map[i] for i in self.profile.org_admin_for]
      else:
        self._org_admin_for = []
    return self._org_admin_for

  @property
  def org_app(self):
    """Returns the org_app field."""
    if not self._isSet(self._org_app):
      self._getProgramWideFields()
    return self._org_app

  @property
  def program(self):
    """Returns the program field."""
    if not self._isSet(self._program):
      self._getProgramWideFields()
    return self._program

  @property
  def program_timeline(self):
    """Returns the program_timeline field."""
    if not self._isSet(self._program_timeline):
      self._getProgramWideFields()
    return self._program_timeline

  @property
  def programs(self):
    """Memorizes and returns a list of all programs."""
    if not self._isSet(self._programs):
      self._programs = list(program_model.GSoCProgram.all())
    return self._programs

  @property
  def student_info(self):
    """Returns the student_info field."""
    if not self._isSet(self._student_info):
      if not self.is_student:
        self._student_info = None
      else:
        student_info_key = profile_model.GSoCProfile.student_info \
            .get_value_for_datastore(self.profile)
        self._student_info = db.get(student_info_key)
    return self._student_info

  @property
  def profile(self):
    """Returns the profile property."""
    if not self._isSet(self._profile):
      if not self.user or not self.program:
        self._profile = None
      else:
        key_name = '%s/%s' % (self.program.key().name(), self.user.link_id)
        self._profile = profile_model.GSoCProfile.get_by_key_name(
            key_name, parent=self.user)
      pass
    return self._profile

  @property
  def timeline(self):
    """Returns the timeline field."""
    if not self._isSet(self._timeline):
      self._timeline = TimelineHelper(self.program_timeline, self.org_app)
    return self._timeline

  def _initOrgMap(self):
    """Initializes _org_map by inserting there all organizations for which
    the current user is either a mentor or org admin.
    """
    if not self._isSet(self._org_map):
      if self.profile:
        orgs = db.get(
            set(self.profile.mentor_for + self.profile.org_admin_for))
        self._org_map = dict((i.key(), i) for i in orgs)
      else:
        self._org_map = {}

  def _getProgramWideFields(self):
    """Fetches program wide fields in a single database round-trip."""
    keys = []

    # add program's key
    if self.kwargs.get('sponsor') and self.kwargs.get('program'):
      program_key_name = "%s/%s" % (
          self.kwargs['sponsor'], self.kwargs['program'])
      program_key = db.Key.from_path('GSoCProgram', program_key_name)
    else:
      program_key = Site.active_program.get_value_for_datastore(self.site)
      program_key_name = program_key.name()
    keys.append(program_key)

    # add timeline's key
    keys.append(db.Key.from_path('GSoCTimeline', program_key_name))

    # add org_app's key
    org_app_key_name = 'gsoc_program/%s/orgapp' % program_key_name
    keys.append(db.Key.from_path('OrgAppSurvey', org_app_key_name))

    self._program, self._program_timeline, self._org_app = db.get(keys)

    # raise an exception if no program is found
    if not self._program:
      raise NotFound("There is no program for url '%s'" % program_key_name)

  def getOrganization(self, org_key):
    """Retrieves the specified organization.
    """
    self._initOrgMap()
    if org_key not in self._org_map:
      org = db.get(org_key)
      self._org_map[org_key] = org

    return self._org_map[org_key]

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

    from soc.modules.gsoc.models.request import GSoCRequest
    query = GSoCRequest.all()
    query.filter('user', self.user)
    query.filter('org', organization)

    return query

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

    if kwargs.get('organization'):
      fields = [self.program.key().id_or_name(), kwargs.get('organization')]
      org_key_name = '/'.join(fields)
      self.organization = GSoCOrganization.get_by_key_name(org_key_name)
      if not self.organization:
        raise NotFound("There is no organization for url '%s'" % org_key_name)


class RedirectHelper(request_data.RedirectHelper):
  """Helper for constructing redirects.
  """

  def review(self, id=None, student=None):
    """Sets the kwargs for an url_patterns.REVIEW redirect.
    """
    if not student:
      assert 'user' in self._data.kwargs
      student = self._data.kwargs['user']
    self.id(id)
    self.kwargs['user'] = student
    return self

  # (dcrodman) This method will become obsolete when the connection module
  # is commited to the main branch.
  def invite(self, role=None):
    """Sets args for an url_patterns.INVITE redirect.
    """
    if not role:
      assert 'role' in self._data.kwargs
      role = self._data.kwargs['role']
    self.organization()
    self.kwargs['role'] = role
    return self

  def orgAppTake(self):
    """Sets kwargs for an url_patterns.SURVEY redirect for org application.
    """
    self.program()
    return self

  def orgAppReTake(self, survey=None):
    """Sets kwargs for an url_patterns.SURVEY redirect for org application.
    """
    if not survey:
      assert 'id' in self._data.kwargs
      survey = self._data.kwargs['id']
    return self.id(survey)

  def document(self, document):
    """Override this method to set GSoC specific _url_name.
    """
    super(RedirectHelper, self).document(document)
    self._url_name = 'show_gsoc_document'
    return self
 
  def acceptedOrgs(self):
    """Sets the _url_name to the list all the accepted orgs.
    """
    super(RedirectHelper, self).acceptedOrgs()
    self._url_name = 'gsoc_accepted_orgs'
    return self

  def allProjects(self):
    """Sets the _url_name to list all GSoC projects.
    """
    self.program()
    self._url_name = 'gsoc_accepted_projects'
    return self

  def homepage(self, program=None):
    """Sets the _url_name for the homepage of the current GSOC program.

    Args:
      program: the link_id of the program for which we need to get the homepage
    """
    super(RedirectHelper, self).homepage(program)
    self._url_name = 'gsoc_homepage'
    return self

  def searchpage(self):
    """Sets the _url_name for the searchpage of the current GSOC program.
    """
    super(RedirectHelper, self).searchpage()
    self._url_name = 'search_gsoc'
    return self

  def orgHomepage(self, link_id):
    """Sets the _url_name for the specified org homepage
    """
    super(RedirectHelper, self).orgHomepage(link_id)
    self._url_name = 'gsoc_org_home'
    return self

  def dashboard(self):
    """Sets the _url_name for dashboard page of the current GSOC program.
    """
    super(RedirectHelper, self).dashboard()
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

    self.program()
    self._url_name = 'gsoc_events'
    return self

  # (dcrodman) This method will become obsolete when the connection module
  # is commited to the main branch.
  def request(self, request):
    """Sets the _url_name for a request.
    """
    assert request
    self.id(request.key().id())
    self.kwargs['user'] = request.parent_key().name()
    if request.type == 'Request':
      self._url_name = 'show_gsoc_request'
    else:
      self._url_name = 'gsoc_invitation'
    self._url_name = 'show_gsoc_request'
    return self
  
  def connect(self, user=None):
    """ Sets the _url_name for a gsoc_user_connection redirect.
     """  
    if not user:
      assert 'user' in self._data.kwargs
      user = self._data.kwargs['user']
    
    self.organization(self._data.organization)
    self.kwargs['link_id'] = user.link_id
    # We need to reassign the kwarg to the org's link_id since it's 
    # being set to the Organization object
    self.kwargs['organization'] = self._data.organization.link_id
    self._url_name = url_names.GSOC_USER_CONNECTION
    return self
  
  def show_connection(self, user, org):
    """ Sets up kwargs for a gsoc_show_connection redirect.
    Args:
      user: the user involved in the connection 
      org: the org involved in the connection
    """
    self._data.organization = org
    self.connect(user)
    self._url_name = url_names.GSOC_SHOW_CONNECTION
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

  def survey(self, survey=None):
    """Sets kwargs for an url_patterns.SURVEY redirect.

    Args:
      survey: the survey's link_id
    """
    self.program()

    if not survey:
      assert 'survey' in self._data.kwargs
      survey = self._data.kwargs['survey']
    self.kwargs['survey'] = survey

    return self

  def survey_record(self, survey=None, id=None, student=None):
    """Returns the redirector object with the arguments for survey record

    Args:
      survey: the survey's link_id
    """
    self.program()
    self.project(id, student)
    if not survey:
      assert 'survey' in self._data.kwargs
      survey = self._data.kwargs['survey']
    self.kwargs['survey'] = survey

    return self

  def grading_record(self, record):
    """Returns the redirector object with the arguments for grading record

    Args:
      record: the grading record entity
    """
    self.program()

    project = record.parent()
    self.project(project.key().id(), project.parent().link_id)

    self.kwargs['group'] = record.grading_survey_group.key().id_or_name()
    self.kwargs['record'] = record.key().id()

    return self

  def editProfile(self):
    """Returns the URL for the edit profile page.
    """
    self.program()
    self._url_name = 'edit_gsoc_profile'

    return self
