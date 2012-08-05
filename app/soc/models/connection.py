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
from google.appengine.ext import db
from soc.models.organization import Organization
from soc.models.profile import Profile


class Connection(db.Model):
  """ Connection model.
  This model is intended to be used to represent either an invitation or 
  request between a User and an Organization. The type of role to be granted
  to the user is determined by the four states: user_mentor, user_org_admin,
  org_mentor, and org_org_admin, which correspond to the respective party's
  acceptance of a given role. 

  Parent: soc.models.user.User (also parent of self.profile here)
  """
  
  # For each of the next four properties, None represents Pending, True
  # is an acceptance and False is a rejection of a role.
  
  # The User's state in respect to a mentoring role.
  user_mentor = db.BooleanProperty(default=None)
  
  # The User's state in respect to an org admin role.
  user_org_admin = db.BooleanProperty(default=None)
  
  # An org's state in respect to a mentoring role for the user.
  org_mentor = db.BooleanProperty(default=None)
  
  # An org's state in respect to an org admin role for the user.
  org_org_admin = db.BooleanProperty(default=None)
  
  # The organization entity involved in the connection for which a user
  # may gain heightened privileges.
  organization = db.ReferenceProperty(Organization, 
      required=True,
      collection_name='connections')
                                     
  # The profile of the User who has either requested or been invited to either
  # a mentor or org admin role.
  profile = db.ReferenceProperty(Profile,
      required=True,
      collection_name='connections')
                            
  # A message from the initiating party (user or org admin) to the other.
  message = db.StringProperty()
  
  # Property for the ShowConnection page to keep track of the time that the
  # connection was initiated.
  created_on = db.DateTimeProperty(auto_now_add=True)
  
  def keyName(self):
    """Returns a string which uniquely represents the entity.
    """
    return '/'.join([self.parent_key().name(), str(self.key().id())])

class AnonymousConnection(db.Model):
  """ This model is intended for use as a placeholder Connection for the
  scenario in which an org admin attempts to send an email invitation to
  a person who does not have both a User entity and GSoCProfile. This 
  model is deleted and 'replaced' by an actual Connection object should
  the user decide to register.

  Parent: soc.models.org.Organization
  """

  # A string to designate the role that will be recreated for the actual
  # connection object.
  role = db.StringProperty(choices=['mentor', 'org_admin'])

  # Hash hexdigest() of this object's key objct to save time when validating 
  # when the user registers.
  hash_id = db.StringProperty()
