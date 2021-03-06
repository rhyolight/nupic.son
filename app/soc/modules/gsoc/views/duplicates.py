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

"""Module containing the views for GSoC proposal duplicates."""

from google.appengine.api import taskqueue
from google.appengine.ext import db

from django import http

from melange.request import access
from melange.request import links

from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gsoc.logic import duplicates as duplicates_logic
from soc.modules.gsoc.logic import profile as profile_logic
from soc.modules.gsoc.models import proposal as proposal_model
from soc.modules.gsoc.models.proposal_duplicates import GSoCProposalDuplicate
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url

from summerofcode.views.helper import urls


class DuplicatesPage(base.GSoCRequestHandler):
  """View for the host to see duplicates."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gsoc/duplicates/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'duplicates/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_view_duplicates'),
    ]

  def context(self, data, check, mutator):
    """Returns the context for this page."""
    program = data.program

    q = GSoCProposalDuplicate.all()
    q.filter('program', program)
    q.filter('is_duplicate', True)

    duplicates = [Duplicate(data, duplicate) for duplicate in q.fetch(1000)]
    duplicates_status = duplicates_logic.getOrCreateStatusForProgram(program)

    context = {
      'page_name': 'Duplicates for %s' %program.name,
      'duplicates_status': duplicates_status,
      'duplicates': duplicates,
    }

    return context

  def post(self, data, request, mutator):
    """Handles the POST request to (re)start calcuation."""
    post_data = data.request.POST

    # pass along these params as POST to the new task
    task_params = {'program_key': data.program.key().id_or_name()}
    task_url = '/tasks/gsoc/proposal_duplicates/start'

    # checks if the task newly added is the first task
    # and must be performed repeatedly every hour or
    # just be performed once right away
    if 'calculate' in post_data:
      task_params['repeat'] = 'yes'
    elif 'recalculate' in post_data:
      task_params['repeat'] = 'no'

    # adds a new task
    new_task = taskqueue.Task(params=task_params, url=task_url)
    new_task.add()

    # TODO(nathaniel): WTF?
    # redirect to self
    return http.HttpResponseRedirect('')


class Duplicate(Template):
  """Template for showing a duplicate to the host."""

  def __init__(self, data, duplicate):
    """Constructs the template for showing a duplicate.

    Args:
      data: RequestData object.
      duplicate: GSoCProposalDuplicat entity to render.
    """
    self.duplicate = duplicate
    super(Duplicate, self).__init__(data)

  def context(self):
    """Returns the context for the current template."""
    context = {'duplicate': self.duplicate}

    # TODO(daniel): it should be done via NDB
    orgs = db.get(self.duplicate.orgs)
    proposals = db.get(self.duplicate.duplicates)

    orgs_details = {}
    for org in orgs:
      orgs_details[org.key().id_or_name()] = {
          'name': org.name,
          'link': links.LINKER.organization(org.key, urls.UrlNames.ORG_HOME),
          }
      org_admins = profile_logic.getOrgAdmins(org.key())

      orgs_details[org.key().id_or_name()]['admins'] = []
      for org_admin in org_admins:
        orgs_details[org.key().id_or_name()]['admins'].append({
            'name': org_admin.name(),
            'email': org_admin.email
            })

      orgs_details[org.key().id_or_name()]['proposals'] = []
      for proposal in proposals:
        org_key = proposal_model.GSoCProposal.org.get_value_for_datastore(
            proposal)
        if org_key == org.key():
          orgs_details[org.key().id_or_name()]['proposals'].append({
              'key': proposal.key().id_or_name(),
              'title': proposal.title,
              'link': links.LINKER.userId(
                  proposal.parent_key(), proposal.key().id(),
                  url_names.PROPOSAL_REVIEW),
              })

    context['orgs'] = orgs_details

    return context

  def templatePath(self):
    """Returns the path to the template that should be used in render()."""
    return 'modules/gsoc/duplicates/proposal_duplicate.html'
