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

""" This module contains a model used to represent a connection between
a user and an organization.
"""
from django.utils.translation import ugettext
from google.appengine.ext import db
from soc.models.organization import Organization
from soc.models.profile import Profile


# Constants to represent the different states that users and org admins
# may select for a connection. Users may select either ROLE or NO_ROLE, 
# meaning that they will accept whatever role the org admin assigns them.
# Org Admins may choose the first three, either declining to accept a
# role or selecting one. It is up to the org admins to leave messages
# on the connection to differentiate between a declined connection and
# one that has just not been answered.
ORG_ADMIN_ROLE = 'org_admin'
MENTOR_ROLE = 'mentor'
NO_ROLE = 'no_role'
ROLE = 'role'

VERBOSE_ROLE_NAMES = {
    NO_ROLE: ugettext('No Role'),
    ROLE: ugettext('Role'),
    MENTOR_ROLE: ugettext('Mentor'),
    ORG_ADMIN_ROLE: ugettext('Organization Administrator')
    }

# Response tuples that encapsulate the available roles that users and org
# admins may respond with in their respective ShowConnection views.
USER_RESPONSES = ((NO_ROLE, 'No Role'), (ROLE, 'Role'))
ORG_RESPONSES = (
  (NO_ROLE, 'No Role'), 
  (MENTOR_ROLE, 'Mentor'), 
  (ORG_ADMIN_ROLE, 'Org Admin')
  )


class Connection(db.Model):
  """Connection model.

  This model is intended to be used to represent a connection between a user
  and an organization. Each initiated connection specifies a role which
  the organization has granted to the user and a role which the user requests
  from the organization. These two properties put together determine what
  type of role the user has for the organization at this moment.

  The class also defines a number of convenience methods to clean up 
  a lot of the logic in the connection module for determining valid actions.

  Parent: soc.models.profile.Profile
  """

  #: The User's state with respect to a given role.
  user_role = db.StringProperty(default=NO_ROLE,
      choices=(NO_ROLE, ROLE))

  #: The Org's state with respect to a given role.
  org_role = db.StringProperty(default=NO_ROLE,
      choices=(NO_ROLE, MENTOR_ROLE, ORG_ADMIN_ROLE))

  #: The organization entity involved in the connection for which a user
  #: may gain heightened privileges.
  organization = db.ReferenceProperty(Organization,
      collection_name='user_connections')

  #: Property for the ShowConnection pages to keep track of the time that the
  #: connection was initiated.
  created_on = db.DateTimeProperty(auto_now_add=True)

  #: Property for the ShowConnection pages to keep a record of the last time
  #: that either the org or user modified the connection.
  last_modified = db.DateTimeProperty(auto_now=True)

  #: Property indicating that a member of the organization has seen
  #: the latest changes made by the user.
  seen_by_org = db.BooleanProperty()

  #: Property indicating that the user has seen the latest changes made
  #: by a member of the organization.
  seen_by_user = db.BooleanProperty()

  def userRequestedRole(self):
    """Indicate whether or not a user has requested to be promoted to a 
    role for an organization.

    Returns:
      True if the user has opted for a role.
    """
    return self.user_role == ROLE

  def orgOfferedMentorRole(self):
    """Indicate whether or not the organization has offered a mentor role.

    Returns:
      True if the organization has opted for a mentor role.
    """
    return self.org_role == MENTOR_ROLE

  def orgOfferedOrgAdminRole(self):
    """Indicate whether or not the organization has offered an organization
    administrator role.

    Returns:
      True if the organization has opted for an organization
      administrator role.
    """
    return self.org_role == ORG_ADMIN_ROLE

  @staticmethod
  def allFields():
    """Returns a list of all names of fields in this model.
    """
    return ['user_role', 'org_role', 'organization', 'created_on']

  def keyName(self):
    """Returns a string which uniquely represents the entity.
    """
    return '/'.join([self.parent_key().name(), str(self.key().id())])

  def getRole(self):
    """Returns the assigned role from the org admin's perspective because it
    offers more information than the user's role.
    """
    if self.org_role == MENTOR_ROLE:
      return 'Mentor'
    elif self.org_role == ORG_ADMIN_ROLE:
      return 'Org Admin'
    else:
      return 'No Role' 


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
  org_role = db.StringProperty(choices=(MENTOR_ROLE, ORG_ADMIN_ROLE))

  #: UUID for the object to be included in a url.
  token = db.StringProperty()

  #: Date until which this object is considered "valid" and can be used to
  #: enroll as a mentor/admin for an organization. This will likely be a
  #: week, based on the implementation in melange.logic.connection.
  expiration_date = db.DateTimeProperty()

  #: Email address representing the user for which the AnonymousConnection
  #: was created.
  email = db.EmailProperty()

  def getRole(self):
    """Returns the assigned role as a more meaningful string."""
    if self.org_role == MENTOR_ROLE:
      return 'Mentor'
    elif self.org_role == ORG_ADMIN_ROLE:
      return 'Org Admin'
    else:
      return 'No Role'


class ConnectionMessage(db.Model):
  """Model of a message that may be sent along with or in response to
  connections.

  Parent:
    soc.models.connection.Connection
  """

  #: A required many:1 relationship with a comment entity indicating
  #: the user who provided that comment.
  author = db.ReferenceProperty(
      reference_class=Profile, required=False,
      collection_name="connection_commented")

  #: The rich textual content of this comment
  content = db.TextProperty(verbose_name=ugettext('Content'))

  #: Date when the comment was added
  created = db.DateTimeProperty(auto_now_add=True)

  #: Whether or not the message was generated programatically
  is_auto_generated = db.BooleanProperty(default=False)

  def getAuthor(self):
    if self.is_auto_generated:
      return "Automatically Generated"
    else:
      return self.author.name()

  def getAuthorId(self):
    if self.is_auto_generated:
      return ""
    else:
      return self.author.link_id
