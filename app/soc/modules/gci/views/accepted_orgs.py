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

"""Module containing the views for GCI accepted orgs."""

from melange.request import access
from melange.request import exception
from soc.views.helper import lists
from soc.views.helper import url as url_helper
from soc.views.helper import url_patterns

from soc.modules.gci.logic import profile as profile_logic
from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.gci.templates.org_list import OrgList
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper.url_patterns import url
from soc.modules.gci.views.helper import url_names


class AcceptedOrgsList(OrgList):
  """Template for list of accepted organizations.
  """

  def _getDescription(self):
    return 'List of organizations accepted into %s' % (
        self.data.program.name)

  def _getListConfig(self):
    # TODO(nathaniel): squeeze this back into a lambda expression in
    # the call to setRowAction below.
    def RowAction(e, *args):
      # TODO(nathaniel): make this .organization call unnecessary.
      self.data.redirect.organization(organization=e)

      return self.data.redirect.urlOf(url_names.GCI_ORG_HOME)

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('name', 'Name',
        lambda e, *args: e.name.strip())
    list_config.addSimpleColumn('link_id', 'Organization ID', hidden=True)
    list_config.setRowAction(RowAction)
    list_config.addPlainTextColumn(
        'ideas', 'Ideas',
        (lambda e, *args: url_helper.urlize(e.ideas, name="[ideas page]")),
        hidden=True)
    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('name')
    return list_config

  def _getQuery(self):
    query = GCIOrganization.all()
    query.filter('program', self.data.program)
    query.filter('status IN', ['new', 'active'])
    return query


class AcceptedOrgsPage(GCIRequestHandler):
  """View for the accepted organizations page."""

  def templatePath(self):
    return 'modules/gci/accepted_orgs/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'accepted_orgs/%s$' % url_patterns.PROGRAM, self,
            name='gci_accepted_orgs'),
    ]

  def checkAccess(self, data, check, mutator):
    check.acceptedOrgsAnnounced()

  def jsonContext(self, data, check, mutator):
    list_content = AcceptedOrgsList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    return {
        'page_name': "Accepted organizations for %s" % data.program.name,
        'accepted_orgs_list': AcceptedOrgsList(data),
        #'program_select': ProgramSelect(data, 'gci_accepted_orgs'),
    }


class AcceptedOrgsAdminList(OrgList):
  """Template for list of accepted organizations for admins."""

  class ListPrefetcher(lists.Prefetcher):
    """Prefetcher used for AcceptedOrgsAdminList list.

    See lists.Prefetcher for specification.
    """

    def prefetch(self, entities):
      """Prefetches GCIProfiles corresponding to Organization Administrators
      of the specified list of GCIOrganization entities.

      See lists.Prefetcher.prefetch for specification.

      Args:
        entities: the specified list of GCIOrganization instances

      Returns:
        prefetched GCIProfile entities in a structure whose format is
        described in lists.Prefetcher.prefetch
      """
      prefetched_dict = {}
      for ent in entities:
        prefetched_dict[ent.key()] = profile_logic.orgAdminsForOrg(ent)

      return [prefetched_dict], {}


  def _getDescription(self):
    return 'List of organizations accepted into %s' % (
        self.data.program.name)

  def _getListConfig(self):
    # TODO(nathaniel): squeeze this back into a lambda expression in the
    # call to setRowAction below.
    def RowAction(e, *args):
      # TODO(nathaniel): make this .organization call unnecessary.
      self.data.redirect.organization(organization=e)

      return self.data.redirect.urlOf(url_names.GCI_ORG_HOME)

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('name', 'Name',
        lambda e, *args: e.name.strip())
    list_config.addSimpleColumn('link_id', 'Organization ID', hidden=True)
    list_config.setRowAction(RowAction)
    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('name')
    list_config.addPlainTextColumn(
      'org_admins', 'Org Admins',
      lambda e, org_admins, *args: ", ".join(
          ["%s <%s>" % (o.name(), o.email) for o in org_admins[e.key()]]),
      hidden=True)
    return list_config

  def _getPrefetcher(self):
    return AcceptedOrgsAdminList.ListPrefetcher()

  def _getQuery(self):
    query = GCIOrganization.all()
    query.filter('program', self.data.program)
    query.filter('status IN', ['new', 'active'])
    return query


class AcceptedOrgsAdminPage(GCIRequestHandler):
  """View for the accepted organizations page for admin with additional info.
  """

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gci/accepted_orgs/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'admin/accepted_orgs/%s$' % url_patterns.PROGRAM, self,
            name='gci_admin_accepted_orgs'),
    ]

  def jsonContext(self, data, check, mutator):
    list_content = AcceptedOrgsAdminList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    return {
        'page_name': "Accepted organizations for %s" % data.program.name,
        'accepted_orgs_list': AcceptedOrgsAdminList(data),
    }
