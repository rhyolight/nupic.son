# Copyright 2013 the Melange authors.
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

"""This module contains the organization related models."""

from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop

from django.utils import translation

from protorpc import messages

from melange.appengine import db
from melange.models import contact as contact_model

from soc.models import licenses


class Status(messages.Enum):
  """Class that enumerates possible statuses of organizations."""
  #: The organization has been accepted and participates in the program.
  ACCEPTED = 1
  #: The organization has not been accepted into the program.
  REJECTED = 2
  #: The organization has been created and applies to the program.
  APPLYING = 3
  #: Program administrators have decided to accept this organization into
  #: the program. When the decision is final, the status will be changed
  #: to ACCEPTED
  PRE_ACCEPTED = 101
  #: Program administrators have decided not to accept this organization into
  #: the program. When the decision is final, the status will be changed
  #: to REJECTED
  PRE_REJECTED = 102


def getSponsorId(org_key):
  """Returns sponsor ID based on the specified organization key.

  Args:
    org_key: Organization key.

  Returns:
    A string that represents sponsor ID.
  """
  if isinstance(org_key, ndb.Key):
    key_name = org_key.id()
  else:
    key_name = org_key.name()
  return key_name.split('/')[0]


def getProgramId(org_key):
  """Returns program ID based on the specified organization key.

  Args:
    org_key: Organization key.

  Returns:
    A string that represents program ID.
  """
  if isinstance(org_key, ndb.Key):
    key_name = org_key.id()
  else:
    key_name = org_key.name()
  return key_name.split('/')[1]


def getOrgId(org_key):
  """Returns organization ID based on the specified organization key.

  Args:
    org_key: Organization key.

  Returns:
    A string that represents organization ID.
  """
  if isinstance(org_key, ndb.Key):
    key_name = org_key.id()
  else:
    key_name = org_key.name()
  return key_name.split('/')[2]


# TODO(daniel): complete this class
class Organization(ndb.Model):
  """Model that represents an organization."""

  #: Field storing identifier of the organization.
  org_id = ndb.StringProperty(
      required=True,
      verbose_name=translation.ugettext('Organization ID'))

  #: Field storing name of the organization.
  name = ndb.StringProperty(required=True,
      verbose_name=translation.ugettext('Name'))
  name.group = translation.ugettext("1. Public Info")

  #: Description of the organization.
  description = ndb.TextProperty(required=True, indexed=False)

  #: URL to an image with organization logo.
  logo_url = ndb.StringProperty(
      indexed=False, validator=db.link_validator)

  #: Contact channels to the organization.
  contact = ndb.LocalStructuredProperty(
      contact_model.Contact, default=contact_model.Contact())

  #: Field storing a reference to the program in which
  #: the organization participates.
  program = ndb.KeyProperty(required=True)

  #: Status of the organization
  status = msgprop.EnumProperty(
      Status, required=True, default=Status.APPLYING)

  #: Specifies whether the organization has participated in the program before
  is_veteran = ndb.BooleanProperty(required=True, default=False)

  #: Collection of tags that describe the organization.
  tags = ndb.StringProperty(repeated=True)

  #: Main license that is used by the organization.
  license = ndb.StringProperty(choices=licenses.LICENSES)
