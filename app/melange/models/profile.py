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

"""This module contains the profile related models."""

from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop

from protorpc import messages

from melange.appengine import db
from melange.models import address as address_model
from melange.models import contact as contact_model
from melange.models import education as education_model


class TeeStyle(messages.Enum):
  """Class that enumerates possible styles for T-Shirts."""
  #: Female style T-Shirt.
  FEMALE = 1
  #: Male style T-Shirt.
  MALE = 2
  #: The user opts not to receive any T-shirts.
  NO_TEE = 3


class TeeSize(messages.Enum):
  """Class that enumerates possible sizes for T-Shirts."""
  #: XXS size.
  XXS = 1
  #: XS size.
  XS = 2
  #: S size.
  S = 3
  #: M size.
  M = 4
  #: L size.
  L = 5
  #: XL size.
  XL = 6
  #: XXL size.
  XXL = 7
  #: XXXL size.
  XXXL = 8
  #: The user opts not to receive any T-shirts.
  NO_TEE = 9


class Gender(messages.Enum):
  """Class that enumerates possible gender choices."""
  #: Female gender.
  FEMALE = 1
  #: Male gender.
  MALE = 2
  #: Other gender.
  OTHER = 3
  #: The user does not disclose their gender.
  NOT_DISCLOSED = 4


class Status(messages.Enum):
  """Class that enumerates possible statuses of profiles."""
  #: The profile is active and participates in the program.
  ACTIVE = 1
  #: The profile has been expelled from the program by program administrators.
  BANNED = 2


class StudentData(ndb.Model):
  """Model that represents student information to be associated with
  the specified profile.
  """
  #: Education information of the student.
  education = ndb.StructuredProperty(education_model.Education, required=True)

  #: Number of proposals which have been submitted by the student.
  number_of_proposals = ndb.IntegerProperty(required=True, default=0)

  #: Number of projects which have been assigned to the student.
  #: Note that right now at most one project per student is supported.
  number_of_projects = ndb.IntegerProperty(required=True, default=0)

  #: Total number of project evaluations that have been passed by the student
  #: for all the projects that have been assigned to him or her.
  number_of_passed_evaluations = ndb.IntegerProperty(required=True, default=0)

  #: Total number of project evaluations that have been failed by the student
  #: for all the projects that have been assigned to him or her.
  number_of_failed_evaluations = ndb.IntegerProperty(required=True, default=0)

  #: List of organizations for which the student have been assigned a project.
  project_for_orgs = ndb.KeyProperty(repeated=True)

  #: Property pointing to the Blob storing student's tax form.
  tax_form = ndb.BlobKeyProperty()

  #: Property pointing to the Blob storing student's enrollment form.
  enrollment_form = ndb.BlobKeyProperty()

  #: Property telling whether the enrollment form is verified by
  #: a program administrator.
  is_enrollment_form_verified = ndb.BooleanProperty(default=False)

  #: Number of tasks completed by the student.
  number_of_completed_tasks = ndb.IntegerProperty(required=True, default=0)

  #: Property telling whether the student has completed at least one task.
  completed_task = ndb.ComputedProperty(
      lambda self: bool(self.number_of_completed_tasks))

  #: Property pointing to the Blob storing student's parental consent form.
  consent_form = ndb.BlobKeyProperty()

  #: Property telling whether the consent form is verified by
  #: a program administrator.
  is_consent_form_verified = ndb.BooleanProperty(default=False)

  #: Organization for which the student is a winner.
  winner_for = ndb.KeyProperty()

  #: Property telling thether the student is a winner of the program.
  is_winner = ndb.ComputedProperty(lambda self: self.winner_for is not None)


