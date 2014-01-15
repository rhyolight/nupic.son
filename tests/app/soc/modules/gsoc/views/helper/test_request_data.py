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

"""Tests for request_data module."""

import httplib
import unittest

from melange.request import exception

from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.views.helper import request_data
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import profile_utils
from tests import program_utils
from tests.utils import project_utils
from tests.utils import proposal_utils


class UrlProjectTest(unittest.TestCase):
  """Unit tests for url_project property or RequestData class."""

  def testNoProjectData(self):
    """Tests that error is raised if there is no project data in kwargs."""
    # no data at all
    data = request_data.RequestData(None, None, {})
    with self.assertRaises(exception.UserError) as context:
      data.url_project
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # program data and project id but no user identifier
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id',
        'id': '1'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_project
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # user identifier and project id present but no program data
    kwargs = {
        'user': 'user_id',
        'id': '1'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_project
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # no project id
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id',
        'user': 'user_id'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_project
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

  def testProjectDoesNotExists(self):
    """Tests that error is raised if requested project does not exist."""
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id',
        'user': 'user_id',
        'id': '1'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_project
    self.assertEqual(context.exception.status, httplib.NOT_FOUND)

  def testProjectExists(self):
    """Tests that project is returned correctly if exists."""
    sponsor = program_utils.seedSponsor()
    program = program_utils.seedProgram(sponsor_key=sponsor.key())

    profile = profile_utils.seedSOCStudent(program)
    project = project_utils.seedProject(profile, program.key())

    kwargs = {
        'sponsor': sponsor.link_id,
        'program': program.program_id,
        'user': profile.profile_id,
        'id': str(project.key().id())
        }
    data = request_data.RequestData(None, None, kwargs)
    url_project = data.url_project
    self.assertEqual(project.key(), url_project.key())


class UrlProposalTest(unittest.TestCase):
  """Unit tests for url_proposal property of RequestData class."""

  def testNoProposalData(self):
    """Tests that error is raised if there is no profile data in kwargs."""
    # no data at all
    data = request_data.RequestData(None, None, {})
    with self.assertRaises(exception.UserError) as context:
      data.url_proposal
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # program data and proposal id but no user identifier
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id',
        'id': '1'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_proposal
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # user identifier and proposal id present but no program data
    kwargs = {
        'user': 'user_id',
        'id': '1'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_proposal
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

    # no proposal id
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id',
        'user': 'user_id'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_proposal
    self.assertEqual(context.exception.status, httplib.BAD_REQUEST)

  def testProposalDoesNotExists(self):
    """Tests that error is raised if requested proposal does not exist."""
    kwargs = {
        'sponsor': 'sponsor_id',
        'program': 'program_id',
        'user': 'user_id',
        'id': '1'
        }
    data = request_data.RequestData(None, None, kwargs)
    with self.assertRaises(exception.UserError) as context:
      data.url_proposal
    self.assertEqual(context.exception.status, httplib.NOT_FOUND)

  def testProposalExists(self):
    """Tests that proposal is returned correctly if exists."""
    sponsor = program_utils.seedSponsor()
    program = program_utils.seedProgram(sponsor_key=sponsor.key())

    profile = profile_utils.seedSOCStudent(program)
    proposal = proposal_utils.seedProposal(profile.key, program.key())

    kwargs = {
        'sponsor': sponsor.link_id,
        'program': program.program_id,
        'user': profile.profile_id,
        'id': str(proposal.key().id())
        }
    data = request_data.RequestData(None, None, kwargs)
    url_proposal = data.url_proposal
    self.assertEqual(proposal.key(), url_proposal.key())
