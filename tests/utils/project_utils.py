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

""" Utilities to manipulate project data."""

from soc.modules.gsoc.models import project as project_model

from tests import org_utils
from tests import profile_utils
from tests.utils import proposal_utils


TEST_ABSTRACT = 'Test Abstract'
TEST_TITLE = 'Test Title'
TEST_CONTENT = 'Test Content'

def seedProject(
    student, program_key, proposal_key=None,
    org_key=None, mentor_key=None, **kwargs):
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
  org_key = org_key or org_utils.seedSOCOrganization(program_key).key
  mentor_key = mentor_key or profile_utils.seedNDBProfile(
      program_key, mentor_for=[org_key]).key

  proposal_key = proposal_key or proposal_utils.seedProposal(
      student.key, program_key, org_key=org_key, mentor_key=mentor_key).key()

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

