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
into a GSoC program, excluding those which have been withdrawn
or failed one of the evaluations.
"""

from google.appengine.ext import ndb

from melange.request import exception
from melange.request import links

from soc.views import base_templates
from soc.views.helper import lists
from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gsoc.logic import project as project_logic
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper.url_patterns import url
from soc.modules.gsoc.views.helper import url_names


class ProjectList(Template):
  """Template for listing the student projects accepted in the program."""

  class ListPrefetcher(lists.ListModelPrefetcher):
    """Prefetcher used to improve performance of when the list is loaded.

    See lists.ListModelPrefetcher for specification.
    """

    def prefetch(self, entities):
      """Prefetches GSoCProfiles corresponding to Mentors for the specified
      list of GSoCProfile entities.

      See lists.ListModelPrefetcher.prefetch for specification.

      Args:
        entities: the specified list of GSoCProject instances

      Returns:
        prefetched GSoCProfile entities in a structure whose format is
        described in lists.ListModelPrefetcher.prefetch
      """
      prefetched_list, _ = super(
          ProjectList.ListPrefetcher, self).prefetch(entities)

      mentor_names = {}
      for e in entities:
        mentor_names[e.key()] = ', '.join(
            [prefetched_list[0][m_key].name() for m_key in e.mentors])

      return [mentor_names], {}


  DEFAULT_IDX = 0

  def __init__(self, data, query, idx=None, row_action=None):
    """Initializes a new object.

    Args:
      data: RequestData object associated with the request
      query: query to be used to retrieve Project entities
      idx: index of the list
      row_action: an optional function that defines row action.
    """
    self.data = data
    self.query = query

    self.idx = self.DEFAULT_IDX if idx is None else idx

    def getOrganization(entity, *args):
      """Helper function to get value for organization column."""
      org_key = GSoCProject.org.get_value_for_datastore(entity)
      return ndb.Key.from_old_key(org_key).get().name

    def getStudent(entity, *args):
      """Helper function to get value for student column."""
      return ndb.Key.from_old_key(entity.parent_key()).get().public_name

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('student', 'Student', getStudent)
    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn('org', 'Organization', getOrganization)
    list_config.addSimpleColumn('status', 'Status', hidden=True)
    list_config.addPlainTextColumn(
        'mentors', 'Mentors',
        lambda entity, *args: ', '.join(
            mentor.public_name for mentor in entity.getMentors()))

    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('student')

    if row_action:
      list_config.setRowAction(row_action(data))
    else:
      list_config.setRowAction(self._getDefaultRowAction())

    self._list_config = list_config

  def context(self):
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx,
        description='List of projects accepted into %s' % (
            self.data.program.name))

    return {
        'lists': [list_configuration_response],
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.data.request)
    if idx == self.idx:
      starter = lists.keyStarter
      # TODO(daniel): enable prefetching from ndb models
      # ('org', 'mentors', 'parent')
      prefetcher = None

      response_builder = lists.RawQueryContentResponseBuilder(
          self.data.request, self._list_config, self.query,
          starter, prefetcher=prefetcher)
      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return "modules/gsoc/projects_list/_project_list.html"

  def _getDefaultRowAction(self):
    """Returns defualt row action for this list that redirects to the page
    with project details.

    Returns:
      a lambda expression that takes a project entity as its first argument
        and returns URL to the page with details of that project.
    """
    return lambda e, *args: links.LINKER.userId(
        e.parent_key(), e.key().id(), url_names.GSOC_PROJECT_DETAILS)


class ListProjects(base.GSoCRequestHandler):
  """View methods for listing all the projects accepted into a program."""

  def templatePath(self):
    return 'modules/gsoc/projects_list/base.html'

  def djangoURLPatterns(self):
    """Returns the list of tuples for containing URL to view method mapping."""

    return [
        url(r'projects/list/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_accepted_projects')
    ]

  def checkAccess(self, data, check, mutator):
    """Access checks for the view."""
    check.acceptedStudentsAnnounced()

  def jsonContext(self, data, check, mutator):
    """Handler for JSON requests."""
    list_query = project_logic.getAcceptedProjectsQuery(
        program=data.program)
    list_content = ProjectList(data, list_query).getListData()

    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    """Handler for GSoC Accepted Projects List page HTTP get request."""
    program = data.program
    list_query = project_logic.getAcceptedProjectsQuery(program=data.program)

    return {
        'page_name': '%s - Accepted Projects' % program.short_name,
        'program_name': program.name,
        'project_list': ProjectList(data, list_query),
        'program_select': base_templates.DefaultProgramSelect(
            data, 'gsoc_accepted_projects'),
    }
