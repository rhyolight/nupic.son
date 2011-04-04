#!/usr/bin/env python2.5
#
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

__authors__ = [
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


from soc.modules.seeder.logic.seeder import logic as seeder_logic


class GSoCProfileHelper(object):
  """Helper class to aid in manipulating profile data.
  """

  def __init__(self, program, dev_test):
    """Initializes the GSocProfileHelper.

    Args:
      program: a GSoCProgram
      dev_test: if set, always creates users as developers
    """
    self.program = program
    self.user = None
    self.profile = None
    self.dev_test = dev_test

  def seed(self, model, properties):
    return seeder_logic.seed(model, properties, recurse=False)

  def seedn(self, model, properties, n):
    return seeder_logic.seedn(model, n, properties, recurse=False)

  def createUser(self):
    """Creates a user entity for the current user.
    """
    if self.user:
      return self.user
    from soc.models.user import User
    from soc.modules.seeder.logic.providers.user import CurrentUserProvider
    properties = {'account': CurrentUserProvider(),
                  'status': 'valid', 'is_developer': self.dev_test}
    self.user = self.seed(User, properties=properties)
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
    from soc.models.user import User
    from soc.modules.seeder.logic.providers.user import FixedUserProvider
    properties = {'account': FixedUserProvider(value=email), 'status': 'valid'}
    self.user = self.seed(User, properties=properties)
    return self

  def createProfile(self):
    """Creates a profile for the current user.
    """
    if self.profile:
      return
    from soc.modules.gsoc.models.profile import GSoCProfile
    user = self.createUser()
    properties = {
        'link_id': user.link_id, 'student_info': None, 'user': user,
        'parent': user, 'scope': self.program, 'status': 'active',
        'email': self.user.account.email(),
        'mentor_for': [], 'org_admin_for': [],
        'is_org_admin': False, 'is_mentor': False, 'is_student': False
    }
    self.profile = self.seed(GSoCProfile, properties)
    return self.profile

  def notificationSettings(
      self, new_requests=False, new_invites=False,
      withdrawn=False, handled=False,
      new_proposals=False, proposal_updates=False,
      public_comments=False, private_comments=False):
    self.createProfile()
    self.profile.notify_new_requests = new_requests
    self.profile.notify_new_invites = new_invites
    self.profile.notify_withdrawn = withdrawn
    self.profile.notify_handled = handled
    self.profile.notify_new_proposals = new_proposals
    self.profile.notify_proposal_updates = proposal_updates
    self.profile.notify_public_comments = public_comments
    self.profile.notify_private_comments = private_comments
    self.profile.put()

  def createStudent(self):
    """Sets the current suer to be a student for the current program.
    """
    self.createProfile()
    from soc.modules.gsoc.models.profile import GSoCStudentInfo
    properties = {'key_name': self.profile.key().name(), 'parent': self.profile,
                  'school': None,}
    self.profile.student_info = self.seed(GSoCStudentInfo, properties)
    self.profile.put()
    return self.profile

  def createStudentWithProposal(self, org, mentor):
    return self.createStudentWithProposals(org, mentor, 1)

  def createStudentWithProposals(self, org, mentor, n):
    """Sets the current user to be a student with a proposal for the current program.
    """
    self.createStudent()
    from soc.modules.gsoc.models.proposal import GSoCProposal
    properties = {'scope': self.profile,
                  'parent': self.profile, 'status': 'pending',
                  'program': self.program, 'org': org, 'mentor': mentor}
    self.seedn(GSoCProposal, properties, n)
    return self.profile

  def createStudentWithProject(self, org, mentor):
    return self.createStudentWithProjects(org, mentor, 1)

  def createStudentWithProjects(self, org, mentor, n):
    """Sets the current user to be a student with a project for the current program.
    """
    self.createStudent()
    from soc.modules.gsoc.models.student_project import StudentProject
    from soc.modules.seeder.logic.providers.string import NextLinkIDProvider
    properties = {'program': self.program, 'scope': org,
                  'student': self.profile, 'status': 'accepted',
                  'mentor': mentor,
                  'link_id': NextLinkIDProvider(start=-1)}
    self.seedn(StudentProject, properties, n)
    return self.profile

  def createHost(self):
    """Sets the current user to be a host for the current program.
    """
    self.createUser()
    self.user.host_for = [self.program.scope.key()]
    self.user.put()
    return self.user

  def createOrgAdmin(self, org):
    """Creates an org admin profile for the current user.
    """
    self.createProfile()
    self.profile.mentor_for = [org.key()]
    self.profile.org_admin_for = [org.key()]
    self.profile.put()
    return self.profile

  def createMentor(self, org):
    """Creates an mentor profile for the current user.
    """
    self.createProfile()
    self.profile.mentor_for = [org.key()]
    self.profile.put()
    return self.profile

  def createMentorWithProject(self, org, student):
    """Creates an mentor profile with a project for the current user.
    """
    self.createMentor(org)
    from soc.modules.gsoc.models.student_project import StudentProject
    properties = {'mentor': self.profile, 'program': self.program,
                  'student': student, 'scope': org}
    self.seed(StudentProject, properties)
    return self.profile
