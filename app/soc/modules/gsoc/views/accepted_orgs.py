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

from django.conf.urls.defaults import url as django_url
from django.utils import html as http_utils

from soc.logic.exceptions import AccessViolation
from soc.views.base_templates import ProgramSelect
from soc.views.helper import lists
from soc.views.template import Template
from soc.views.helper import url as url_helper
from soc.views.helper import url_patterns

from soc.modules.gsoc.models import organization as org_model
from soc.modules.gsoc.models import profile as profile_model
from soc.modules.gsoc.templates import org_list
from soc.modules.gsoc.views.base import GSoCRequestHandler
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url


class AcceptedOrgsPublicList(org_list.OrgList):
  """Template for a public list of accepted organizations."""

  def _getDescription(self):
    """See org_list.OrgList._getDescription for specification."""
    return org_list.ACCEPTED_ORG_LIST_DESCRIPTION % self.data.program.name

  def _getListConfig(self):
    """See org_list.OrgList._getListConfig for specification."""
    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('name', 'Name',
        lambda e, *args: e.name.strip())
    list_config.addSimpleColumn('link_id', 'Organization ID', hidden=True)
    list_config.addPlainTextColumn(
        'tags', 'Tags', lambda e, *args: ", ".join(e.tags))
    list_config.addPlainTextColumn('ideas', 'Ideas',
        lambda e, *args: url_helper.urlize(e.ideas, name="[ideas page]"),
        hidden=True)
    
    list_config.setRowAction(
        lambda e, *args: (
            self.data.redirect.organization(e),
            self.data.redirect.urlOf('gsoc_org_home')))
    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('name')

    return list_config

  def _getQuery(self):
    """See org_list.OrgList._getQuery for specification."""
    query = org_model.GSoCOrganization.all()
    query.filter('scope', self.data.program)
    return query


class AdminAcceptedOrgsList(Template):
  """Template for list of accepted organizations."""

  def __init__(self, request, data):
    self.data = data

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('name', 'Name',
        (lambda e, *args: e.short_name.strip()), width=75)
    list_config.addSimpleColumn('link_id', 'Organization ID', hidden=True)

    list_config = self.extraColumn(list_config)

    # TODO(nathaniel): squeeze this back into a lambda expression
    # in the call to setRowAction below.
    def RowAction(e, *args):
      # TODO(nathaniel): make this .organization call unnecessary.
      self.data.redirect.organization(organization=e)

      return self.data.redirect.urlOf('gsoc_org_home')

    list_config.setRowAction(RowAction)

    self._list_config = list_config

  def extraColumn(self, list_config):
    list_config.addHtmlColumn('org_admin', 'Org Admins',
        (lambda e, *args: args[0][e.key()]))

    return list_config

  def context(self):
    description = 'List of organizations accepted into %s' % (
        self.data.program.name)

    list = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)

    return {
        'lists': [list],
    }

  def getListData(self):
    idx = lists.getListIndex(self.data.request)
    if idx != 0:
      return None

    q = org_model.GSoCOrganization.all().filter('scope', self.data.program)

    starter = lists.keyStarter

    def prefetcher(orgs):
      org_admins = {}
      for org in orgs:
        oas = profile_model.GSoCProfile.all().filter(
            'org_admin_for', org).fetch(limit=1000)
        org_admins[org.key()] = ', '.join(
            ['"%s" &lt;%s&gt;' % (
                http_utils.conditional_escape(oa.name()),
                http_utils.conditional_escape(oa.email)) for oa in oas])

      return ([org_admins], {})

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, starter, prefetcher=prefetcher)

    return response_builder.build()

  def templatePath(self):
    return "v2/modules/gsoc/admin/_accepted_orgs_list.html"


class AcceptedOrgsPublicPage(GSoCRequestHandler):
  """View for the accepted organizations page."""

  def templatePath(self):
    return 'v2/modules/gsoc/accepted_orgs/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'accepted_orgs/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_accepted_orgs'),
        url(r'program/accepted_orgs/%s$' % url_patterns.PROGRAM, self),
        django_url(r'^program/accepted_orgs/%s$' % url_patterns.PROGRAM, self),
    ]

  def checkAccess(self, data, check, mutator):
    check.acceptedOrgsAnnounced()

  def jsonContext(self, data, check, mutator):
    list_content = AcceptedOrgsPublicList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise AccessViolation('You do not have access to this data')

  def context(self, data, check, mutator):
    return {
        'page_name': "Accepted organizations for %s" % data.program.name,
        'accepted_orgs_list': AcceptedOrgsPublicList(data),
        'program_select': ProgramSelect(data, 'gsoc_accepted_orgs'),
    }


class AdminOrgsListPage(GSoCRequestHandler):
  """View that lists all the projects associated with the program."""

  LIST_IDX = 0

  def djangoURLPatterns(self):
    return [
        url(r'admin/accepted_orgs/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GSOC_ORG_LIST_FOR_HOST),
    ]

  def checkAccess(self, data, check, mutator):
    check.isHost()

  def templatePath(self):
    return 'v2/modules/gsoc/admin/list.html'

  def jsonContext(self, data, check, mutator):
    list_content = AdminAcceptedOrgsList(data.request, data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exceptions.AccessViolation('You do not have access to this data')

  def context(self, data, check, mutator):
    return {
      'page_name': 'Organizations list page',
      # TODO(nathaniel): Drop the first parameter of AcceptedOrgsList.
      'list': AdminAcceptedOrgsList(data.request, data)
    }
