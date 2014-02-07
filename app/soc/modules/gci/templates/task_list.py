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

"""Module containing template with a list of GCITask entities."""

from google.appengine.ext import ndb

from soc.views.helper import lists
from soc.views.template import Template

from soc.modules.gci.models.task import GCITask


class TaskList(Template):
  """Template for list of tasks."""

  def __init__(self, data):
    self.data = data

    self._columns = self._getColumns()
    self._list_config = self._getListConfig()

  def context(self):
    description = self._getDescription()

    task_list = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)

    return {
        'lists': [task_list],
    }

  def getListData(self):
    idx = lists.getListIndex(self.data.request)
    if idx == 0:
      query = self._getQuery()

      starter = lists.keyStarter
      prefetcher = self._getPrefetcher()

      response_builder = lists.RawQueryContentResponseBuilder(
          self.data.request, self._list_config, query,
          starter=starter, prefetcher=prefetcher)

      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return 'modules/gci/task/_task_list.html'

  def _getColumns(self):
    raise NotImplementedError

  def _getDescription(self):
    raise NotImplementedError

  def _getPrefetcher(self):
    fields = []
    list_fields = []

    if 'org' in self._columns:
      fields.append('org')

    # TODO(daniel): re-enable prefetching (mentor)
    # if 'mentors' in self._columns:
    # list_fields.append('mentors')

    return lists.ListModelPrefetcher(GCITask, fields, list_fields)

  def _getListConfig(self):
    list_config = lists.ListConfiguration()

    def getMentors(entity, *args):
      """Helper function to get value for mentors column."""
      mentors = ndb.get_multi(
          map(ndb.Key.from_old_key,
              GCITask.mentors.get_value_for_datastore(entity)))
      return ', '.join(mentor.public_name for mentor in mentors if mentor)

    if 'title' in self._columns:
      list_config.addSimpleColumn('title', 'Title')

    if 'organization' in self._columns:
      list_config.addPlainTextColumn('org', 'Organization',
          lambda entity, *args: entity.org.name)

    if 'mentors' in self._columns:
      list_config.addPlainTextColumn('mentors', 'Mentors', getMentors)

    if 'types' in self._columns:
      list_config.addPlainTextColumn('types', 'Category',
          lambda entity, *args: ', '.join(entity.types))

    if 'tags' in self._columns:
      list_config.addPlainTextColumn('tags', 'Tags',
          lambda entity, *args: ', '.join(entity.tags))

    if 'status' in self._columns:
      list_config.addSimpleColumn('status', 'Status')

    list_config.setRowAction(
        lambda e, *args: self.data.redirect.id(e.key().id()).urlOf(
            'gci_view_task'))

    return list_config

  def _getQuery(self):
    raise NotImplementedError
