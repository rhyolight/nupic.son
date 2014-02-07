# Copyright 2011 the Melange authors.
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

"""Module containing the views for listing all the projects accepted
into a GSoC program.
"""

import json
import logging

from google.appengine.ext import db
from google.appengine.ext import ndb

from django import http

from melange.request import access
from melange.request import exception
from soc.views import base_templates
from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.logic import proposal as proposal_logic
from soc.modules.gsoc.models import project as project_model
from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper.url_patterns import url

# key to map proposal with and its full key in list data
_PROPOSAL_KEY = 'full_proposal_key'

class ProposalList(Template):
  """Template for listing the student proposals submitted to the program."""

  def __init__(self, data):

    def getOrganization(entity, *args):
      """Helper function to get value of organization column."""
      org_key = proposal_model.GSoCProposal.org.get_value_for_datastore(entity)
      return ndb.Key.from_old_key(org_key).get().name

    self.data = data

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('student', 'Student',
                          lambda entity, *args: entity.parent().name())
    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn('org', 'Organization', getOrganization)

    def status(proposal):
      """Status to show on the list with color.
      """
      if proposal.status == proposal_model.STATUS_ACCEPTED:
        return """<strong><font color="green">Accepted</font><strong>"""
      elif proposal.status == 'withdrawn':
        return """<strong><font color="red">Withdrawn</font></strong>"""

      return proposal.status.capitalize()

    list_config.addHtmlColumn('status', 'Status',
        lambda entity, *args: status(entity))

    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('student')

    # hidden keys
    list_config.addHtmlColumn(
        _PROPOSAL_KEY, 'Full proposal key',
        (lambda ent, *args: str(ent.key())), hidden=True)

    # action button
    bounds = [1, 'all']
    keys = [_PROPOSAL_KEY]
    list_config.addPostButton('accept', "Accept", "", bounds, keys)

    self._list_config = list_config

  def context(self):
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=0,
        description='List of proposals submitted for %s' % (
            self.data.program.name))

    return {
        'list_title': 'Submitted Proposals',
        'lists': [list_configuration_response],
        }

  def post(self):
    idx = lists.getListIndex(self.data.request)
    if idx != 0:
      return None

    list_data = self.data.POST.get('data')

    if not list_data:
      raise exception.BadRequest(message="Missing data")

    button_id = self.data.POST.get('button_id')

    if button_id == 'accept':
      return self.postHandler(json.loads(list_data))
    elif button_id:
      raise exception.BadRequest(message='Unknown button_id')
    else:
      raise exception.BadRequest(message="Missing button_id")

  def postHandler(self, data):
    for properties in data:
      if _PROPOSAL_KEY not in properties:
        logging.warning("Missing key in '%s'", properties)
        continue

      proposal_key = properties[_PROPOSAL_KEY]

      def accept_proposal_txn():
        """Accept the proposal within a transaction."""
        proposal = db.get(proposal_key)

        if not proposal:
          logging.warning("Proposal '%s' doesn't exist", proposal_key)
        elif proposal.status == proposal_model.STATUS_ACCEPTED:
          logging.warning("Proposal '%s' already accepted", proposal_key)
        else:
          # check if the proposal has been assigned a mentor
          mentor_key = (proposal_model.GSoCProposal.mentor
              .get_value_for_datastore(proposal))
          if not mentor_key:
            logging.warning(
                'Proposal with key %s cannot be accepted because no mentor has'
                ' been assigned to it.', proposal_key)
          else:
            proposal_logic.acceptProposal(proposal)

      # TODO(daniel): run within a transaction when proposals are NDB models
      # db.run_in_transaction(accept_proposal_txn)
      accept_proposal_txn()

    return True

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.data.request)
    if idx == 0:
      list_query = proposal_logic.getProposalsQuery(program=self.data.program)

      starter = lists.keyStarter

      # TODO(daniel): support prefetching of NDB organizations
      #prefetcher = lists.ModelPrefetcher(
      #    proposal_model.GSoCProposal, ['org'], parent=True)
      # Since ModelPrefetcher doesn't work with NDB, pass an empty list
      # for the field parameter to prevent __init__() exception.
      prefetcher = lists.ModelPrefetcher(
          proposal_model.GSoCProposal, [], parent=True)

      response_builder = lists.RawQueryContentResponseBuilder(
          self.data.request, self._list_config, list_query,
          starter, prefetcher=prefetcher)
      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return 'modules/gsoc/accept_withdraw_projects/_project_list.html'


class AcceptProposals(base.GSoCRequestHandler):
  """View for accepting individual proposals."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gsoc/accept_withdraw_projects/base.html'

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping."""

    return [
        url(r'admin/proposals/accept/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_admin_accept_proposals')
    ]

  def jsonContext(self, data, check, mutator):
    """Handler for JSON requests."""
    list_content = ProposalList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def post(self, data, check, mutator):
    list_content = ProposalList(data)
    if list_content.post():
      return http.HttpResponse()
    else:
      raise exception.Forbidden(message='You cannot change this data')

  def context(self, data, check, mutator):
    """Builds the context for GSoC proposals List page HTTP get request."""
    program = data.program

    return {
        'page_name': '%s - Proposals' % program.short_name,
        'program_name': program.name,
        'list': ProposalList(data),
        'program_select': base_templates.DefaultProgramSelect(
            data, 'gsoc_admin_accept_proposals'),
    }


