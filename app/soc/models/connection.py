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

ORG_ADMIN_STATE = 'org_admin'
MENTOR_STATE = 'mentor'

# Strings used in the dashboard (via the status() method below) to display
# short, simple status messages for connections based on its state.
STATUS_STATE_ACCEPTED = 'Accepted'
STATUS_STATE_REJECTED = 'Rejected'
STATUS_STATE_WITHDRAWN = 'Withdrawn'
STATUS_STATE_UNREPLIED = 'Unreplied'
STATUS_STATE_USER_ACTION_REQ = 'User Action Required'
STATUS_STATE_ORG_ACTION_REQ = 'Org Action Required'

STATUS_CHOICES = [STATUS_STATE_ACCEPTED,
    STATUS_STATE_REJECTED,
    STATUS_STATE_WITHDRAWN,
    STATUS_STATE_UNREPLIED,
    STATUS_STATE_USER_ACTION_REQ,
    STATUS_STATE_ORG_ACTION_REQ
    ]

class Connection(db.Model):
  """Connection model.
  This model is intended to be used to represent either an invitation or 
  request between a User and an Organization. The type of role to be granted
  to the user is determined by the role field and promotion is handled
  depending on the states of user and org acceptance. The methods below
  are simply convenience to clean up a lot of the logic in the connection
  module for determining valid actions.

  Parent: soc.models.user.User (also parent of self.profile here)
  """

  #: The User's state with respect to a given role.
  user_state = db.StringProperty(default=STATUS_STATE_UNREPLIED, 
      choices=STATUS_CHOICES)

  #: The Org's state with respect to a given role.
  org_state = db.StringProperty(default=STATUS_STATE_UNREPLIED,
      choices=STATUS_CHOICES)

  role = db.StringProperty(default=MENTOR_STATE, 
      choices=[MENTOR_STATE, ORG_ADMIN_STATE])

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
    return self.user_state == STATUS_STATE_UNREPLIED

  def isOrgUnreplied(self):
    return self.org_state == STATUS_STATE_UNREPLIED

  def isUserAccepted(self):
    return self.user_state == STATUS_STATE_ACCEPTED

  def isOrgAccepted(self):
    return self.org_state == STATUS_STATE_ACCEPTED

  def isUserRejected(self):
    return self.user_state == STATUS_STATE_REJECTED

  def isOrgRejected(self):
    return self.org_state == STATUS_STATE_REJECTED

  def isUserWithdrawn(self):
    return self.user_state == STATUS_STATE_WITHDRAWN

  def isOrgWithdrawn(self):
    return self.org_state == STATUS_STATE_WITHDRAWN

  def isWithdrawn(self):
    return self.user_state == STATUS_STATE_WITHDRAWN \
        or self.org_state == STATUS_STATE_WITHDRAWN

  def isStalemate(self):
    return (self.user_state == STATUS_STATE_ACCEPTED \
        and self.org_state == STATUS_STATE_REJECTED) \
        or (self.user_state == STATUS_STATE_REJECTED \
        and self.org_state == STATUS_STATE_ACCEPTED)

  def isAccepted(self):
    return self.user_state == STATUS_STATE_ACCEPTED and \
        self.org_state == STATUS_STATE_ACCEPTED

  def keyName(self):
    """Returns a string which uniquely represents the entity.
    """
    return '/'.join([self.parent_key().name(), str(self.key().id())])

  def getUserFriendlyRole(self):
    """Converts an internal role representation to a user-friendly version 
    to be used in templates and dashboard.
    """
    return 'Org Admin' if self.role == ORG_ADMIN_STATE else 'Mentor'

  def status(self):
    """Determine the state of the connection and select a string to
    indicate a user-facing status message.

    Returns:
       "Accepted" if both parties have confirmed the connection.
       "Rejected" if one or both have rejected it.
       "Withdrawn" if the initiating party has withdrawn the connection.
       "User/Org Action Required" if one party has accepted the connection
          and is waiting on a response from the other.
    """
    if self.user_state == STATUS_STATE_ACCEPTED and  \
        self.org_state == STATUS_STATE_ACCEPTED:
      return STATUS_STATE_ACCEPTED
    elif self.user_state == STATUS_STATE_WITHDRAWN or \
        self.org_state == STATUS_STATE_WITHDRAWN:
      return STATUS_STATE_WITHDRAWN
    elif self.user_state == STATUS_STATE_REJECTED or \
        self.org_state == STATUS_STATE_REJECTED:
      return STATUS_STATE_REJECTED
    elif self.user_state == STATUS_STATE_ACCEPTED:
      return STATUS_STATE_ORG_ACTION_REQ
    elif self.org_state == STATUS_STATE_ACCEPTED:
      return STATUS_STATE_USER_ACTION_REQ
    else:
      # This should never happen, so we're going to blow up execution.
      raise ValueError()

class AnonymousConnection(db.Model):
  """This model is intended for use as a placeholder Connection for the
  scenario in which an org admin attempts to send an email invitation to
  a person who does not have both a User entity and program Profile. This 
  model is deleted and 'replaced' by an actual Connection object should
  the user decide to register.

  Parent: soc.models.org.Organization
  """

  #: A string to designate the role that will be recreated for the actual
  #: connection object.
  role = db.StringProperty(choices=[MENTOR_STATE, ORG_ADMIN_STATE])

  #: Hash hexdigest() of this object's key to save time when validating
  #: when the user registers.
  hash_id = db.StringProperty()

  #: The email to which the anonymous connection was sent; this should be 
  #: queried against to prevent duplicate anonymous connections.
  email = db.StringProperty()