class Profile(ndb.Model):
  """Model that represents profile that is registered on per-program basis
  for a user.

  Parent:
    melange.models.user.User
  """
  #: A reference to program entity to which the profile corresponds.
  #: Each profile is created for exactly one program. If the same
  #: user participates in more of them, a separate profile must be created
  #: for each.
  program = ndb.KeyProperty(required=True)

  #: Required field storing a name that is to be displayed publicly.
  # Can be a real name or a nick name or some other public alias.
  # Public names can be any valid UTF-8 text.
  public_name = ndb.StringProperty(required=True)

  #: Required field storing first name of the profile. Can only be ASCII,
  #: not UTF-8 text, because it may be used as a shipping address
  #: and such characters may not be printable.
  first_name = ndb.StringProperty(required=True)

  #: Required field storing last name of the profile. Can only be ASCII,
  #: not UTF-8 text, because it may be used as a shipping address
  #: and such characters may not be printable.
  last_name = ndb.StringProperty(required=True)

  #: Optional field storing a URL to an image, for example a personal photo
  #: or a cartoon avatar. May be displayed publicly.
  photo_url = ndb.StringProperty(validator=db.link_validator)

  #: Contact options to the profile.
  contact = ndb.LocalStructuredProperty(
      contact_model.Contact, default=contact_model.Contact())

  #: Residential address of the registered profile. It is assumed that
  #: the person resides at this address.
  residential_address = ndb.StructuredProperty(
      address_model.Address, required=True)

  #: Shipping address of the registered profile. All possible program related
  #: packages will be sent to this address.
  shipping_address = ndb.StructuredProperty(address_model.Address)

  #: Birth date of the registered profile.
  birth_date = ndb.DateProperty(required=True)

  #: Field storing chosen T-Shirt style.
  tee_style = msgprop.EnumProperty(TeeStyle)

  #: Field storing chosen T-Shirt size.
  tee_size = msgprop.EnumProperty(TeeSize)

  #: Field storing gender of the registered profile.
  gender = msgprop.EnumProperty(Gender)

  #: Field storing answers to the question how the registered profile heard
  #: about the program.
  program_knowledge = ndb.TextProperty()

  #: Field storing student specific information which is relevant and set only
  #: if the registered profile has a student role for the program.
  student_data = ndb.StructuredProperty(StudentData)

  #: Field storing whether the registered profile has
  #: a student role for the program
  is_student = ndb.ComputedProperty(lambda self: bool(self.student_data))

  #: Field storing keys of organizations for which the registered profile
  #: has a mentor role.
  #: This information is also stored in a connection entity between the
  #: specified organization and this profile.
  mentor_for = ndb.KeyProperty(repeated=True)

  #: Field storing whether the registered profile has a mentor
  #: role for at least one organization in the program.
  is_mentor = ndb.ComputedProperty(lambda self: bool(self.mentor_for))

  #: Field storing keys of organizations for which the registered profile
  #: has an organization administrator role.
  #: This information is also stored in a connection entity between the
  #: specified organization and this profile.
  #: Please note that organization administrator is considered a mentor as well.
  #: Therefore, each key, which is present in this field, can be also found
  #: in mentor_for field.
  admin_for = ndb.KeyProperty(repeated=True)

  #: Field storing whether the registered profile has an organization
  #: administrator role for at least one organization in the program.
  is_admin = ndb.ComputedProperty(lambda self: bool(self.admin_for))

  #: Field storing the status of the registered profile.
  status = msgprop.EnumProperty(Status, default=Status.ACTIVE)

  #: Field storing keys of Terms Of Service documents that have been accepted
  #: by the registered profile.
  accepted_tos = ndb.KeyProperty(repeated=True)

  @property
  def profile_id(self):
    """Unique identifier of the registered profile on per program basis.

    It is the same as the identifier of the underlying user entity. It means
    that all profiles for the same user for different programs hold
    the same identifier.

    May be displayed publicly and used as parts of various URLs that are
    specific to this profile.
    """
    return self.key.parent().id()

  @property
  def legal_name(self):
    """Full, legal name associated with the profile."""
    return '%s %s' % (self.first_name, self.last_name)

  @property
  def ship_to_address(self):
    """Address to which all program packages should be shipped."""
    if self.shipping_address:
      address = address_model.Address(**self.shipping_address.to_dict())
      if not address.name:
        address.name = self.legal_name
    else:
      address = address_model.Address(**self.residential_address.to_dict())
      address.name = self.legal_name
    return address


def getSponsorId(profile_key):
  """Returns sponsor ID based on the specified profile key.

  Args:
    profile_key: Profile key.

  Returns:
    A string that represents sponsor ID.
  """
  if isinstance(profile_key, ndb.Key):
    return profile_key.id().split('/')[0]
  else:
    return profile_key.name().split('/')[0]


def getProgramId(profile_key):
  """Returns program ID based on the specified profile key.

  Args:
    profile_key: Profile key.

  Returns:
    A string that represents program ID.
  """
  if isinstance(profile_key, ndb.Key):
    return profile_key.id().split('/')[1]
  else:
    return profile_key.name().split('/')[1]


def getUserId(profile_key):
  """Returns user ID based on the specified profile key.

  Args:
    profile_key: Profile key.

  Returns:
    A string that represents user ID.
  """
  if isinstance(profile_key, ndb.Key):
    return profile_key.id().split('/')[2]
  else:
    return profile_key.name().split('/')[2]
