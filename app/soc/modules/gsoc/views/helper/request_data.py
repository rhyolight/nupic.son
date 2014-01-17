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


from google.appengine.ext import db
from google.appengine.ext import ndb

from melange.logic import user as user_logic
from melange.models import connection as connection_model
from melange.models import organization as melange_org_model
# TODO(nathaniel): I'm not sure how I feel about the exception module
# being important here, but that just goes hand-in-hand with my skepticism
# about the RequestData object raising exceptions generally.
from melange.request import exception
from melange.utils import time

from soc.views.helper.access_checker import isSet
from soc.views.helper import request_data

from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import program as program_model
from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.views.helper import url_names

from summerofcode import types


class TimelineHelper(request_data.TimelineHelper):
  """Helper class for the determination of the currently active period.

  Methods ending with "On", "Start", or "End" return a date.
  Methods ending with "Between" return a tuple with two dates.
  Methods ending with neither return a Boolean.
  """

  def currentPeriod(self):
    """Returns where we are currently on the timeline.

    Here is detailed description and definitions of how the resulting string
    is generated based on the current date and program timeline:

    - 'offseason' is returned before the program start date and after
      program end date
    - 'kickoff_period' is returned after the program start date and before
      organization application start date
    - 'org_signup_period' is returned after organization application start
      date and before student sign-up start date
    - 'student_signup_period' is returned after student sign-up start date
      and before students announced date
    - 'coding_period' is returned after students announced date and before
      program end date

    Returns:
      name of the current period on the timeline as described in this method's
      documentation
    """
    # NOTE(daniel): this is a temporary fix to the timeline widget
    # it should be replaced/fixed shortly
    return 'offseason'

    if not self.programActive():
      return 'offseason'

    if self.beforeOrgSignupStart():
      return 'kickoff_period'

    if self.beforeStudentSignup():
      return 'org_signup_period'

    if self.beforeStudentsAnnounced():
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

    if time.isBetween(self.orgSignupEnd(), self.orgsAnnouncedOn()):
      return ("Accepted Orgs Announced In", self.orgsAnnouncedOn())

    if self.orgsAnnounced() and self.beforeStudentSignupStart():
      return ("Student Application Opens", self.studentSignupStart())

    if self.studentSignup():
      return ("Student Application Deadline", self.studentSignupEnd())

    if time.isBetween(self.studentSignupEnd(), self.applicationMatchedOn()):
      return ("Proposal Matched Deadline", self.applicationMatchedOn())

    if time.isBetween(
        self.applicationMatchedOn(), self.applicationReviewEndOn()):
      return ("Proposal Scoring Deadline", self.applicationReviewEndOn())

    if time.isBetween(
        self.applicationReviewEndOn(), self.studentsAnnouncedOn()):
      return ("Accepted Students Announced", self.studentsAnnouncedOn())

    return ('', None)

  def studentsAnnouncedOn(self):
    return self.timeline.accepted_students_announced_deadline

  def studentsAnnounced(self):
    return time.isAfter(self.studentsAnnouncedOn())

  def beforeStudentsAnnounced(self):
    return time.isBefore(self.studentsAnnouncedOn())

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
    return time.isAfter(first_survey_start)

  def formSubmissionStartOn(self):
    """Returns the date after which accepted students may submit their forms.

    Returns:
      datetime.datetime object representing a point in time after which
        student forms may be submitted.
    """
    return self.timeline.form_submission_start

  def afterFormSubmissionStart(self):
    """Answers the question if the current point in time is after students can
    start submitting their forms.

    Returns:
      A bool value which is True if the current time is after students can
        start submitting their forms.
    """
    return time.isAfter(self.formSubmissionStartOn())


