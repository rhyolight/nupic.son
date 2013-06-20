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

"""Module containing the view for GCI tasks list page."""

from melange.request import exception
from soc.views.helper import addresses
from soc.views.helper import url_patterns
from soc.views.helper import lists
from soc.views.template import Template

from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper.url_patterns import url


class MentorsList(Template):
  """Template for list of mentors for admins."""

  def __init__(self, data):
    self.data = data

    list_config = lists.ListConfiguration()

    list_config.addPlainTextColumn('name', 'Name',
                          lambda e, *args: e.name().strip())
    list_config.addSimpleColumn('link_id', 'Username')
    list_config.addPlainTextColumn('is_org_admin', 'Org Admin',
        lambda e, *args: 'Yes' if e.is_org_admin else 'No', hidden=True)
    list_config.addSimpleColumn('email', 'Email')
    list_config.addPlainTextColumn(
        'org_admin_for', 'Org Admin For',
        lambda e, org_admin_for, *args: ', '.join(
            [org_admin_for[k].name for k in e.org_admin_for]))
    list_config.addPlainTextColumn(
        'mentor_for', 'Mentor For',
        lambda e, mentor_for, *args: ', '.join(
            [mentor_for[k].name for k in e.mentor_for]))

    addresses.addAddressColumns(list_config)

    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('name')

    self._list_config = list_config

  def context(self):
    description = \
        'List of organization admins and mentors participating in %s' % (
            self.data.program.name)

    list = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)

    return {
        'lists': [list],
    }

  def getListData(self):
    if lists.getListIndex(self.data.request) != 0:
      return None

    q = GCIProfile.all()
    q.filter('program', self.data.program)
    q.filter('is_mentor', True)

    starter = lists.keyStarter
    prefetcher = lists.ListFieldPrefetcher(
        GCIProfile, ['org_admin_for', 'mentor_for'])

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, starter,
        prefetcher=prefetcher)

    return response_builder.build()

  def templatePath(self):
    return 'modules/gci/participants/_mentors_list.html'


class MentorsListAdminPage(GCIRequestHandler):
  """View for the organization admin and mentors page for admin."""

  def templatePath(self):
    return 'modules/gci/participants/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'admin/list/mentors/%s$' % url_patterns.PROGRAM, self,
            name='gci_list_mentors'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isHost()

  def jsonContext(self, data, check, mutator):
    list_content = MentorsList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    return {
        'page_name': "List of organization admins and mentors for %s" % (
            data.program.name),
        'mentors_list': MentorsList(data),
    }
