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

"""Module containing the views for GSoC accepted orgs."""

from google.appengine.ext import ndb

from django.utils import html as html_utils

from melange.request import access
from melange.request import exception
from melange.request import links
from soc.views.helper import lists
from soc.views.helper import url_patterns

from soc.modules.gsoc.logic import profile as profile_logic
from soc.modules.gsoc.templates import org_list
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url

from summerofcode.models import organization as org_model
from summerofcode.views.helper import urls

# TODO(daniel): update this class to fully work with NDB organizations
class AcceptedOrgsAdminList(org_list.OrgList):
  """Template for list of accepted organizations."""

  class ListPrefetcher(lists.Prefetcher):
    """Prefetcher used by AcceptedOrgsAdminList.

    See lists.Prefetcher for specification.
    """

    def prefetch(self, entities):
      """See lists.Prefetcher.prefetch for specification."""
      org_admins = {}
      for entity in entities:
        org_admins_for_org = profile_logic.getOrgAdmins(entity.key)
        org_admins[entity.key] = ', '.join(
            ['"%s" &lt;%s&gt;' % (
                html_utils.conditional_escape(org_admin_for_org.name()),
                html_utils.conditional_escape(org_admin_for_org.email))
                for org_admin_for_org in org_admins_for_org])

      return ([org_admins], {})

  def _getDescription(self):
    """See org_list.OrgList._getDescription for specification."""
    return org_list.ACCEPTED_ORG_LIST_DESCRIPTION % self.data.program.name

  def _getListConfig(self):
    """See org_list.OrgList._getListConfig for specification."""
    list_config = lists.ListConfiguration()

    list_config.addPlainTextColumn('name', 'Name',
        lambda e, *args: e.name.strip())

    list_config.addSimpleColumn('org_id', 'Organization ID', hidden=True)

    list_config.addHtmlColumn('org_admin', 'Org Admins',
        lambda e, *args: args[0][e.key])

    list_config.setRowAction(
        lambda e, *args: links.LINKER.organization(
            e.key, urls.UrlNames.ORG_HOME))

    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('name')

    return list_config

  def _getQuery(self):
    """See org_list.OrgList._getQuery for specification."""
    query = org_model.SOCOrganization.query(
        org_model.SOCOrganization.program ==
            ndb.Key.from_old_key(self.data.program.key()))

    return query

  def _getPrefetcher(self):
    """See org_list.OrgList._getPrefetcher for specification."""
    return AcceptedOrgsAdminList.ListPrefetcher()


class AcceptedOrgsAdminPage(base.GSoCRequestHandler):
  """View for admin-only page that lists the accepted organizations."""

  LIST_IDX = 0

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url(r'admin/accepted_orgs/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GSOC_ORG_LIST_FOR_HOST),
    ]

  def templatePath(self):
    return 'modules/gsoc/admin/list.html'

  def jsonContext(self, data, check, mutator):
    list_content = AcceptedOrgsAdminList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    return {
      'page_name': 'Organizations list page',
      'list': AcceptedOrgsAdminList(data)
    }
