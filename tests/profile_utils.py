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

from google.appengine.ext import db
from google.appengine.ext import ndb

from datetime import timedelta

from melange.models import address as address_model
from melange.models import connection as connection_model
from melange.models import contact as contact_model
from melange.models import education as education_model
from melange.models import profile as ndb_profile_model
from melange.models import user as ndb_user_model

from soc.models import profile as profile_model
from soc.models import user as user_model

from soc.modules.gci.models import profile as gci_profile_model
from soc.modules.gsoc.models import profile as gsoc_profile_model
from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.seeder.logic.providers import string as string_provider
from soc.modules.seeder.logic.providers import user as user_provider
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from summerofcode.models import profile as soc_profile_model

from tests import forms_to_submit_utils
from tests import task_utils
from tests.utils import connection_utils
from tests.utils import seed_utils

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
  if is_admin:
    os.environ['USER_IS_ADMIN'] = '1'
  else:
    os.environ['USER_IS_ADMIN'] = '0'


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

  def createUser(self):
    """Creates a user entity for the current user.
    """
    if self.user:
      return self.user

    email = os.environ['USER_EMAIL']

    self.user = seedUser(email=email, is_developer=self.dev_test)
    return self.user

  def createOtherUser(self, email):
    """Creates a user entity for the specified email.
    """
    # TODO(daniel): does it really should override self.user state??
    self.user = seedUser(email=email)
    return self

  def deleteProfile(self):
    """Deletes the created profile.
    """
    if not self.profile:
      return self

    if self.profile.student_info:
      self.profile.student_info.delete()
    self.profile.delete()
    self.profile = None

    return self

  def createProfile(self):
    """Creates a profile for the current user.
    """
    pass

  def createStudent(self):
    """Sets the current user to be a student for the current program.
    """
    pass

  def removeStudent(self):
    """Removes the student profile from the current user.
    """
    if not self.profile:
      return self
    if self.profile.student_info:
      self.profile.student_info.delete()
      self.profile.student_info = None
      self.profile.put()
    return self.profile

  def removeHost(self):
    """Removes the host profile from the current user.
    """
    if not self.user:
      return self
    self.user.host_for = []
    self.user.put()
    return self.user

  def removeOrgAdmin(self):
    """Removes the org admin profile from the current user.
    """
    if not self.profile:
      return self
    self.profile.mentor_for = []
    self.profile.org_admin_for = []
    self.profile.is_mentor = False
    self.profile.is_org_admin = False
    self.profile.put()
    return self.profile

  def removeMentor(self):
    """Removes the mentor profile from the current user.
    """
    if not self.profile:
      return self
    self.profile.mentor_for = []
    self.profile.is_mentor = False
    self.profile.put()
    return self.profile

  def removeAllRoles(self):
    """Removes all profile roles from the current user excluding host.
    """
    if not self.profile:
      return self
    self.removeMentor()
    self.removeOrgAdmin()
    self.removeStudent()
    return self.profile

  def clear(self):
    if self.profile and self.profile.student_info:
      self.profile.student_info.delete()
    if self.profile:
      self.profile.delete()
    if self.user:
      self.user.delete()
    self.profile = None
    self.user = None


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

  def createProfile(self):
    """Creates a profile for the current user.
    """
    if self.profile:
      return self.profile

    user = seedNDBUser()
    self.profile = seedNDBProfile(self.program.key(), user=user)
    return self.profile

  def createNDBProfile(self):
    """Creates a profile for the current user."""
    if self.profile:
      return self.profile

    user = seedNDBUser()
    loginNDB(user)
    self.profile = seedNDBProfile(self.program.key(), user=user)

    return self.profile

  def createOrgAdmin(self, org):
    """Creates an Organization Administrator profile for the current user.

    Args:
      org: organization entity.

    Returns:
      the current profile entity.
    """
    user = seedNDBUser()
    loginNDB(user)
    self.profile = seedNDBProfile(
        self.program.key(), user=user, admin_for=[org.key])

    return self.profile

  def createMentor(self, org):
    """Creates an Organization Administrator profile for the current user.

    Args:
      org: organization entity.

    Returns:
      the current profile entity.
    """
    user = seedNDBUser()
    loginNDB(user)
    self.profile = seedNDBProfile(
        self.program.key(), user=user, mentor_for=[org.key])

    return self.profile

  def notificationSettings(
      self, new_requests=False, request_handled=False,
      new_proposals=False, proposal_updates=False,
      public_comments=False, private_comments=False):
    self.createProfile()
    self.profile.notify_new_requests = new_requests
    self.profile.notify_request_handled = request_handled
    self.profile.notify_new_proposals = new_proposals
    self.profile.notify_proposal_updates = proposal_updates
    self.profile.notify_public_comments = public_comments
    self.profile.notify_private_comments = private_comments
    self.profile.put()

  def createStudent(self):
    """Sets the current user to be a student for the current program.
    """
    if self.profile:
      return self.profile

    user = seedNDBUser()
    self.profile = seedSOCStudent(
        self.program, birth_date=generateEligibleStudentBirthDate(self.program),
        user=user)
    return self.profile

  def createNDBStudent(self):
    """Sets the current user to be a student for the current program."""
    user = seedNDBUser()
    loginNDB(user)
    self.profile = seedSOCStudent(self.program, user=user)
    return self.profile

  def createStudentWithProposal(self, org, mentor):
    """Sets the current user to be a student with a proposal for the
    current program.
    """
    return self.createStudentWithProposals(org, mentor, 1)

  def createStudentWithProposals(self, org, mentor, n):
    """Sets the current user to be a student with specified number of
    proposals for the current program.
    """
    self.createStudent()
    self.profile.student_info.number_of_proposals = n
    self.profile.put()
    self.profile.student_info.put()
    properties = {
        'scope': self.profile, 'score': 0, 'nr_scores': 0,
        'is_publicly_visible': False, 'accept_as_project': False,
        'is_editable_post_deadline': False, 'extra': None,
        'parent': self.profile, 'status': 'pending', 'has_mentor': True,
        'program': self.program, 'org': org.key.to_old_key(), 'mentor': mentor
    }
    self.seedn(proposal_model.GSoCProposal, properties, n)
    return self.profile

  def createStudentWithProject(self, org, mentor):
    """Sets the current user to be a student with a project for the
    current program.
    """
    return self.createStudentWithProjects(org, mentor, 1)

  def createStudentWithProjects(self, org, mentor, n):
    """Sets the current user to be a student with specified number of
    projects for the current program.
    """
    student = seedSOCStudent(self.program, user=seedNDBUser())
    mentor = seed_utils.seedNDBProfile(
        self.program.key(), seedNDBUser(), mentor_for=[org.key])

    proposal = seed_utils.seedProposal(
        student.key, self.program.key(), org.key, mentor.key)
    seed_utils.seedProject(
        student, self.program.key(), proposal.key(), org.key, mentor.key)

    self.profile = student
    return self.profile

  def createMentorWithProject(self, org, student):
    """Creates an mentor profile with a project for the current user."""
    self.createMentor(org)
    proposal = proposal_model.GSoCProposal.all().ancestor(student).get()

    properties = {'mentors': [self.profile.key()], 'program': self.program,
                  'parent': student, 'org': org.key.to_old_key(),
                  'status': 'accepted', 'proposal': proposal}
    self.seed(project_model.GSoCProject, properties)
    return self.profile

  def createConnection(self, org):
    self.createProfile()
    self.connection = connection_utils.seed_new_connection(
        ndb.Key.from_old_key(self.profile.key()), org.key)
    return self.connection


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

  def createHost(self):
    """Sets the current user to be a host for the current program."""
    self.createUser()
    self.user.host_for = [self.program.scope.key()]
    self.user.put()
    return self.user

  def createProfile(self):
    """Creates a profile for the current user."""
    if self.profile:
      return
    user = self.createUser()
    properties = {
        'link_id': user.link_id, 'student_info': None, 'user': user,
        'parent': user, 'scope': self.program, 'status': 'active',
        'email': self.user.account.email(), 'program': self.program,
        'mentor_for': [], 'org_admin_for': [],
        'is_org_admin': False, 'is_mentor': False, 'is_student': False
    }
    self.profile = self.seed(gci_profile_model.GCIProfile, properties)
    return self.profile

  def createOrgAdmin(self, org):
    """Creates an Organization Administrator profile for the current user.

    Args:
      org: organization entity.

    Returns:
      the current profile entity.
    """
    self.createProfile()
    self.profile.mentor_for = [org.key()]
    self.profile.org_admin_for = [org.key()]
    self.profile.is_mentor = True
    self.profile.is_org_admin = True
    self.profile.put()

    connection_properties = {
        'user_role': connection_model.ROLE,
        'org_role': connection_model.ORG_ADMIN_ROLE
        }
    connection_utils.seed_new_connection(
        ndb.Key.from_old_key(self.profile.key()),
        ndb.Key.from_old_key(org.key()), **connection_properties)

    return self.profile

  def createMentor(self, org):
    """Creates a Mentor profile for the current user.

    Args:
      org: organization entity.

    Returns:
      the current profile entity.
    """
    self.createProfile()
    self.profile.mentor_for = [org.key()]
    self.profile.is_mentor = True
    self.profile.put()

    connection_properties = {
        'user_role': connection_model.ROLE,
        'org_role': connection_model.MENTOR_ROLE
        }
    connection_utils.seed_new_connection(
        ndb.Key.from_old_key(self.profile.key()),
        ndb.Key.from_old_key(org.key()), **connection_properties)

    return self.profile

  def notificationSettings(
      self, new_requests=False, request_handled=False, comments=False):
    self.createProfile()
    self.profile.notify_new_requests = new_requests
    self.profile.notify_request_handled = request_handled
    self.profile.notify_comments = comments
    self.profile.put()

  def createStudent(self, **kwargs):
    """Sets the current user to be a student for the current program."""
    self.createProfile()

    properties = {
        'key_name': self.profile.key().name(),
        'parent': self.profile,
        'school': None,
        'number_of_completed_tasks': 0,
        'program': self.program,
        'is_winner': False,
        'winner_for': None
    }
    properties.update(kwargs)

    self.profile.student_info = self.seed(
        gci_profile_model.GCIStudentInfo, properties)
    self.profile.is_student = True
    self.profile.put()
    return self.profile

  def createStudentWithTask(self, status, org, mentor):
    """Sets the current user to be a student with a task for the
    current program.
    """
    return self.createStudentWithTasks(status, org, mentor, 1)[0]

  def createStudentWithTasks(self, status, org, mentor, n=1):
    """Sets the current user to be a student with specified number of
    tasks for the current program.
    """
    student = self.createStudent()
    student.student_info.put()
    tasks = []
    for _ in xrange(n):
      task = task_utils.seedTask(
          self.program, org, [mentor.key()], student=student, status=status)
      tasks.append(task)
    return tasks

  def createStudentWithConsentForms(self, status='active', consent_form=False,
      student_id_form=False):
    """Creates a student who might have submitted consent forms required
    by the program Terms of Service.
    """
    forms_helper = forms_to_submit_utils.FormsToSubmitHelper()

    properties = {}
    if consent_form:
      properties['consent_form'] = forms_helper.createBlobStoreForm()
    if student_id_form:
      properties['student_id_form'] = forms_helper.createBlobStoreForm()

    return self.createStudent(**properties)

  def createMentorWithTask(self, status, org):
    """Creates an mentor profile with a task for the current user.
    """
    return self.createMentorWithTasks(status, org, 1)[0]

  def createMentorWithTasks(self, status, org, n=1):
    """Creates an mentor profile with a task for the current user.
    """
    mentor = self.createMentor(org)
    tasks = []
    for _ in xrange(n):
      task = task_utils.seedTask(
          self.program, org, [mentor.key()], status=status)
      tasks.append(task)
    return tasks