class RequestData(request_data.RequestData):
  """Object containing data we query for each request in the GSoC module.

  The only view that will be exempt is the one that creates the program.

  Fields:
    site: The Site entity
    user: The user entity (if logged in)
    css_path: a part of the css to fetch the GSoC specific CSS resources
    programs: All GSoC programs.
    program_timeline: The GSoCTimeline entity
    is_mentor: is the current user a mentor in the program
    is_student: is the current user a student in the program
    is_org_admin: is the current user an org admin in the program
    org_admin_for: the organizations the current user is an admin for
    mentor_for: the organizations the current user is a mentor for
    organization: the organization for the current url

  Raises:
    out_of_band: 404 when the program does not exist
  """

  def __init__(self, request, args, kwargs):
    """Constructs a new RequestData object.

    Args:
      request: Django HTTPRequest object.
      args: The args that Django sends along with the request.
      kwargs: The kwargs that Django sends along with the request.
    """
    super(RequestData, self).__init__(request, args, kwargs)

    self.models = types.SOC_MODELS

    # program wide fields
    self._program_timeline = self._unset
    self._programs = self._unset
    self._org_app = self._unset

    # user profile specific fields
    self._is_mentor = self._unset
    self._is_student = self._unset
    self._is_org_admin = self._unset
    self._mentor_for = self._unset
    self._org_admin_for = self._unset
    self._organization = self._unset

    self._url_project = self._unset
    self._url_proposal = self._unset

    # _org_map contains only those organizations for which the current user
    # is a mentor or org admin.
    self._org_map = self._unset

  @property
  def css_path(self):
    """Returns the css_path property."""
    return 'gsoc'

  @property
  def is_mentor(self):
    """Returns the is_mentor field."""
    if not self._isSet(self._is_mentor):
      if not self.ndb_profile:
        self._is_mentor = False
      else:
        self._is_mentor = self.ndb_profile.is_mentor or self.is_org_admin
    return self._is_mentor

  @property
  def is_org_admin(self):
    """Returns the is_org_admin field."""
    if not self._isSet(self._is_org_admin):
      if not self.ndb_profile:
        self._is_org_admin = False
      else:
        self._is_org_admin = (self.ndb_profile.is_admin or
            user_logic.isHostForProgram(self.ndb_user, self.program.key()))
    return self._is_org_admin

  @property
  def is_student(self):
    """Returns the is_student field."""
    if not self._isSet(self._is_student):
      if not self.ndb_profile:
        self._is_student = False
      else:
        self._is_student = self.ndb_profile.is_student
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

  def _getOrganization(self):
    """Returns the organization field."""
    if not self._isSet(self._organization):
      if self.kwargs.get('organization'):
        fields = [
            self.program.key().id_or_name(),
            self.kwargs.get('organization')]
        org_key_name = '/'.join(fields)
        self._organization = self.models.ndb_org_model.get_by_id(org_key_name)
        if not self._organization:
          raise exception.NotFound(
              message="There is no organization for url '%s'" % org_key_name)
      else:
        self._organization = None
    return self._organization

  def _setOrganization(self, organization):
    """Sets the organization field to the specified value."""
    self._organization = organization

  # TODO(daniel): organization should be immutable. All the parts, which
  # actually try to override this value, should be changed
  organization = property(_getOrganization, _setOrganization)

  @property
  def org_admin_for(self):
    """Returns the org_admin_for field."""
    if not self._isSet(self._org_admin_for):
      if self.ndb_profile:
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
  def redirect(self):
    """Returns the redirect helper."""
    if not self._isSet(self._redirect):
      self._redirect = RedirectHelper(self)
    return self._redirect

  @property
  def timeline(self):
    """Returns the timeline field."""
    if not self._isSet(self._timeline):
      self._timeline = TimelineHelper(self.program_timeline, self.org_app)
    return self._timeline

  @property
  def url_project(self):
    """Returns the url_project field.

    This property represents a project entity corresponding to a profile whose
    identifier is a part of the URL of the processed request. Numerical
    identifier of the project is also a part of the URL.

    Returns:
      Retrieved project entity.

    Raises:
      exception.BadRequest: if some data is missing in the current request.
      exception.NotFound: if no entity is found.
    """
    if not self._isSet(self._url_project):
      if 'id' not in self.kwargs:
        raise exception.BadRequest(
            message='The request does not contain project id.')
      else:
        self._url_project = project_model.GSoCProject.get_by_id(
            int(self.kwargs['id']), self.url_ndb_profile.key.to_old_key())

        if not self._url_project:
          raise exception.NotFound(
              message='Requested project does not exist.')

    return self._url_project

  @property
  def url_proposal(self):
    """Returns the url_proposal field.

    This property represents a proposal entity corresponding to a profile whose
    identifier is a part of the URL of the processed request. Numerical
    identifier of the proposal is also a part of the URL.

    Returns:
      Retrieved proposal entity.

    Raises:
      exception.BadRequest: if some data is missing in the current request.
      exception.NotFound: if no entity is found.
    """
    if not self._isSet(self._url_proposal):
      if 'id' not in self.kwargs:
        raise exception.BadRequest(
            message='The request does not contain proposal id.')
      else:
        self._url_proposal = proposal_model.GSoCProposal.get_by_id(
            int(self.kwargs['id']), self.url_ndb_profile.key.to_old_key())

        if not self._url_proposal:
          raise exception.NotFound(
              message='Requested proposal does not exist.')

    return self._url_proposal

  def _initOrgMap(self):
    """Initializes _org_map by inserting there all organizations for which
    the current user is either a mentor or org admin.
    """
    if not self._isSet(self._org_map):
      if self.ndb_profile:
        org_keys = set(self.ndb_profile.mentor_for)
        org_keys.update(self.ndb_profile.admin_for)

        orgs = ndb.get_multi(org_keys)

        self._org_map = dict((i.key, i) for i in orgs)
      else:
        self._org_map = {}

  def getOrganization(self, org_key):
    """Retrieves the specified organization.
    """
    self._initOrgMap()
    if org_key not in self._org_map:
      org = db.get(org_key)
      return org

    return self._org_map[org_key]

  def orgAdminFor(self, org_key):
    """Returns true iff the user is admin for the specified organization.

    Args:
      org_key: Organization key.
    """
    if user_logic.isHostForProgram(self.ndb_user, self.program.key()):
      return True

    if not self.ndb_profile:
      return False

    return org_key in self.ndb_profile.admin_for

  def mentorFor(self, org_key):
    """Returns true iff the user is mentor for the specified organization.

    Args:
      org_key: Organization key.
    """
    if user_logic.isHostForProgram(self.ndb_user, self.program.key()):
      return True

    if not self.ndb_profile:
      return False

    return org_key in self.ndb_profile.mentor_for

  def isPossibleMentorForProposal(self, mentor_profile=None):
    """Checks if the user is a possible mentor for the proposal in the data.
    """
    profile = mentor_profile if mentor_profile else self.ndb_profile

    return profile.key.to_old_key() in self.url_proposal.possible_mentors


