# Copyright 2012 the Melange authors.
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

"""Module for the GCI organization score page."""

from soc.logic import exceptions
from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gci.models.score import GCIOrgScore
from soc.modules.gci.templates.org_list import BasicOrgList
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url


class OrgScoresList(Template):
  """Template for the list students with the number of tasks they
  have completed for the specified organization.
  """

  ORG_SCORE_LIST_IDX = 0

  def __init__(self, request, data):
    self.request = request
    self.data = data
    r = data.redirect

    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addColumn('key', 'Key', (lambda ent, *args: "%s" % (
        ent.parent().key().id_or_name())), hidden=True)
    list_config.addColumn('student', 'Student',
        lambda e, *args: e.parent().name())
    list_config.addColumn('tasks', 'Tasks',
        lambda e, *args: e.numberOfTasks())
    list_config.setDefaultSort('tasks', 'desc')

    list_config.setRowAction(
        lambda e, *args: r.userOrg(user=e.parent().link_id).urlOf(
            url_names.GCI_STUDENT_TASKS_FOR_ORG))

    self._list_config = list_config

  def context(self):
    description = 'Organization scores for %s' % (
            self.data.organization.name)

    org_scores_list = lists.ListConfigurationResponse(
        self.data, self._list_config, self.ORG_SCORE_LIST_IDX, description)

    return {
        'lists': [org_scores_list],
    }

  def getListData(self):
    idx = lists.getListIndex(self.request)
    if idx == self.ORG_SCORE_LIST_IDX:
      q = GCIOrgScore.all()
      q.filter('org', self.data.organization)

      skipper = lambda entity, start: entity.numberOfTasks() <= 0
    #  prefetcher = lists.modelPrefetcher(GCIScore, [], True)

      response_builder = lists.RawQueryContentResponseBuilder(self.request,
          self._list_config, q, lists.keyStarter, skipper=skipper)

      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return 'v2/modules/gci/leaderboard/_leaderboard_list.html'


class OrgScoresForOrgzanizationPage(GCIRequestHandler):
  """View for the organizations scores page.
  """

  def templatePath(self):
    return 'v2/modules/gci/org_score/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'org_scores/%s$' % url_patterns.ORG, self,
            name=url_names.GCI_ORG_SCORES),
    ]

  def checkAccess(self):
    pass

  def context(self):
    return {
        'page_name': "Organization scores for %s" %
            self.data.organization.name,
        'org_scores_list': OrgScoresList(self.request, self.data),
    }

  def jsonContext(self):
    list_content = OrgScoresList(self.request, self.data).getListData()

    if not list_content:
      raise exceptions.AccessViolation(
          'You do not have access to this data')
    return list_content.content()


class OrganizationsForOrgScoreList(BasicOrgList):
  """Lists all organizations that have been accepted for the specified
  program and the row action is to show a list of scores for this organization.
  """

  def _getDescription(self):
    return "Choose an organization for which to display scores."

  def _getRedirect(self):
    def redirect(e, *args):
      r = self.data.redirect
      return r.organization(e).urlOf(url_names.GCI_ORG_SCORES)
    return redirect


class ChooseOrganizationForOrgScorePage(GCIRequestHandler):
  """View with a list of organizations. When a user clicks on one of them,
  he or she is moved to the organization scores for this organization.
  """

  def templatePath(self):
    return 'v2/modules/gci/org_list/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'org_choose_for_score/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_ORG_CHOOSE_FOR_SCORE),
    ]

  def checkAccess(self):
    # TODO(daniel): check if the program has started
    self.check.isHost()
    pass

  def jsonContext(self):
    list_content = OrganizationsForOrgScoreList(
        self.request, self.data).getListData()

    if not list_content:
      raise exceptions.AccessViolation(
          'You do not have access to this data')
    return list_content.content()

  def context(self):
    return {
        'page_name': "Choose an organization for which to display scores.",
        'org_list': OrganizationsForOrgScoreList(self.request, self.data),
        #'program_select': ProgramSelect(self.data, 'gci_accepted_orgs'),
    }
