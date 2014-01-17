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

""" Utilities to manipulate proposal data."""

from soc.modules.gsoc.models import proposal as proposal_model

from tests import org_utils
from tests import profile_utils


TEST_ABSTRACT = 'Test Abstract'
TEST_TITLE = 'Test Title'
TEST_CONTENT = 'Test Content'


def seedProposal(
    student_key, program_key, org_key=None, mentor_key=None, **kwargs):
  """Seeds a new proposal entity.

  Args:
    student_key: Key of the student who is an author of the proposal.
    program_key: Key of the program to which the proposal applies.
    org_key: Key of the organization to which the proposal is submitted.
    mentor_key: Key of the mentor assigned to the proposal.

  Returns:
    The newly seeded proposal entity.
  """
  org_key = org_key or org_utils.seedSOCOrganization(program_key).key
  mentor_key = mentor_key or profile_utils.seedNDBProfile(
      program_key, mentor_for=[org_key]).key

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

