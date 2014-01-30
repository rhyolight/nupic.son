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

"""Breaks a cyclic import problem but possibly shouldn't exist."""

import datetime

from google.appengine.ext import ndb

from melange.models import address as address_model
from melange.models import contact as contact_model
from melange.models import profile as ndb_profile_model

from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import proposal as proposal_model

TEST_PUBLIC_NAME = 'Public Name'
TEST_FIRST_NAME = 'First'
TEST_LAST_NAME = 'Last'
TEST_STREET = 'Street'
TEST_CITY = 'City'
TEST_COUNTRY = 'United States'
TEST_POSTAL_CODE = '90000'
TEST_PROVINCE = 'California'
TEST_ABSTRACT = 'Test Abstract'
TEST_TITLE = 'Test Title'
TEST_CONTENT = 'Test Content'


def seedNDBProfile(
    program_key, user, mentor_for=None, admin_for=None, **kwargs):
  """Seeds a new profile.

  Args:
    program_key: Program key for which the profile is seeded.
    user: User entity corresponding to the profile.
    mentor_for: List of organizations keys for which the profile should be
      registered as a mentor.
    admin_for: List of organizations keys for which the profile should be
      registered as organization administrator.

  Returns:
    A newly seeded Profile entity.
  """
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
  profile = ndb_profile_model.Profile(
      id='%s/%s' % (program_key.name(), user.key.id()),
      parent=user.key, **properties)
  profile.put()
  return profile


def seedProposal(student_key, program_key, org_key, mentor_key, **kwargs):
  """Seeds a new proposal entity.

  Args:
    student_key: Key of the student who is an author of the proposal.
    program_key: Key of the program to which the proposal applies.
    org_key: Key of the organization to which the proposal is submitted.
    mentor_key: Key of the mentor assigned to the proposal.

  Returns:
    The newly seeded proposal entity.
  """
  properties = {
      'scope': student_key.to_old_key(),
      'score': 0,
      'nr_scores': 0,
      'is_publicly_visible': False,
      'accept_as_project': False,
      'is_editable_post_deadline': False,
      'extra': None,
      'parent': student_key.to_old_key(),
      'status': 'pending',
      'has_mentor': True,
      'program': program_key,
      'org': org_key.to_old_key(),
      'mentor': mentor_key.to_old_key(),
      'abstract': TEST_ABSTRACT,
      'title': TEST_TITLE,
      'content': TEST_CONTENT,
      }
  properties.update(**kwargs)
  proposal = proposal_model.GSoCProposal(**properties)
  proposal.put()

  if proposal.status != proposal_model.STATUS_WITHDRAWN:
    student = student_key.get()
    student.student_data.number_of_proposals += 1
    student.put()

  return proposal


def seedProject(
    student, program_key, proposal_key, org_key, mentor_key, **kwargs):
  """Seeds a new project entity.

  Args:
    student: Profile entity of the student who is an author of the project.
    program_key: Key of the program to which the project applies.
    proposal_key: Key of the proposal corresponding to the project.
    org_key: Key of the organization to which the project is submitted.
    mentor_key: Key of the mentor assigned to the project.

  Returns:
    The newly seeded project entity.
  """
  properties = {
      'program': program_key,
      'org': org_key.to_old_key(),
      'status': project_model.STATUS_ACCEPTED,
      'parent': student.key.to_old_key(),
      'mentors': [mentor_key.to_old_key()],
      'proposal': proposal_key,
      'title': TEST_TITLE,
      'abstract': TEST_ABSTRACT,
      }
  properties.update(**kwargs)
  project = project_model.GSoCProject(**properties)
  project.put()

  student.student_data.number_of_projects += 1
  student.put()

  return project
