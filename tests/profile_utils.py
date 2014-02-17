# Copyright 2010 the Melange authors.
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

"""Utils for manipulating profile data."""

import datetime
import os

from google.appengine.ext import ndb

from datetime import timedelta

from melange.models import address as address_model
from melange.models import connection as connection_model
from melange.models import contact as contact_model
from melange.models import education as education_model
from melange.models import profile as ndb_profile_model
from melange.models import user as ndb_user_model

from soc.models import user as user_model

from soc.modules.gci.models import profile as gci_profile_model
from soc.modules.seeder.logic.providers import string as string_provider
from soc.modules.seeder.logic.providers import user as user_provider
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from summerofcode.models import profile as soc_profile_model

from tests import forms_to_submit_utils
from tests import task_utils
from tests.utils import connection_utils


DEFAULT_EMAIL = 'test@example.com'

DEFAULT_MAX_AGE = 100
DEFAULT_MIN_AGE = 0

def generateEligibleStudentBirthDate(program):
  min_age = program.student_min_age or DEFAULT_MIN_AGE
  max_age = program.student_max_age or DEFAULT_MAX_AGE
  eligible_age = min_age + max_age / 2
  return datetime.datetime.date(
      datetime.datetime.today() - timedelta(days=eligible_age * 365))


def login(user):
  """Logs in the specified user by setting 'USER_EMAIL' and 'USER_ID'
  environmental variables.

  Args:
    user: user entity.
  """
  signInToGoogleAccount(user.account.email(), user.account.user_id())


# TODO(daniel): Change name to login and remove the function above
def loginNDB(user, is_admin=False):
  """Logs in the specified user by setting 'USER_ID' environmental variables.

  Args:
    user: user entity.
    is_admin: A bool specifying whether the user is an administrator
      of the application or not.
  """
  os.environ['USER_ID'] = user.account_id
  os.environ['USER_IS_ADMIN'] = '1' if is_admin else '0'


def logout():
  """Logs out the current user by clearing the 'USER_EMAIL'
  and 'USER_ID' environment variables.
  """
  del os.environ['USER_EMAIL']
  del os.environ['USER_ID']


def signInToGoogleAccount(email, user_id=None):
  """Signs in an email address for the account that is logged in by setting
  'USER_EMAIL' and 'USER_ID' environmental variables.

  The Google account associated with the specified email will be considered
  currently logged in, after this function terminates.

  Args:
    email: the user email as a string, e.g.: 'test@example.com'
    user_id: the user id as a string
  """
  os.environ['USER_EMAIL'] = email
  os.environ['USER_ID'] = user_id or ''


def seedUser(email=None, **kwargs):
  """Seeds a new user.

  Args:
    email: email address specifying
    kwargs: initial values for instance's properties, as keyword arguments.

  Returns:
    A newly seeded User entity.
  """
  properties = {'status': 'valid', 'is_developer': False}

  if email is not None:
    properties['account'] = user_provider.FixedUserProvider(value=email)
  else:
    properties['account'] = user_provider.RandomUserProvider()

  properties.update(**kwargs)
  user = seeder_logic.seed(user_model.User, properties=properties)

  # this is tricky - AppEngine SDK sets user_id for user's account
  # only after it is retrieved from datastore for the first time
  user = user_model.User.get(user.key())
  user.user_id = user.account.user_id()
  user.put()

  return user


# TODO(daniel): Change name to seedUser and remove the function above
def seedNDBUser(user_id=None, host_for=None, **kwargs):
  """Seeds a new user.

  Args:
    user_id: Identifier of the new user.
    host_for: List of programs for which the seeded user is a host.

  Returns:
    Newly seeded User entity.
  """
  user_id = user_id or string_provider.UniqueIDProvider().getValue()

  host_for = host_for or []
  host_for = [ndb.Key.from_old_key(program.key()) for program in host_for]

  properties = {
      'account_id': string_provider.UniqueIDProvider().getValue(),
      'host_for': host_for,
      }
  properties.update(**kwargs)

  user = ndb_user_model.User(id=user_id, **properties)
  user.put()

  return user


TEST_PUBLIC_NAME = 'Public Name'
TEST_FIRST_NAME = 'First'
TEST_LAST_NAME = 'Last'
TEST_STREET = 'Street'
TEST_CITY = 'City'
TEST_COUNTRY = 'United States'
TEST_POSTAL_CODE = '90000'
TEST_PROVINCE = 'California'

