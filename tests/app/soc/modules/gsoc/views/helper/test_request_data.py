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

from soc.models import program as program_model

from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.views.helper import request_data
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from tests import profile_utils
from tests import program_utils


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

    program_properties = {
        'scope': sponsor,
        'sponsor': sponsor,
        }
    program = seeder_logic.seed(
        program_model.Program, properties=program_properties)
    program.program_id = program.link_id
    program.put()

    profile = profile_utils.seedGSoCStudent(program)
    project_properties = {'parent': profile}
    project = seeder_logic.seed(project_model.GSoCProject,
        properties=project_properties)

    kwargs = {
        'sponsor': sponsor.link_id,
        'program': program.program_id,
        'user': profile.link_id,
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
    program = seeder_logic.seed(program_model.Program)
    user = profile_utils.seedUser()
    profile_properties = {
        'key_name': '%s/%s/%s' % 
            (sponsor.link_id, program.program_id, user.link_id),
        'parent': user,
        'link_id': user.link_id
        }
    profile = seeder_logic.seed(profile_model.GSoCProfile, profile_properties)
    proposal_properties = {'parent': profile}
    proposal = seeder_logic.seed(proposal_model.GSoCProposal,
        properties=proposal_properties)

    kwargs = {
        'sponsor': sponsor.link_id,
        'program': program.program_id,
        'user': profile.link_id,
        'id': str(proposal.key().id())
        }
    data = request_data.RequestData(None, None, kwargs)
    url_proposal = data.url_proposal
    self.assertEqual(proposal.key(), url_proposal.key())
