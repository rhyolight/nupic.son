#!/usr/bin/env python2.5
#
# Copyright 2012 the Melange authors.
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

""" This module contains the object used to represent invitations and
requests between a user and an organization
"""
from django.utils.translation import ugettext
from google.appengine.ext import db
from soc.models.organization import Organization
from soc.models.profile import Profile


RESPONSE_STATE_ACCEPTED = 'Accepted'
RESPONSE_STATE_REJECTED = 'Rejected'
RESPONSE_STATE_UNREPLIED = 'Unreplied'

RESPONSE_STATES = [
    RESPONSE_STATE_UNREPLIED, RESPONSE_STATE_ACCEPTED, RESPONSE_STATE_REJECTED]

STATUS_STATES = {'accepted':'Accepted', 'rejected':'Rejected',
    'user_action_req':'User Action Required', 
    'org_action_req' : 'Org Action Required'}

class Connection(db.Model):
  """ Connection model.
  This model is intended to be used to represent either an invitation or 
  request between a User and an Organization. The type of role to be granted
  to the user is determined by the four states: user_mentor, user_org_admin,
  org_mentor, and org_org_admin, which correspond to the respective party's
  acceptance of a given role. 

  Parent: soc.models.user.User (also parent of self.profile here)
  """

  #: The User's state in respect to a mentoring role.
  user_mentor = db.StringProperty(
      default=RESPONSE_STATE_UNREPLIED, choices=RESPONSE_STATES)

  #: The User's state in respect to an org admin role.
  user_org_admin = db.StringProperty(
      default=RESPONSE_STATE_UNREPLIED, choices=RESPONSE_STATES)

  #: An org's state in respect to a mentoring role for the user.
  org_mentor = db.StringProperty(
      default=RESPONSE_STATE_UNREPLIED, choices=RESPONSE_STATES)

  #: An org's state in respect to an org admin role for the user.
  org_org_admin = db.StringProperty(
      default=RESPONSE_STATE_UNREPLIED, choices=RESPONSE_STATES)

  #: The organization entity involved in the connection for which a user
  #: may gain heightened privileges.
  organization = db.ReferenceProperty(Organization, 
      required=True,
      collection_name='connections')
  
  #: Property for the ShowConnection page to keep track of the time that the
  #: connection was initiated.
  created_on = db.DateTimeProperty(auto_now_add=True)

  @staticmethod
  def allFields():
    """Returns a list of all names of fields in this model.
    """
    return ['user_mentor', 'user_org_admin', 'org_mentor', 'org_org_admin',
        'organization', 'profile', 'created_on']

  def acceptMentorRoleByUser(self):
    self.user_mentor = RESPONSE_STATE_ACCEPTED

  def rejectMentorRoleByUser(self):
    self.user_mentor = RESPONSE_STATE_REJECTED

  def isMentorRoleAcceptedByUser(self):
    return self.user_mentor == RESPONSE_STATE_ACCEPTED

  def acceptMentorRoleByOrg(self):
    self.org_mentor = RESPONSE_STATE_ACCEPTED

  def rejectMentorRoleByOrg(self):
    self.org_mentor = RESPONSE_STATE_REJECTED

  def isMentorRoleAcceptedByOrg(self):
    return self.org_mentor == RESPONSE_STATE_ACCEPTED

  def acceptOrgAdminRoleByUser(self):
    self.user_org_admin = RESPONSE_STATE_ACCEPTED

  def rejectOrgAdminRoleByUser(self):
    self.user_org_admin = RESPONSE_STATE_REJECTED

  def isOrgAdminRoleAcceptedByUser(self):
    return self.user_org_admin == RESPONSE_STATE_ACCEPTED

  def acceptOrgAdminRoleByOrg(self):
    self.org_org_admin = RESPONSE_STATE_ACCEPTED

  def rejectOrgAdminRoleByOrg(self):
    self.org_org_admin = RESPONSE_STATE_REJECTED

  def isOrgAdminRoleAcceptedByOrg(self):
    return self.org_org_admin == RESPONSE_STATE_ACCEPTED

  def isMentorRoleAccepted(self):
    return self.isMentorRoleAcceptedByUser() and \
        self.isMentorRoleAcceptedByOrg()

  def isOrgAdminRoleAccepted(self):
    return self.isOrgAdminRoleAcceptedByUser() and \
        self.isOrgAdminRoleAcceptedByOrg()

  def keyName(self):
    """Returns a string which uniquely represents the entity.
    """
    return '/'.join([self.parent_key().name(), str(self.key().id())])

  def status(self):
    """ Returns a simple status string based on which of the user/org
    properties has been set. 
    """
    if self.user_mentor == RESPONSE_STATE_ACCEPTED and \
        self.org_mentor == RESPONSE_STATE_ACCEPTED:
      return STATUS_STATES['accepted']
    elif self.user_mentor == RESPONSE_STATE_REJECTED or \
        self.org_mentor == RESPONSE_STATE_REJECTED:
      return STATUS_STATES['rejected']
    elif self.user_mentor == RESPONSE_STATE_UNREPLIED:
      return STATUS_STATES['user_action_req']
    elif self.org_mentor == RESPONSE_STATE_UNREPLIED:
      return STATUS_STATES['org_action_req']
    else:
      return ''

class AnonymousConnection(db.Model):
  """ This model is intended for use as a placeholder Connection for the
  scenario in which an org admin attempts to send an email invitation to
  a person who does not have both a User entity and GSoCProfile. This 
  model is deleted and 'replaced' by an actual Connection object should
  the user decide to register.

  Parent: soc.models.org.Organization
  """

  #: A string to designate the role that will be recreated for the actual
  #: connection object.
  role = db.StringProperty(choices=['mentor', 'org_admin'])

  #: Hash hexdigest() of this object's key to save time when validating
  #: when the user registers.
  hash_id = db.StringProperty()

  #: The email to which the anonymous connection was sent; this should be 
  #: queried against to prevent duplicate anonymous connections.
  email = db.StringProperty()