def seedNDBProfile(program_key, model=ndb_profile_model.Profile,
    user=None, mentor_for=None, admin_for=None, **kwargs):
  """Seeds a new profile.

  Args:
    program_key: Program key for which the profile is seeded.
    model: Model class of which a new profile should be seeded.
    user: User entity corresponding to the profile.
    mentor_for: List of organizations keys for which the profile should be
      registered as a mentor.
    admin_for: List of organizations keys for which the profile should be
      registered as organization administrator.

  Returns:
    A newly seeded Profile entity.
  """
  user = user or seedNDBUser()

  mentor_for = mentor_for or []
  admin_for = admin_for or []

  residential_address = address_model.Address(
      street=TEST_STREET, city=TEST_CITY, province=TEST_PROVINCE,
      country=TEST_COUNTRY, postal_code=TEST_POSTAL_CODE)

  properties = {'email': '%s@example.com' % user.user_id}
  contact_properties = dict(
     (k, v) for k, v in kwargs.iteritems()
         if k in contact_model.Contact._properties)
  properties.update(**contact_properties)
  contact = contact_model.Contact(**properties)

  properties = {
      'program': ndb.Key.from_old_key(program_key),
      'status': ndb_profile_model.Status.ACTIVE,
      'public_name': TEST_PUBLIC_NAME,
      'first_name': TEST_FIRST_NAME,
      'last_name': TEST_LAST_NAME,
      'birth_date': datetime.date(1990, 1, 1),
      'residential_address': residential_address,
      'tee_style': ndb_profile_model.TeeStyle.MALE,
      'tee_size': ndb_profile_model.TeeSize.M,
      'mentor_for': list(set(mentor_for + admin_for)),
      'admin_for': admin_for,
      'contact': contact,
      }
  properties.update(**kwargs)
  profile = model(id='%s/%s' % (program_key.name(), user.key.id()),
      parent=user.key, **properties)
  profile.put()

  org_keys = list(set(mentor_for + admin_for))
  for org_key in org_keys:
    if org_key in admin_for:
      org_role = connection_model.ORG_ADMIN_ROLE
    else:
      org_role = connection_model.MENTOR_ROLE

    connection_properties = {
        'user_role': connection_model.ROLE,
        'org_role': org_role
        }

    # TODO(daniel): remove when all organizations are converted
    if not isinstance(org_key, ndb.Key):
      org_key = ndb.Key.from_old_key(org_key)
    connection_utils.seed_new_connection(
        profile.key, org_key, **connection_properties)

  return profile


_TEST_SCHOOL_NAME = 'United States'
_TEST_SCHOOL_ID = 'Melange University'
_TEST_EXPECTED_GRADUATION = datetime.date.today().year + 1

def _seedEducation():
  """Seeds a new education."""
  return education_model.Education(
      school_country=_TEST_SCHOOL_NAME, school_id=_TEST_SCHOOL_ID,
      expected_graduation=_TEST_EXPECTED_GRADUATION)


def seedStudentData(model=ndb_profile_model.StudentData, **kwargs):
  """Seeds a new student data.

  Args:
    model: Model class of which a new student data should be seeded.

  Returns:
    A newly seeded student data entity.
  """
  properties = {'education': _seedEducation()}
  properties.update(**kwargs)
  return model(**properties)





def seedNDBStudent(program, student_data_model=ndb_profile_model.StudentData,
    student_data_properties=None, user=None, **kwargs):
  """Seeds a new profile who is registered as a student.

  Args:
    program: Program entity for which the profile is seeded.
    student_data_model: Model of which a new student data should be seeded.
    student_data_properties: Optional properties of the student data to seed.
    user: User entity corresponding to the profile.

  Returns:
    A newly seeded Profile entity.
  """
  profile = seedNDBProfile(program.key(), user=user, **kwargs)

  student_data_properties = student_data_properties or {}
  profile.student_data = seedStudentData(
      model=student_data_model, **student_data_properties)
  profile.put()
  return profile


def seedSOCStudent(program, user=None, **kwargs):
  """Seeds a new profile who is registered as a student for Summer Of Code.

  Args:
    program: Program entity for which the profile is seeded.
    user: User entity corresponding to the profile.

  Returns:
    A newly seeded Profile entity.
  """
  return seedNDBStudent(
      program, student_data_model=soc_profile_model.SOCStudentData,
      user=user, **kwargs)


class ProfileHelper(object):
  """Helper class to aid in manipulating profile data.
  """

  def __init__(self, program, dev_test):
    """Initializes the ProfileHelper.

    Args:
      program: a program
      dev_test: if set, always creates users as developers
    """
    self.program = program
    self.user = None
    self.profile = None
    self.connection = None
    self.dev_test = dev_test

  def seed(self, model, properties,
           auto_seed_optional_properties=True):
    return seeder_logic.seed(model, properties, recurse=False,
        auto_seed_optional_properties=auto_seed_optional_properties)

  def seedn(self, model, properties, n,
            auto_seed_optional_properties=True):
    return seeder_logic.seedn(model, n, properties, recurse=False,
        auto_seed_optional_properties=auto_seed_optional_properties)


class GSoCProfileHelper(ProfileHelper):
  """Helper class to aid in manipulating GSoC profile data.
  """

  def __init__(self, program, dev_test):
    """Initializes the GSocProfileHelper.

    Args:
      program: a GSoCProgram
      dev_test: if set, always creates users as developers
    """
    super(GSoCProfileHelper, self).__init__(program, dev_test)


class GCIProfileHelper(ProfileHelper):
  """Helper class to aid in manipulating GCI profile data.
  """

  def __init__(self, program, dev_test):
    """Initializes the GSocProfileHelper.

    Args:
      program: a GCIProgram
      dev_test: if set, always creates users as developers
    """
    super(GCIProfileHelper, self).__init__(program, dev_test)
