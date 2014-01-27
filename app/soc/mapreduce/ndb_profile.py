# Copyright 2014 the Melange authors.
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

"""MapReduce scripts that convert profile entities to the new Profile model."""

import logging

from google.appengine.ext import db
from google.appengine.ext import ndb

from melange.models import address as address_model
from melange.models import contact as contact_model
from melange.models import profile as profile_model

# This MapReduce requires these models to have been imported.
# pylint: disable=unused-import
from soc.models.profile import Profile
from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gsoc.models.profile import GSoCProfile
# pylint: enable=unused-import


@ndb.transactional
def _createProfileTxn(new_profile):
  """Persists the specified profile in the datastore."""
  new_profile.put()


def _teeStyleToEnum(profile):
  """Returns enum value for T-Shirt style for the specified profile.

  Args:
    profile: Profile entity.

  Returns:
    Value of profile_model.TeeStyle type corresponding to the T-Shirt style
    or profile_model.TeeStyle.NO_TEE, no T-Shirt style is set.
  """
  if not profile.tshirt_style:
    return profile_model.TeeStyle.NO_TEE
  elif profile.tshirt_style == 'male':
    return profile_model.TeeStyle.MALE
  elif profile.tshirt_style == 'female':
    return profile_model.TeeStyle.FEMALE
  else:
    logging.warning(
        'Unknown T-Shirt style %s for profile %s.',
        profile.tshirt_style, profile.key().name())
    return profile_model.TeeStyle.NO_TEE


def _teeSizeToEnum(profile):
  """Returns enum value for T-Shirt style for the specified profile.

  Args:
    profile: Profile entity.

  Returns:
    Value of profile_model.TeeSize type corresponding to the T-Shirt size
    or profile_model.TeeSize.NO_TEE, no T-Shirt size is set.
  """
  if not profile.tshirt_size:
    return profile_model.TeeSize.NO_TEE
  elif profile.tshirt_size == 'XXS':
    return profile_model.TeeSize.XXS
  elif profile.tshirt_size == 'XS':
    return profile_model.TeeSize.XS
  elif profile.tshirt_size == 'S':
    return profile_model.TeeSize.S
  elif profile.tshirt_size == 'M':
    return profile_model.TeeSize.M
  elif profile.tshirt_size == 'L':
    return profile_model.TeeSize.L
  elif profile.tshirt_size == 'XL':
    return profile_model.TeeSize.XL
  elif profile.tshirt_size == 'XXL':
    return profile_model.TeeSize.XXL
  elif profile.tshirt_size == 'XXXL':
    return profile_model.TeeSize.XXXL
  else:
    logging.warning(
        'Unknown T-Shirt size %s for profile %s.',
        profile.tshirt_size, profile.key().name())
    return profile_model.TeeSize.NO_TEE


def _genderToEnum(profile):
  """Returns enum value for gender for the specified profile.

  Args:
    profile: Profile entity.

  Returns:
    Value of profile_model.Gender type corresponding to the gender
    or profile_model.Gender.NOT_DISCLOSED, no gender is not ser.
  """
  if not profile.gender:
    return profile_model.Gender.NOT_DISCLOSED
  elif profile.gender == 'male':
    return profile_model.Gender.MALE
  elif profile.gender == 'female':
    return profile_model.Gender.FEMALE
  elif profile.gender == 'other':
    return profile_model.Gender.OTHER
  else:
    logging.warning(
        'Unknown gender %s for profile %s.',
        profile.gender, profile.key().name())
    return profile_model.Gender.NOT_DISCLOSED


def _statusToEnum(profile):
  """Returns enum value for status for the specified profile.

  Args:
    profile: Profile entity.

  Returns:
    Value of profile_model.Status type corresponding to the status.
  """
  if not profile.status or profile.status == 'active':
    return profile_model.Status.ACTIVE
  elif profile.status == 'invalid':
    return profile_model.Status.BANNED
  else:
    logging.warning(
        'Unknown status %s for profile %s.',
        profile.status, profile.key().name())
    return profile_model.Status.ACTIVE


def _getStudentData(profile):
  """Gets student data for the specified profile.

  Args:
    profile: Profile entity.

  Returns:
    Instance of profile_model.StudentData if the specified profile is a student
    or None otherwise.
  """
  if not profile.student_info:
    return None
  else:
    # TODO(daniel): implement this function
    return profile_model.StudentData()


def convertProfile(profile_key):
  """Converts the specified profile by creating a new user entity that inherits
  from the newly added NDB model.

  Args:
    profile: Profile key.
  """
  profile = db.get(profile_key)

  program = ndb.Key.from_old_key(
      Profile.program.get_value_for_datastore(profile))
  public_name = profile.public_name
  first_name = profile.given_name
  last_name = profile.surname
  photo_url = profile.photo_url

  # create contact for profile
  email = profile.email
  web_page = profile.home_page
  blog = profile.blog
  phone = profile.phone
  contact = contact_model.Contact(
      email=email, web_page=web_page, blog=blog, phone=phone)

  # create residential address
  name = profile.full_name()
  street = profile.res_street
  street_extra = profile.res_street_extra
  city = profile.res_city
  province = profile.res_state
  country = profile.res_country
  postal_code = profile.res_postalcode
  residential_address = address_model.Address(
      name=name, street=street, street_extra=street_extra, city=city,
      province=province, country=country, postal_code=postal_code)

  # create shipping address
  if (profile.ship_street and profile.ship_city and profile.ship_country and
      profile.ship_postalcode):
    name = profile.ship_name or profile.full_name()
    street = profile.ship_street
    street_extra = profile.ship_street_extra
    city = profile.ship_city
    province = profile.ship_state
    country = profile.ship_country
    postal_code = profile.ship_postal_code
    shipping_address = address_model.Address(
        name=name, street=street, street_extra=street_extra, city=city,
        province=province, country=country, postal_code=postal_code)
  else:
    shipping_address = None

  birth_date = profile.birth_date
  tee_style = _teeStyleToEnum(profile)
  tee_size = _teeSizeToEnum(profile)
  gender = _genderToEnum(profile)
  program_knowledge = profile.program_knowledge

  student_data = _getStudentData(profile)
  mentor_for = set(
      ndb.Key.from_old_key(org_key) for org_key in profile.mentor_for)
  admin_for = set(
      ndb.Key.from_old_key(org_key) for org_key in profile.org_admin_for)

  status = _statusToEnum(profile)

  # TODO(daniel): get value for accepted_tos field

  new_profile = profile_model.Profile(
      program=program, public_name=public_name, first_name=first_name,
      last_name=last_name, photo_url=photo_url, contact=contact,
      residential_address=residential_address,
      shipping_address=shipping_address, birth_date=birth_date,
      tee_style=tee_style, tee_size=tee_size, gender=gender,
      program_knowledge=program_knowledge, student_data=student_data,
      mentor_for=mentor_for, admin_for=admin_for, status=status)

  _createProfileTxn(new_profile)
