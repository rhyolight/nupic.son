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
from soc.views.helper.request_data import RequestData

from soc.modules.gci.models.program import GCIProgram
from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.logic.models.organization import logic as org_logic

class RequestData(RequestData):
  """Object containing data we query for each request in the GCI module.

  The only view that will be exempt is the one that creates the program.

  Fields:
    site: The Site entity
    user: The user entity (if logged in)
    program: The GCI program entity that the request is pointing to
    programs: All GCI programs.
    profile: The GCIProfile entity of the current user
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

    org_app_key_name = 'gci_program/%s/orgapp' % program_key_name
    org_app_key = db.Key.from_path('OrgAppSurvey', org_app_key_name)

    keys = [program_key, org_app_key]

    self.program, self.org_app = db.get(keys)

    if not self.program:
      raise NotFound("There is no program for url '%s'" % program_key_name)

    if kwargs.get('organization'):
      org_keyfields = {
          'link_id': kwargs.get('organization'),
          'scope_path': self.program.key().id_or_name(),
          }
      self.organization = org_logic.getFromKeyFieldsOr404(org_keyfields)

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
    
 
class RedirectHelper(object):
  """Helper for constructing redirects.
  """

  def document(self, document):
    """Override this method to set GCI specific _url_name.
    """
    self._url_name = 'gci_show_document'
    return super(RedirectHelper, self).document(document)
    
  def homepage(self):
    """Sets the _url_name for the homepage of the current GCI program.
    """
    self._url_name = 'gci_homepage'
    return super(RedirectHelper, self).homepage()

  def searchpage(self):
    """Sets the _url_name for the searchpage of the current GCI program.
    """
    self._url_name = 'gci_search'
    return super(RedirectHelper,self).searchpage()

  def dashboard(self):
    """Sets the _url_name for dashboard page of the current GCI program.
    """
    self._url_name = 'gci_dashboard'
    return super(RedirectHelper, self).dashboard()

  def events(self):
    """Sets the _url_name for the events page, if it is set.
    """
    key = GCIProgram.events_page.get_value_for_datastore(self._data.program)

    self._url_name = 'gci_events'
    return super(RedirectHelper, self).events()
