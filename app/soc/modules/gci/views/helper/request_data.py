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
request in the GCI module.
"""

from google.appengine.ext import db

# TODO(nathaniel): Still reticent about having the RequestData object
# allowed to raise exceptions from the exception module.

from codein import types

from melange.request import exception
from melange.utils import time

from soc.views.helper import request_data

from soc.modules.gci.logic.helper import timeline as timeline_helper
from soc.modules.gci.models.program import GCIProgram
from soc.modules.gci.models import profile as profile_model
from soc.modules.gci.models import organization as org_model

from soc.modules.gci.views.helper import url_names


class TimelineHelper(request_data.TimelineHelper):
  """Helper class for the determination of the currently active period.
     see the super class, soc.views.helper.request_data.TimelineHelper
  """

  def currentPeriod(self):
    """Return where we are currently on the timeline.
    """
    # This is required as a protection against the cases when the
    # org apps are not created for the program and hence there is
    # no way we can determine if the org app has started.
    if self.beforeProgramStart():
      return 'kickoff_period'

    if self.beforeOrgSignupStart():
      return 'kickoff_period'

    if self.orgSignup():
      return 'org_signup_period'

    if self.studentSignup():
      return 'student_signup_period'

    if self.tasksPubliclyVisible() and self.programActive():
      return 'working_period'

    return 'offseason'

  def nextDeadline(self):
    """Determines the next deadline on the timeline.
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

    if time.isBetween(self.tasksPubliclyVisible(),
                              self.tasksClaimEndOn()):
      return ("Tasks Claim Deadline", self.tasksClaimEndOn())

    if time.isBetween(self.tasksClaimEndOn(), self.stopAllWorkOn()):
      return ("Work Submission Deadline", self.stopAllWorkOn())

    return ('', None)

  def tasksPubliclyVisibleOn(self):
    return self.timeline.tasks_publicly_visible

  def tasksPubliclyVisible(self):
    return time.isAfter(self.tasksPubliclyVisibleOn())

  def tasksClaimEndOn(self):
    return self.timeline.task_claim_deadline

  def tasksClaimEnded(self):
    return time.isAfter(self.tasksClaimEndOn())

  def stopAllWorkOn(self):
    return self.timeline.stop_all_work_deadline

  def allWorkStopped(self):
    return time.isAfter(self.stopAllWorkOn())

  def stopAllReviewsOn(self):
    return self.timeline.work_review_deadline

  def allReviewsStopped(self):
    return time.isAfter(self.stopAllReviewsOn())

  def winnersAnnouncedOn(self):
    return self.timeline.winners_announced_deadline

  def winnersAnnounced(self):
    return time.isAfter(self.winnersAnnouncedOn())

  def remainingTime(self):
    """Returns the remaining time in the program a tuple of days, hrs and mins.
    """
    end = self.stopAllWorkOn()
    return timeline_helper.remainingTimeSplit(end)

  def tasksVisibleInTime(self):
    """Returns the remaining time till the tasks are publicly visible to
    the students.
    """
    end = self.tasksPubliclyVisibleOn()
    return timeline_helper.remainingTimeSplit(end)

  def completePercentage(self):
    """Computes the remaining time percentage

    It is VERY IMPORTANT TO NOTE here that this percentage is between the
    task opening date and the date task can be last claimed.

    However if the all work stop deadline is set after the task claim date
    that will only be visible on per task basis, this percentage would still
    return zero.
    """
    start = self.tasksPubliclyVisibleOn()
    end = self.tasksClaimEndOn()

    if not start or not end:
      return 0.0

    return timeline_helper.completePercentage(start, end)

  def stopwatchPercentage(self):
    """Computes the closest matching percentage for the static clock images.
    """
    complete_percentage = self.completePercentage()
    return timeline_helper.stopwatchPercentage(complete_percentage)


class RequestData(request_data.RequestData):
  """Object containing data we query for each request in the GCI module.

  The only view that will be exempt is the one that creates the program.

  Fields:
    site: The Site entity
    user: The user entity (if logged in)
    css_path: a part of the css to fetch the GCI specific CSS resources
    programs: All GCI programs.
    program_timeline: The GCITimeline entity
    is_mentor: is the current user a mentor in the program
    is_student: is the current user a student in the program
    is_org_admin: is the current user an org admin in the program
    org_admin_for: the organizations the current user is an admin for
    mentor_for: the organizations the current user is a mentor for
    student_info: the StudentInfo for the current user and program
    organization: the GCIOrganization for the current url

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

    self.models = types.CI_MODELS

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
    self._student_info = self._unset
    self._organization = self._unset

    # _org_map contains only those organizations for which the current user
    # is a mentor or org admin.
    self._org_map = self._unset

  @property
  def css_path(self):
    """Returns the css_path property."""
    return 'gci'

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
        self._is_student = bool(profile_model.GCIProfile.student_info \
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

  def _getOrganization(self):
    """Returns the organization field."""
    if not self._isSet(self._organization):
      if self.kwargs.get('organization'):
        fields = [
            self.program.key().id_or_name(),
            self.kwargs.get('organization')]
        org_key_name = '/'.join(fields)
        self._organization = org_model.GCIOrganization.get_by_key_name(
            org_key_name)
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
  def program_timeline(self):
    """Returns the program_timeline field."""
    if not self._isSet(self._program_timeline):
      self._getProgramWideFields()
    return self._program_timeline

  @property
  def programs(self):
    """Memorizes and returns a list of all programs."""
    if not self._isSet(self._programs):
      self._programs = list(GCIProgram.all())
    return self._programs

  @property
  def redirect(self):
    """Returns the redirect helper."""
    if not self._isSet(self._redirect):
      self._redirect = RedirectHelper(self)
    return self._redirect

  @property
  def student_info(self):
    """Returns the student_info field."""
    if not self._isSet(self._student_info):
      if not self.is_student:
        self._student_info = None
      else:
        student_info_key = profile_model.GCIProfile.student_info \
            .get_value_for_datastore(self.profile)
        self._student_info = db.get(student_info_key)
    return self._student_info

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

  def getOrganization(self, org_key):
    """Retrieves the specified organization.
    """
    self._initOrgMap()
    if org_key not in self._org_map:
      org = db.get(org_key)
      return org

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


class RedirectHelper(request_data.RedirectHelper):
  """Helper for constructing redirects.
  """

  def document(self, document):
    """Override this method to set GCI specific _url_name.
    """
    super(RedirectHelper, self).document(document)
    self._url_name = 'show_gci_document'
    return self

  def events(self):
    """Sets the _url_name for the events page, if it is set.
    """
    super(RedirectHelper, self).events()
    self._url_name = 'gci_events'
    return self

