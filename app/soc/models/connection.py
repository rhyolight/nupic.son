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
RESPONSE_STATE_WITHDRAWN = 'Withdrawn'

RESPONSE_STATES = [
    RESPONSE_STATE_UNREPLIED, RESPONSE_STATE_ACCEPTED, 
    RESPONSE_STATE_REJECTED,RESPONSE_STATE_WITHDRAWN
    ]

STATUS_STATES = {'withdrawn':'Withdrawn',
    'accepted':'Accepted',
    'rejected':'Rejected',
    'user_action_req':'User Action Required', 
    'org_action_req' : 'Org Action Required',
    'withdrawn' : 'Withdrawn'
    }

class Connection(db.Model):
  """ Connection model.
  This model is intended to be used to represent either an invitation or 
  request between a User and an Organization. The type of role to be granted
  to the user is determined by the role field and promotion is handled
  depending on the states of user and org acceptance. The methods below
  are simply convenience to clean up a lot of the logic in the connection
  module for determining valid actions.

  Parent: soc.models.user.User (also parent of self.profile here)
  """

  #: The User's state with respect to a given role.
  user_state = db.StringProperty(default='Unreplied', 
      choices=RESPONSE_STATES)

  #: The Org's state with respect to a given role.
  org_state = db.StringProperty(default='Unreplied',
      choices=RESPONSE_STATES)

  role = db.StringProperty(default='Mentor', 
      choices=['Mentor', 'Org Admin'])

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
    return ['user_state', 'org_state', 'role','organization', 
        'profile', 'created_on']

  def isUserUnreplied(self):
    return self.user_state == RESPONSE_STATE_UNREPLIED

  def isOrgUnreplied(self):
    return self.org_state == RESPONSE_STATE_UNREPLIED

  def isUserAccepted(self):
    return self.user_state == RESPONSE_STATE_ACCEPTED

  def isOrgAccepted(self):
    return self.org_state == RESPONSE_STATE_ACCEPTED

  def isUserRejected(self):
    return self.user_state == RESPONSE_STATE_REJECTED

  def isOrgRejected(self):
    return self.org_state == RESPONSE_STATE_REJECTED

  def isUserWithdrawn(self):
    return self.user_state == RESPONSE_STATE_WITHDRAWN

  def isOrgWithdrawn(self):
    return self.org_state == RESPONSE_STATE_WITHDRAWN

  def isWithdrawn(self):
    return self.user_state == RESPONSE_STATE_WITHDRAWN \
        or self.org_state == RESPONSE_STATE_WITHDRAWN

  def isStalemate(self):
    return (self.user_state == RESPONSE_STATE_ACCEPTED \
        and self.org_state == RESPONSE_STATE_REJECTED) \
        or (self.user_state == RESPONSE_STATE_REJECTED \
        and self.org_state == RESPONSE_STATE_ACCEPTED)

  def isAccepted(self):
    return self.user_state == RESPONSE_STATE_ACCEPTED and \
        self.org_state == RESPONSE_STATE_ACCEPTED

  def keyName(self):
    """Returns a string which uniquely represents the entity.
    """
    return '/'.join([self.parent_key().name(), str(self.key().id())])

  def status(self):
    """ Returns a simple status string based on which of the user/org
    properties has been set. 
    """
    if self.user_state == 'Accepted' and self.org_state == 'Accepted':
      return STATUS_STATES['accepted']
    elif self.user_state == 'Withdrawn' or self.org_state == 'Withdrawn':
      return STATUS_STATES['withdrawn']
    elif self.user_state == 'Rejected' or self.org_state == 'Rejected':
      return STATUS_STATES['rejected']
    elif self.user_state == 'Accepted':
      return STATUS_STATES['org_action_req']
    elif self.org_state == 'Accepted':
      return STATUS_STATES['user_action_req']
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
  role = db.StringProperty(choices=['Mentor', 'Org Admin'])

  #: Hash hexdigest() of this object's key to save time when validating
  #: when the user registers.
  hash_id = db.StringProperty()

  #: The email to which the anonymous connection was sent; this should be 
  #: queried against to prevent duplicate anonymous connections.
  email = db.StringProperty()