class ProjectList(Template):
  """Template for listing the student projects accepted in the program.
  """

  def __init__(self, data):

    def getOrganization(entity, *args):
      """Helper function to get value of organization column."""
      org_key = project_model.GSoCProject.org.get_value_for_datastore(entity)
      return ndb.Key.from_old_key(org_key).get().name

    def getStudent(entity, *args):
      """Helper function to get value of student column."""
      return ndb.Key.from_old_key(entity.parent_key()).get().public_name

    self.data = data

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('student', 'Student', getStudent)
    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn('org', 'Organization', getOrganization)

    def status(project):
      """Status to show on the list with color.
      """
      if project.status == project_model.STATUS_ACCEPTED:
        return """<strong><font color="green">Accepted</font><strong>"""
      elif project.status == 'withdrawn':
        return """<strong><font color="red">Withdrawn</font></strong>"""

      return project.status

    list_config.addHtmlColumn('status', 'Status',
        lambda entity, *args: status(entity))

    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('student')

    # hidden keys
    list_config.addPlainTextColumn(
        'full_project_key', 'Full project key',
        lambda ent, *args: str(ent.key()), hidden=True)

    # action button
    bounds = [1, 'all']
    keys = ['full_project_key']
    list_config.addPostButton('withdraw', "Withdraw", "", bounds, keys)
    list_config.addPostButton('accept', "Accept", "", bounds, keys)

    self._list_config = list_config

  def context(self):
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=0,
        description='List of %s projects whether accepted or withdrawn' % (
            self.data.program.name))

    return {
        'list_title': 'Accepted Projects',
        'lists': [list_configuration_response],
        }

  def post(self):
    idx = lists.getListIndex(self.data.request)
    if idx != 0:
      return None

    data = self.data.POST.get('data')

    if not data:
      raise exception.BadRequest(message="Missing data")

    parsed = json.loads(data)

    button_id = self.data.POST.get('button_id')

    if not button_id:
      raise exception.BadRequest(message="Missing button_id")
    elif button_id == 'withdraw':
      return self.postHandler(parsed)
    elif button_id == 'accept':
      return self.postHandler(parsed, withdraw=False)
    else:
      raise exception.BadRequest(message="Unknown button_id")

  def postHandler(self, data, withdraw=True):
    for properties in data:
      if 'full_project_key' not in properties:
        logging.warning("Missing key in '%s'", properties)
        continue

      project_key = properties['full_project_key']
      project = db.get(db.Key(project_key))

      if not project:
        logging.warning("Project '%s' doesn't exist", project_key)
        continue

      if withdraw and project.status == 'withdrawn':
        logging.warning("Project '%s' already withdrawn", project_key)
        continue

      if not withdraw and project.status == project_model.STATUS_ACCEPTED:
        logging.warning("Project '%s' already accepted", project_key)
        continue

      # key of the organization for the project
      org_key = ndb.Key.from_old_key(
          project_model.GSoCProject.org.get_value_for_datastore(project))
      # key of the student profile for the project
      profile_key = ndb.Key.from_old_key(project.parent_key())

      proposal = project.proposal

      def withdraw_or_accept_project_txn():
        profile = profile_key.get()
        orgs = profile.student_data.project_for_orgs

        if withdraw:
          new_status = 'withdrawn'
          new_number = 0
          orgs.remove(org_key)
        else:
          new_status = project_model.STATUS_ACCEPTED
          new_number = 1
          orgs = list(set(orgs + [org_key]))

        project.status = new_status
        proposal.status = new_status
        profile.student_data.project_for_orgs = orgs
        profile.student_data.number_of_projects = new_number

        db.put([proposal, project])
        profile.put()

      db.run_in_transaction(withdraw_or_accept_project_txn)

    return True

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.data.request)
    if idx == 0:
      list_query = project_logic.getProjectsQuery(program=self.data.program)

      starter = lists.keyStarter
      # TODO(daniel): support prefetching of NDB organizations
      #prefetcher = lists.ModelPrefetcher(
      #    project_model.GSoCProject, ['org'], parent=True)
      prefetcher = None

      response_builder = lists.RawQueryContentResponseBuilder(
          self.data.request, self._list_config, list_query,
          starter, prefetcher=prefetcher)
      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return "modules/gsoc/accept_withdraw_projects/_project_list.html"


class WithdrawProjects(base.GSoCRequestHandler):
  """View methods for withdraw projects."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gsoc/accept_withdraw_projects/base.html'

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping.
    """

    return [
        url(r'withdraw_projects/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_withdraw_projects')
    ]

  def jsonContext(self, data, check, mutator):
    """Handler for JSON requests."""
    list_content = ProjectList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def post(self, data, check, mutator):
    """See soc.views.base.RequestHandler.post for specification."""
    list_content = ProjectList(data)
    if list_content.post():
      return http.HttpResponse()
    else:
      raise exception.Forbidden(message='You cannot change this data')

  def context(self, data, check, mutator):
    """Handler for GSoC Accepted Projects List page HTTP get request."""
    return {
        'page_name': '%s - Projects' % data.program.short_name,
        'program_name': data.program.name,
        'list': ProjectList(data),
        'program_select': base_templates.DefaultProgramSelect(
            data, 'gsoc_withdraw_projects'),
    }