class RedirectHelper(request_data.RedirectHelper):
  """Helper for constructing redirects."""

  def document(self, document):
    """Override this method to set GSoC specific _url_name."""
    super(RedirectHelper, self).document(document)
    self._url_name = 'show_gsoc_document'
    return self

  def connect_user(self, user=None, org_key=None):
    """Sets the _url_name for a gsoc_user_connection redirect.

    Intended for use when generating a url for a redirect to OrgConnectionPage.

    Args:
      user: The User instance for which one wishes to establish a connection to
        an organization.
      organization: The organization instance to which a user is trying
        to connect.
    """
    if not user:
      assert 'user' in self._data.kwargs
      user = self._data.kwargs['user']

    self.connect_org(org_key=org_key)
    self.kwargs['link_id'] = user.link_id
    return self

  def connect_org(self, org_key=None):
    """Sets the _url_name for a gsoc_org_connection redirect.

    Intended for use when generating a url for a redirect to
    UserConnectionPage.

    Args:
      org_key: Override the current organization (if any) provided
        by the RequestData object. Intended specifically for the call
        from connect_user.
    """
    if not org_key:
      org_key = self._data.url_ndb_org.key

    # We need to reassign the kwarg to the org's link_id since it's
    # being set to the Organization object
    self.kwargs['sponsor'] = melange_org_model.getSponsorId(org_key)
    self.kwargs['program'] = melange_org_model.getProgramId(org_key)
    self.kwargs['organization'] = melange_org_model.getOrgId(org_key)
    self._url_name = url_names.GSOC_USER_CONNECTION
    return self

  def show_org_connection(self, connection):
    """ Sets up kwargs for a gsoc_show_org_connection redirect.

    Args:
      connection: The Connection instance to view.
    """
    org_key = (
        connection_model.Connection.organization
            .get_value_for_datastore(connection))
    self.connect_org(org_key)

    self.kwargs['id'] = connection.key().id()
    # Need to make sure that when the view loads it can query for the
    # connection, and in order to do that it needs its parent entity.
    self.kwargs['user'] = connection.parent().parent().key().name()
    self._url_name = url_names.GSOC_SHOW_ORG_CONNECTION
    return self

  def show_user_connection(self, connection):
    """ Sets up kwargs for a gsoc_show_org_connection redirect.
    Args:
      connection: The Connection instance to view.
    """
    self.show_org_connection(connection)
    self._url_name = url_names.GSOC_SHOW_USER_CONNECTION
    return self

  def profile_anonymous_connection(self, role, token):
    """ Sets up kwargs for the gsoc_profile_anonymous_connection reirect.

    Args:
      role: Role (org_admin | mentor) to which the user will be promoted
          after their profile is created.
      token: The UUID token (string representation) for an
          AnonymousConnection object.
    """
    self.createProfile(role)
    self.kwargs['key'] = token
    self._url_name = url_names.GSOC_ANONYMOUS_CONNECTION
    return self

  # TODO(daniel): id built-in function should not be shadowed
  def survey_record(self, survey=None, id=None, student=None):
    """Returns the redirector object with the arguments for survey record

    Args:
      survey: the survey's link_id
    """
    self.program()
    self.id(id=id)

    if not student:
      assert 'user' in self._data.kwargs
      student = self._data.kwargs['user']
    self.kwargs['user'] = student

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
    project = record.parent()

    self.program()
    self.id()
    self.kwargs['user'] = project.parent().link_id
    self.kwargs['group'] = record.grading_survey_group.key().id_or_name()
    self.kwargs['record'] = record.key().id()

    return self
