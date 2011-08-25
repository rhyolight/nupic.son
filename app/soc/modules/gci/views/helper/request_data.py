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
request in the GCI module.
"""

__authors__ = [
  '"Selwyn Jacob" <selwynjacob90@gmail.com>',
]


from google.appengine.ext import db

from soc.logic.exceptions import NotFound
from soc.models.site import Site
from soc.views.helper import request_data

from soc.modules.gci.models.program import GCIProgram
from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.gci.models.timeline import GCITimeline


class TimelineHelper(request_data.TimelineHelper):
  """Helper class for the determination of the currently active period.
     see the super class, soc.views.helper.request_data.TimelineHelper
  """

  def currentPeriod(self):
    """Return where we are currently on the timeline.
    """
    if not self.programActive():
      return 'offseason'

    if self.beforeOrgSignupStart():
      return 'kickoff_period'

    if self.afterOrgSignupStart():
      return 'org_signup_period'

    if self.afterStudentSignupStart():
      return 'student_signup_period'

    if self.tasksPubliclyVisible():
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

    if request_data.isBetween(self.orgSignupEnd(), self.orgsAnnouncedOn()):
      return ("Accepted Orgs Announced In", self.orgsAnnouncedOn())

    if self.orgsAnnounced() and self.beforeStudentSignupStart():
      return ("Student Application Opens", self.studentSignupStart())

    if self.studentSignup():
      return ("Student Application Deadline", self.studentSignupEnd())

    if request_data.isBetween(self.tasksPubliclyVisible(), self.tasksClaimEndOn()):
      return ("Tasks Claim Deadline", self.tasksClaimEndOn())

    if request_data.isBetween(self.tasksClaimEndOn(), self.stopAllWorkOn()):
      return ("Work Submission Deadline", self.stopAllWorkOn())

    return ('', None)

  def tasksPubliclyVisibleOn(self):
    return self.timeline.tasks_publicly_visible

  def tasksPubliclyVisible(self):
    return request_data.isAfter(self.tasksPubliclyVisibleOn())

  def tasksClaimEndOn(self):
    return self.timeline.task_claim_deadline

  def stopAllWorkOn(self):
    return self.timeline.stop_all_work_deadline


class RequestData(request_data.RequestData):
  """Object containing data we query for each request in the GCI module.

  The only view that will be exempt is the one that creates the program.

  Fields:
    site: The Site entity
    user: The user entity (if logged in)
    program: The GCI program entity that the request is pointing to
    programs: All GCI programs.
    program_timeline: The GCITimeline entity
    timeline: A TimelineHelper entity
    profile: The GCIProfile entity of the current user
    is_host: is the current user a host of the program
    is_mentor: is the current user a mentor in the program
    is_student: is the current user a student in the program
    is_org_admin: is the current user an org admin in the program
    org_map: map of retrieved organizations
    org_admin_for: the organizations the current user is an admin for
    mentor_for: the organizations the current user is a mentor for
    student_info: the StudentInfo for the current user and program
    organization: the GCIOrganization for the current url

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
    self.organization = None

  @property
  def programs(self):
    """Memorizes and returns a list of all programs.
    """
    if not self._programs:
      self._programs = list(GCIProgram.all())

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

  def populate(self, redirect, request, args, kwargs):
    """Populates the fields in the RequestData object.

    Args:
      request: Django HTTPRequest object.
      args & kwargs: The args and kwargs django sends along.
    """
    super(RequestData, self).populate(redirect, request, args, kwargs)

    if kwargs.get('sponsor') and kwargs.get('program'):
      program_key_name = "%s/%s" % (kwargs['sponsor'], kwargs['program'])
      program_key = db.Key.from_path('GCIProgram', program_key_name)
    else:
      program_key = Site.active_program.get_value_for_datastore(self.site)
      program_key_name = program_key.name()

    timeline_key = db.Key.from_path('GCITimeline', program_key_name)

    org_app_key_name = 'gci_program/%s/orgapp' % program_key_name
    org_app_key = db.Key.from_path('OrgAppSurvey', org_app_key_name)

    keys = [program_key, timeline_key, org_app_key]

    self.program, self.program_timeline, self.org_app = db.get(keys)

    if not self.program:
      raise NotFound("There is no program for url '%s'" % program_key_name)

    self.timeline = TimelineHelper(self.program_timeline, self.org_app)

    if kwargs.get('organization'):
      fields = [self.program.key().id_or_name(), kwargs.get('organization')]
      org_key_name = '/'.join(fields)
      self.organization = GCIOrganization.get_by_key_name(org_key_name)
      if not self.organization:
        raise NotFound("There is no organization for url '%s'" % org_key_name)

    if self.user:
      key_name = '%s/%s' % (self.program.key().name(), self.user.link_id)
      self.profile = GCIProfile.get_by_key_name(
          key_name, parent=self.user)

      host_key = GCIProgram.scope.get_value_for_datastore(self.program)
      self.is_host = host_key in self.user.host_for

    if self.profile:
      org_keys = set(self.profile.mentor_for + self.profile.org_admin_for)

      prop = GCIProfile.student_info
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
    self._url_name = 'gci_show_document'
    return self

  def homepage(self):
    """Sets the _url_name for the homepage of the current GCI program.
    """
    super(RedirectHelper, self).homepage()
    self._url_name = 'gci_homepage'
    return self

  def dashboard(self):
    """Sets the _url_name for dashboard page of the current GCI program.
    """
    super(RedirectHelper, self).dashboard()
    self._url_name = 'gci_dashboard'
    return self

  def events(self):
    """Sets the _url_name for the events page, if it is set.
    """
    super(RedirectHelper, self).events()
    self._url_name = 'gci_events'
    return self
