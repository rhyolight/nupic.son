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

from melange.logic import profile as profile_logic
from melange.request import access
from melange.request import exception

from soc.views.helper import addresses
from soc.views.helper import url_patterns
from soc.views.helper import lists
from soc.views.template import Template

from soc.modules.gci.models import organization as org_model
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper.url_patterns import url


class MentorsList(Template):
  """Template for list of mentors for admins."""

  def __init__(self, data):
    self.data = data

    list_config = lists.ListConfiguration()

    list_config.addPlainTextColumn(
        'name', 'Name', lambda e, *args: e.public_name.strip())
    list_config.addSimpleColumn('profile_id', 'Username')
    list_config.addPlainTextColumn('is_admin', 'Is Admin',
        lambda e, *args: 'Yes' if e.is_admin else 'No', hidden=True)
    list_config.addPlainTextColumn(
        'email', 'Email', lambda entity, *args: entity.contact.email)

    def getMentorFor(entity, *args):
      """Helper function to get value of mentor_for column."""
      org_keys = [org_key.to_old_key() for org_key in entity.admin_for]
      return ', '.join(
          org.name for org in org_model.GCIOrganization.get(org_keys)
              if org)

    def getAdminFor(entity, *args):
      """Helper function to get value of admin_for column."""
      org_keys = [org_key.to_old_key() for org_key in entity.mentor_for]
      return ', '.join(
          org.name for org in org_model.GCIOrganization.get(org_keys) if org)

    list_config.addPlainTextColumn('admin_for', 'Admin For', getAdminFor)
    list_config.addPlainTextColumn('mentor_for', 'Mentor For', getMentorFor)

    addresses.addAddressColumns(list_config)

    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('name')

    self._list_config = list_config

  def context(self):
    description = \
        'List of organization admins and mentors participating in %s' % (
            self.data.program.name)

    return {
        'lists': [lists.ListConfigurationResponse(
            self.data, self._list_config, 0, description)],
    }

  def getListData(self):
    if lists.getListIndex(self.data.request) != 0:
      return None

    query = profile_logic.queryAllMentorsForProgram(self.data.program.key())
    import logging
    logging.error(query.fetch(1000))

    starter = lists.keyStarter

    # TODO(daniel): enable prefetching for the list (mentor_for, admin_for)
    prefetcher = None

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, query, starter,
        prefetcher=prefetcher)

    return response_builder.build()

  def templatePath(self):
    return 'modules/gci/participants/_mentors_list.html'


class MentorsListAdminPage(GCIRequestHandler):
  """View for the organization admin and mentors page for admin."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gci/participants/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'admin/list/mentors/%s$' % url_patterns.PROGRAM, self,
            name='gci_list_mentors'),
    ]

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
