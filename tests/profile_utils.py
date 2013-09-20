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


"""Utils for manipulating profile data.
"""

import os

from datetime import datetime
from datetime import timedelta

from melange.models import connection as connection_model

from soc.models import user as user_model
from soc.modules.seeder.logic.providers import user as user_provider
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests.utils import connection_utils


def generate_eligible_student_birth_date(program):
  eligible_age = program.student_min_age + program.student_max_age // 2
  return datetime.date(datetime.today() - timedelta(days=eligible_age * 365))


def login(user):
  """Logs in the specified user by setting 'USER_EMAIL' and 'USER_ID'
  environmental variables.

  Args:
    user: user entity.
  """
  os.environ['USER_EMAIL'] = user.account.email()
  os.environ['USER_ID'] = user.account.user_id() or ''


def logout():
  """Logs out the current user by clearing the 'USER_EMAIL'
  and 'USER_ID' environment variables.
  """
  del os.environ['USER_EMAIL']
  del os.environ['USER_ID']


def seedUser(email=None, **kwargs):
  """Seeds a new user.

  Args:
    email: email address specifying
    kwargs: initial values for instance's properties, as keyword arguments.
  """
  properties = {'status': 'valid'}

  if email is not None:
    properties['account'] = user_provider.FixedUserProvider(value=email)
  else:
    properties['account'] = user_provider.CurrentUserProvider()

  properties.update(**kwargs)
  user = seeder_logic.seed(user_model.User, properties=properties)

  # this is tricky - AppEngine SDK sets user_id for user's account
  # only after it is retrieved from datastore for the first time
  user = user_model.User.get(user.key())
  user.user_id = user.account.user_id()
  user.put()

  return user


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
    self.user = seedUser(is_developer=self.dev_test)
    return self.user

  def createDeveloper(self):
    """Creates a user entity for the current user that is a developer.
    """
    self.createUser()
    self.user.is_developer = True
    self.user.put()
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

  def createHost(self):
    """Sets the current user to be a host for the current program.
    """
    self.createUser()
    self.user.host_for = [self.program.scope.key()]
    self.user.put()
    return self.user

  def removeHost(self):
    """Removes the host profile from the current user.
    """
    if not self.user:
      return self
    self.user.host_for = []
    self.user.put()
    return self.user

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
    connection_utils.seed_new_connection(self.profile, org,
        **connection_properties)

    return self.profile

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
    connection_utils.seed_new_connection(self.profile, org,
        **connection_properties)    

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
    from soc.modules.gsoc.models.profile import GSoCProfile
    user = self.createUser()
    properties = {
        'link_id': user.link_id, 'student_info': None, 'user': user,
        'parent': user, 'scope': self.program, 'status': 'active',
        'email': self.user.account.email(), 'program': self.program,
        'mentor_for': [], 'org_admin_for': [],
        'is_org_admin': False, 'is_mentor': False, 'is_student': False
    }
    self.profile = self.seed(GSoCProfile, properties)
    return self.profile

  def notificationSettings(
      self, new_requests=False, new_invites=False,
      invite_handled=False, request_handled=False,
      new_proposals=False, proposal_updates=False,
      public_comments=False, private_comments=False):
    self.createProfile()
    self.profile.notify_new_requests = new_requests
    self.profile.notify_new_invites = new_invites
    self.profile.notify_invite_handled = invite_handled
    self.profile.notify_request_handled = request_handled
    self.profile.notify_new_proposals = new_proposals
    self.profile.notify_proposal_updates = proposal_updates
    self.profile.notify_public_comments = public_comments
    self.profile.notify_private_comments = private_comments
    self.profile.put()

  def createStudent(self):
    """Sets the current user to be a student for the current program.
    """
    self.createProfile()
    from soc.modules.gsoc.models.profile import GSoCStudentInfo
    properties = {'key_name': self.profile.key().name(), 'parent': self.profile,
        'school': None, 'tax_form': None, 'enrollment_form': None,
        'number_of_projects': 0, 'number_of_proposals': 0,
        'passed_evaluations': 0, 'failed_evaluations': 0,
        'program': self.program,
        'birth_date': generate_eligible_student_birth_date(self.program)}
    self.profile.student_info = self.seed(GSoCStudentInfo, properties)
    self.profile.is_student = True
    self.profile.put()
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
    from soc.modules.gsoc.models.proposal import GSoCProposal
    properties = {
        'scope': self.profile, 'score': 0, 'nr_scores': 0,
        'is_publicly_visible': False, 'accept_as_project': False,
        'is_editable_post_deadline': False, 'extra': None,
        'parent': self.profile, 'status': 'pending', 'has_mentor': True,
        'program': self.program, 'org': org, 'mentor': mentor
    }
    self.seedn(GSoCProposal, properties, n)
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
    student = self.createStudentWithProposal(org, mentor)
    from soc.modules.gsoc.models import proposal as proposal_model
    proposal = proposal_model.GSoCProposal.all().ancestor(student).get()

    student.student_info.number_of_projects = n

    # We add an organization entry for each project even if the projects belong
    # to the same organization, we add the organization multiple times. We do
    # this to make project removal easy.
    student.student_info.project_for_orgs += [org.key()] * n
    student.student_info.put()
    from soc.modules.gsoc.models import project as project_model
    properties = {
        'program': self.program,
        'org': org,
        'status': project_model.STATUS_ACCEPTED,
        'parent': self.profile,
        'mentors': [mentor.key()],
        'proposal': proposal
        }
    self.seedn(project_model.GSoCProject, properties, n)
    return self.profile

  def createMentorWithProject(self, org, student):
    """Creates an mentor profile with a project for the current user.
    """
    self.createMentor(org)
    from soc.modules.gsoc.models.proposal import GSoCProposal
    proposal = GSoCProposal.all().ancestor(student).get()

    from soc.modules.gsoc.models.project import GSoCProject
    properties = {'mentors': [self.profile.key()], 'program': self.program,
                  'parent': student, 'org': org, 'status': 'accepted',
                  'proposal': proposal}
    self.seed(GSoCProject, properties)
    return self.profile
  
  def createConnection(self, org):
    self.connection = connection_utils.seed_new_connection(self.profile, org)
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

  def createProfile(self):
    """Creates a profile for the current user.
    """
    if self.profile:
      return
    from soc.modules.gci.models.profile import GCIProfile
    user = self.createUser()
    properties = {
        'link_id': user.link_id, 'student_info': None, 'user': user,
        'parent': user, 'scope': self.program, 'status': 'active',
        'email': self.user.account.email(), 'program': self.program,
        'mentor_for': [], 'org_admin_for': [],
        'is_org_admin': False, 'is_mentor': False, 'is_student': False
    }
    self.profile = self.seed(GCIProfile, properties)
    return self.profile

  def notificationSettings(
      self, new_requests=False, new_invites=False,
      invite_handled=False, request_handled=False,
      comments=False):
    self.createProfile()
    self.profile.notify_new_requests = new_requests
    self.profile.notify_new_invites = new_invites
    self.profile.notify_invite_handled = invite_handled
    self.profile.notify_request_handled = request_handled
    self.profile.notify_comments = comments
    self.profile.put()

  def createStudent(self, **kwargs):
    """Sets the current user to be a student for the current program.
    """
    from soc.modules.gci.models.profile import GCIStudentInfo

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

    self.profile.student_info = self.seed(GCIStudentInfo, properties)
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
    from tests.gci_task_utils import GCITaskHelper
    student = self.createStudent()
    student.student_info.put()
    gci_task_helper = GCITaskHelper(self.program)
    tasks = []
    for _ in xrange(n):
        task = gci_task_helper.createTask(status, org, mentor, student)
        tasks.append(task)
    return tasks

  def createStudentWithConsentForms(self, status='active', consent_form=False,
      student_id_form=False):
    """Creates a student who might have submitted consent forms required
    by the program Terms of Service.
    """
    from tests.forms_to_submit_utils import FormsToSubmitHelper
    forms_helper = FormsToSubmitHelper()

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
    from tests.gci_task_utils import GCITaskHelper
    self.createMentor(org)
    gci_task_helper = GCITaskHelper(self.program)
    tasks = []
    for _ in xrange(n):
        task = gci_task_helper.createTask(status, org, self.profile)
        tasks.append(task)
    return tasks
