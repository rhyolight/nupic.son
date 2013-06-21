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

"""Module for the GCI participant dashboard."""

import json
import logging

from google.appengine.ext import db

from django import http
from django.utils.dateformat import format
from django.utils.translation import ugettext

from melange.request import exception
from soc.logic import document as document_logic
from soc.logic import org_app as org_app_logic
from soc.models import document as soc_document_model
from soc.models.org_app_record import OrgAppRecord
from soc.views.dashboard import Component
from soc.views.dashboard import Dashboard
from soc.views.helper import lists
from soc.views.helper import url_patterns

from soc.modules.gci.logic import document as gsoc_document_logic
from soc.modules.gci.logic import task as task_logic
from soc.modules.gci.models.request import GCIRequest
from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.gci.models.profile import GCIProfile
from soc.modules.gci.models.task import CLAIMABLE
from soc.modules.gci.models.task import GCITask
from soc.modules.gci.models.task import UNPUBLISHED
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url


BACKLINKS_TO_MAIN = {'to': 'main', 'title': 'Main dashboard'}
BIRTHDATE_FORMAT = 'd-m-Y'
DATETIME_FORMAT = 'Y-m-d H:i:s'


class MainDashboard(Dashboard):
  """Dashboard for user's main-dashboard
  """

  def __init__(self, data):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
    """
    super(MainDashboard, self).__init__(data)
    self.subpages = []

  def context(self):
    """Returns the context of main dashboard."""
    return {
        'title': 'Participant dashboard',
        'name': 'main',
        'subpages': self._divideSubPages(self.subpages),
        'enabled': True
    }

  def addSubpages(self, subpage):
    self.subpages.append(subpage)


class ComponentsDashboard(Dashboard):
  """Dashboard that holds component list."""

  def __init__(self, data, component_property):
    """Initializes the dashboard.

    Args:
      data: The RequestData object
      component_property: Component property
    """
    super(ComponentsDashboard, self).__init__(data)
    self.name = component_property.get('name')
    self.title = component_property.get('title')
    self.components = [component_property.get('component'),]
    self.backlinks = [component_property.get('backlinks'),]

  def context(self):
    """Returns the context of components dashboard.
    """
    return {
        'title': self.title,
        'name': self.name,
        'backlinks': self.backlinks,
        'components': self.components,
    }


# TODO(nathaniel): Make all attributes of this class private except
# those that fulfill the RequestHandler type.
class DashboardPage(GCIRequestHandler):
  """View for the participant dashboard."""

  def djangoURLPatterns(self):
    """The URL pattern for the dashboard."""
    return [
        url(r'dashboard/%s$' % url_patterns.PROGRAM, self,
            name='gci_dashboard')]

  def checkAccess(self, data, check, mutator):
    """Denies access if you are not logged in."""
    check.isProfileActive()

  def templatePath(self):
    """Returns the path to the template."""
    return 'modules/gci/dashboard/base.html'

  def populateDashboards(self, data):
    """Populates the various dashboard subpages and components for each subpage.
    """
    # dashboard container, will hold each component list
    dashboards = []

    # main container that contains all component list
    main = MainDashboard(data)

    # retrieve active links and add it to the main dashboard
    links = self.links(data)
    for link in links:
      main.addSubpages(link)

    # retrieve active component(s) for currently logged-in user
    components = self.components(data)

    # add components as children of main dashboard and treat the component
    # as dashboard element
    for component in components:
      c = {
          'name': component.context().get('name'),
          'description': component.context().get('description'),
          'title': component.context().get('title'),
          'component_link': True,
          }
      main.addSubpages(c)

      dashboards.append(ComponentsDashboard(data, {
          'name': component.context().get('name'),
          'title': component.context().get('title'),
          'component': component,
          'backlinks': BACKLINKS_TO_MAIN,
          }))

    dashboards.append(main)

    return dashboards

  def shouldSubmitForms(self, data):
    """Checks if the current user should submit the student forms.

    Args:
      data: A RequestData describing the current request.

    Returns: A pair of booleans the first of which indicates whether
      or not the student should submit their Student ID form and the
      second of which indicates whether or not the student should
      submit their Consent form.
    """
    if data.student_info:
      return (not data.student_info.student_id_form,
              not data.student_info.consent_form)
    else:
      return False, False

  def context(self, data, check, mutator):
    """Handler for default HTTP GET request."""
    context = {
        'page_name': data.program.name,
        'user_name': data.user.name if data.user else None,
        }

    # Check if the student should submit either of the forms
    student_id_form, consent_form = self.shouldSubmitForms(data)
    context['student_id_form'] = student_id_form
    context['consent_form'] = consent_form

    context['dashboards'] = self.populateDashboards(data)

    return context

  def jsonContext(self, data, check, mutator):
    """Handler for JSON requests."""
    for component in self.components(data):
      list_content = component.getListData()
      if list_content:
        return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def post(self, data, check, mutator):
    """Handler for POST requests for each component."""
    for component in self.components(data):
      if component.post():
        return http.HttpResponse()
    else:
      raise exception.Forbidden(message='You cannot change this data')

  def components(self, data):
    """Returns the list components that are active on the page.

    Args:
      data: A RequestData describing the current request.

    Returns:
      The list components that are active on the page.
    """
    components = []

    if data.student_info:
      components += self._getStudentComponents(data)
    elif data.is_org_admin:
      components += self._getOrgAdminComponents(data)
      components += self._getMentorComponents(data)
    elif data.is_mentor:
      components += self._getMentorComponents(data)

    return components

  def _getStudentComponents(self, data):
    """Get the dashboard components for a student."""
    return [DocumentComponent(data)]

  def _getMentorComponents(self, data):
    """Get the dashboard components for Organization members."""
    components = []

    components.append(DocumentComponent(data))

    component = self._getMyOrgApplicationsComponent(data)
    if component:
      components.append(component)

    components.append(MyOrgsTaskList(data))

    # add org list just before creating task and invitation, so mentor can
    # choose which organization the task or invitite will be created for
    components.append(MyOrgsListBeforeCreateTask(data))

    return components

  def _getOrgAdminComponents(self, data):
    """Get the dashboard components for org admins."""
    components = []

    # add list of mentors component
    components.append(MyOrgsMentorsList(data))

    # add invite mentors component
    components.append(MyOrgsListBeforeInviteMentor(data))

    # add invite org admins component
    components.append(MyOrgsListBeforeInviteOrgAdmin(data))

    # add list of all the invitations
    components.append(OrgAdminInvitesList(data))

    # add bulk create tasks component
    components.append(MyOrgsListBeforeBulkCreateTask(data))

    # add edit org profile component
    components.append(MyOrgsListBeforeOrgProfile(data))

    # add org scores component
    components.append(MyOrgsScoresList(data))

    return components

  def _getMyOrgApplicationsComponent(self, data):
    """Returns MyOrgApplicationsComponent iff this user is main_admin or
    backup_admin in an application.
    """
    survey = org_app_logic.getForProgram(data.program)

    # Test if this user is main admin or backup admin
    q = OrgAppRecord.all()
    q.filter('survey', survey)
    q.filter('main_admin', data.user)

    record = q.get()

    q = OrgAppRecord.all()
    q.filter('survey', survey)
    q.filter('backup_admin', data.user)

    if record or q.get():
      # add a component showing the organization application of the user
      return MyOrgApplicationsComponent(data, survey)

    return None

  def links(self, data):
    """Returns additional links of main dashboard that are active on the page.

    Args:
      data: A RequestData describing the current request.

    Returns:
      Additional links of the main dashboard that are active on the page.
    """
    links = []

    # TODO(nathaniel): Does there have to be so much control flow here? Must
    # this function be responsible for enforcing students-cannot-also-be-
    # any-other-role or might enforcement of that rule elsewhere be enough?
    if data.student_info:
      links += self._getStudentLinks(data)
    else:
      if data.is_org_admin:
        links += self._getOrgAdminLinks(data)
      if data.is_mentor:
        links += self._getMentorLinks(data)

    return links

  def _getStudentLinks(self, data):
    """Get the main dashboard links for student."""
    links = [
        self._getStudentFormsLink(data),
        self._getMyTasksLink(data),
        self._getMySubscribedTasksLink(data)
        ]

    current_task = task_logic.queryCurrentTaskForStudent(data.profile).get()
    if current_task:
      links.append(self._getCurrentTaskLink(data, current_task))

    return links

  def _getOrgAdminLinks(self, data):
    """Get the main dashboard links for org-admin."""
    links = []

    # add propose winners component
    if data.timeline.allReviewsStopped():
      links.append(self._getProposeWinnersLink(data))
    return links

  def _getMentorLinks(self, data):
    """Get the main dashboard links for mentor."""
    return []

  def _getMyInvitationsLink(self, data):
    """Get the link of incoming invitations list (invitations sent to me)."""
    # TODO(nathaniel): This doesn't appear to be used?
    r = data.redirect
    r.program()

    return {
        'name': 'list_invites',
        'description': ugettext(
            'List of all invites which have been sent to me.'),
        'title': 'Invites to me',
        'link': r.urlOf(url_names.GCI_LIST_INVITES)
        }

  def _getMyOrgInvitationsLink(self, data):
    """Get the link of outgoing invitations list (invitations sent by my orgs).
    """
    # TODO(nathaniel): This also doesn't appear to be used?
    r = data.redirect
    r.program()

    return {
        'name': 'list_org_invites',
        'description': ugettext(
            'List of all invites which have been sent by my organizations.'),
        'title': 'My organization outgoing invitations',
        'link': r.urlOf(url_names.GCI_LIST_ORG_INVITES)
        }

  def _getStudentFormsLink(self, data):
    """Get the link for uploading student forms."""
    r = data.redirect
    r.program()

    return {
        'name': 'form_uploads',
        'description': ugettext(
            'Upload student id and parental consent forms.'),
        'title': 'Form uploads',
        'link': r.urlOf(url_names.GCI_STUDENT_FORM_UPLOAD)
        }

  def _getMyTasksLink(self, data):
    """Get the link to the list of all the tasks for the student
    who is currently logged in.
    """
    r = data.redirect
    r.profile(data.user.link_id)

    return {
        'name': 'student_tasks',
        'description': ugettext(
            'List of the tasks that you have completed so far in the program'),
        'title': 'My completed tasks',
        'link': r.urlOf(url_names.GCI_STUDENT_TASKS)
        }

  def _getCurrentTaskLink(self, data, current_task):
    """Get the link to the task that the student is currently working on.
    """
    r = data.redirect
    r.id(current_task.key().id())

    return {
        'name': 'current_task',
        'description': ugettext(
            'The task you are currently working on'),
        'title': 'My current task',
        'link': r.urlOf('gci_view_task')
        }

  def _getMySubscribedTasksLink(self, data):
    """Get the link to the list of all the tasks the current logged in user
    is subscribed to.
    """
    # TODO(nathaniel): make this .profile call unnecessary.
    data.redirect.profile(data.user.link_id)

    return {
        'name': 'subscribed_tasks',
        'description': ugettext(
            'List of the tasks that you have subscribed to'),
        'title': 'My subscribed tasks',
        'link': data.redirect.urlOf(url_names.GCI_SUBSCRIBED_TASKS)
        }

  def _getProposeWinnersLink(self, data):
    """Get the link to the list of organization to propose winners for."""
    r = data.redirect
    r.program()

    return {
        'name': 'propose_winners',
        'description': ugettext(
            'Propose the Grand Prize Winners'),
        'title': 'Propose the Grand Prize Winners',
        'link': r.urlOf(url_names.GCI_ORG_CHOOSE_FOR_PROPOSE_WINNNERS)
        }


class MyOrgApplicationsComponent(Component):
  """Component for listing the Organization Applications of the current user.
  """

  # TODO(nathaniel): Huh? This constructor calls its super constructor twice?
  def __init__(self, data, survey):
    """Initializes the component.

    Args:
      data: The RequestData object
      survey: the OrgApplicationSurvey entity
    """
    super(MyOrgApplicationsComponent, self).__init__(data)

    # passed in so we don't have to do double queries
    self.survey = survey

    list_config = lists.ListConfiguration()

    list_config.addSimpleColumn('name', 'Name')
    list_config.addSimpleColumn('org_id', 'Organization ID')
    list_config.addPlainTextColumn(
        'created', 'Created On',
        lambda ent, *args: format(ent.created, DATETIME_FORMAT))
    list_config.addPlainTextColumn(
        'modified', 'Last Modified On',
        lambda ent, *args: format(ent.modified, DATETIME_FORMAT))

    if self.data.timeline.surveyPeriod(survey):
      url_name = 'gci_retake_org_app'
    else:
      url_name = 'gci_show_org_app'

    list_config.setRowAction(
        lambda e, *args: data.redirect.id(e.key().id()).
            urlOf(url_name))

    self._list_config = list_config

    super(MyOrgApplicationsComponent, self).__init__(data)

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return 'modules/gci/dashboard/list_component.html'

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=0, preload_list=False)

    return {
        'name': 'org_app',
        'title': 'My organization applications',
        'lists': [list],
        'description': ugettext('My organization applications'),
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.data.request) != 0:
      return None

    q = OrgAppRecord.all()
    q.filter('survey', self.survey)
    q.filter('main_admin', self.data.user)

    records = q.fetch(1000)

    q = OrgAppRecord.all()
    q.filter('survey', self.survey)
    q.filter('backup_admin', self.data.user)

    records.extend(q.fetch(1000))

    response = lists.ListContentResponse(self.data.request, self._list_config)

    for record in records:
      response.addRow(record)
    response.next = 'done'

    return response

class MyOrgsTaskList(Component):
  """Component for listing the tasks of the orgs of the current user.
  """

  IDX = 1
  PUBLISH_BUTTON_ID = 'publish'
  UNPUBLISH_BUTTON_ID = 'unpublish'

  def __init__(self, data):
    """Initializes the component.

    Args:
      data: The RequestData object
    """
    super(MyOrgsTaskList, self).__init__(data)

    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('title', 'Title')
    list_config.addPlainTextColumn(
        'org', 'Organization', lambda ent, *args: ent.org.name)
    list_config.addPlainTextColumn(
        'type', 'Type', lambda entity, *args: ", ".join(entity.types))
    list_config.addPlainTextColumn(
        'tags', 'Tags', lambda entity, *args: ", ".join(entity.tags))
    list_config.addPlainTextColumn(
        'time_to_complete', 'Time to complete',
        lambda entity, *args: entity.taskTimeToComplete())


    list_config.addPlainTextColumn(
        'mentors', 'Mentors',
        lambda entity, mentors, *args: ', '.join(
            mentors[i].name() for i in entity.mentors))

    list_config.addSimpleColumn('description', 'Description', hidden=True)
    list_config.addPlainTextColumn(
        'student', 'Student',
        lambda ent, *args: ent.student.name() if ent.student else '',
        hidden=True)
    list_config.addPlainTextColumn(
        'created_by', 'Created by',
        lambda entity, *args: entity.created_by.name() \
            if entity.created_by else '',
        hidden=True)
    list_config.addPlainTextColumn(
        'modified_by', 'Modified by',
        lambda entity, *args: entity.modified_by.name() \
            if entity.modified_by else '',
        hidden=True)
    list_config.addPlainTextColumn(
        'created_on', 'Created on',
        lambda entity, *args: format(entity.created_on, DATETIME_FORMAT) \
            if entity.created_on else '',
        hidden=True)
    list_config.addPlainTextColumn(
        'modified_on', 'Modified on',
        lambda entity, *args: format(entity.modified_on, DATETIME_FORMAT) \
            if entity.modified_on else '',
        hidden=True)
    list_config.addPlainTextColumn('closed_on', 'Closed on',
        lambda entity, *args: format(
            entity.closed_on, DATETIME_FORMAT) if entity.closed_on else '',
        hidden=True)
    list_config.addSimpleColumn('status', 'Status')

    # TODO (madhu): Super temporary solution until the pretty lists are up.
    list_config.addHtmlColumn('edit', 'Edit',
        lambda entity, *args: (
          '<a href="%s" style="color:#0000ff;text-decoration:underline;">'
          'Edit</a>' % (data.redirect.id(entity.key().id()).urlOf(
              'gci_edit_task'))))

    list_config.setRowAction(
        lambda e, *args: data.redirect.id(e.key().id()).
            urlOf('gci_view_task'))

    # Add publish/unpublish buttons to the list and enable per-row checkboxes.
    #
    # It is very important to note that the setRowAction should go before
    # addPostButton call for the checkbox to be present on the list.
    # setRowAction sets multiselect attribute to False which is set to True
    # by addPostButton method and should be True for the checkbox to be
    # present on the list.
    if data.is_org_admin:
      # publish/unpublish tasks
      bounds = [1,'all']
      # GCITask is keyed based solely on the entity ID, because it is very
      # difficult to group it with either organizations or profiles, so to
      # make the querying easier across entity groups we only use entity ids
      # as keys.
      keys = ['key']
      list_config.addPostButton(
          self.PUBLISH_BUTTON_ID, 'Publish', '', bounds, keys)
      list_config.addPostButton(
          self.UNPUBLISH_BUTTON_ID, 'Unpublish', '', bounds, keys)

    self._list_config = list_config

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'modules/gci/dashboard/list_component.html'

  def post(self):
    """Processes the form post data by checking what buttons were pressed.
    """
    idx = lists.getListIndex(self.data.request)
    if idx != self.IDX:
      return None

    data = self.data.POST.get('data')

    if not data:
      raise exception.BadRequest(message='Missing data')

    parsed = json.loads(data)

    button_id = self.data.POST.get('button_id')

    if not button_id:
      raise exception.BadRequest(message='Missing button_id')

    if button_id == self.PUBLISH_BUTTON_ID:
      return self.postPublish(parsed, True)

    if button_id == self.UNPUBLISH_BUTTON_ID:
      return self.postPublish(parsed, False)

    raise exception.BadRequest(message="Unknown button_id")

  def postPublish(self, data, publish):
    """Publish or unpublish tasks based on the value in the publish parameter.

    Args:
      data: Parsed post data containing the list of of task keys
      publish: True if the task is to be published, False to unpublish
    """
    for properties in data:
      task_key = properties.get('key')
      if not task_key:
        logging.warning("Missing key in '%s'" % properties)
        continue
      if not task_key.isdigit():
        logging.warning("Invalid task id in '%s'" % properties)
        continue

      def publish_task_txn():
        task = GCITask.get_by_id(int(task_key))

        if not task:
          logging.warning("Task with task_id '%s' does not exist" % (
              task_key,))
          return

        org_key = GCITask.org.get_value_for_datastore(task)
        if not self.data.orgAdminFor(org_key):
          logging.warning('Not an org admin')
          return

        if publish:
          if task.status in UNPUBLISHED:
            task.status = 'Open'
            task.put()
          else:
            logging.warning('Trying to publish task with %s status.' %
                task.status)
        else:
          if task.status == 'Open':
            task.status = 'Unpublished'
            task.put()
          else:
            logging.warning('Trying to unpublish task with %s status.' %
                task.status)

      db.run_in_transaction(publish_task_txn)
    return True

  def context(self):
    """Returns the context of this component.
    """
    task_list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.IDX, preload_list=False)

    return {
        'name': 'all_org_tasks',
        'title': 'All tasks for my organizations',
        'lists': [task_list],
        'description': ugettext('List of all tasks for my organization'),
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.data.request) != 1:
      return None

    q = GCITask.all()
    q.filter('program', self.data.program)
    q.filter('org IN', self.data.mentor_for)

    starter = lists.keyStarter
    prefetcher = lists.ListModelPrefetcher(
        GCITask, ['org', 'student', 'created_by', 'modified_by'], ['mentors'])

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, starter,
        prefetcher=prefetcher)

    return response_builder.build()


class MyOrgsList(Component):
  """Component for listing the orgs of the current user.

  Since mentor_for is a list of orgs, we need to give org selection first
  """

  def __init__(self, data):
    """Initializes the component.

    Args:
      data: The RequestData object
    """
    super(MyOrgsList, self).__init__(data)

    list_config = lists.ListConfiguration()

    list_config.addSimpleColumn('name', 'Organization Name')

    self._list_config = list_config

    self._setRowAction(data.request, data)

    self._setIdx()

  def _setIdx(self):
    raise NotImplemented

  # TODO(nathaniel): Drop the "request" parameter of this method.
  def _setRowAction(self, request, data):
    """Since setRowAction can be vary, it must be implemented individually.
    """
    raise NotImplemented

  def _getContext(self):
    raise NotImplemented

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'modules/gci/dashboard/list_component.html'

  def context(self):
    """Returns the context of this component.
    """
    return self._getContext()

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.data.request) != self.idx:
      return None

    response = lists.ListContentResponse(self.data.request, self._list_config)

    for org in self.data.mentor_for:
      response.addRow(org)

    response.next = 'done'

    return response


class MyOrgsListBeforeCreateTask(MyOrgsList):
  """Component for listing the orgs of the current user, just before creating
  task.
  """

  def _setIdx(self):
    self.idx = 2

  def _getContext(self):
    org_list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx, preload_list=False)

    return {
        'name': 'create_tasks',
        'title': 'Create Task',
        'lists': [org_list],
        'description': ugettext('Create task for students. Since you may '
            'belong to more than one organizations, you need to choose one '
            'organization you will create the task for.')}

  def _setRowAction(self, request, data):
    # TODO(nathaniel): squeeze this back into a lambda expression in the
    # setRowAction call below.
    def RowAction(e, *args):
      # TODO(nathaniel): make this .organization call unnecessary.
      data.redirect.organization(organization=e)

      return data.redirect.urlOf('gci_create_task')

    self._list_config.setRowAction(RowAction)


class MyOrgsListBeforeBulkCreateTask(MyOrgsList):
  """Component for listing the orgs of the current user, just before creating
  task.
  """

  def _setIdx(self):
    self.idx = 3

  def _getContext(self):
    org_list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx, preload_list=False)

    return {
        'name': 'bulk_create_tasks',
        'title': 'Bulk Upload Tasks',
        'lists': [org_list],
        'description': ugettext('Bulk upload tasks. Since you may '
            'belong to more than one organizations, you need to choose one '
            'organization you will upload the tasks for.')}

  def _setRowAction(self, request, data):
    # TODO(nathaniel): squeeze this back into a lambda expression in the
    # setRowAction call below.
    def RowAction(e, *args):
      # TODO(nathaniel): make this .organization call unnecessary.
      data.redirect.organization(organization=e)

      return data.redirect.urlOf(url_names.GCI_TASK_BULK_CREATE)

    self._list_config.setRowAction(RowAction)


class MyOrgsListBeforeInviteMentor(MyOrgsList):
  """Component for listing the orgs of the current user, just before creating
  invite.
  """

  def _setIdx(self):
    self.idx = 4

  def _getContext(self):
    org_list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx, preload_list=False)

    return {
        'name': 'invite_mentor',
        'title': 'Invite Mentor',
        'lists': [org_list],
        'description': ugettext('Invite mentors to be part of your '
            'organization.')}

  def _setRowAction(self, request, data):
    r = data.redirect

    self._list_config.setRowAction(
        lambda e, *args: r.invite('mentor', e)
            .urlOf(url_names.GCI_SEND_INVITE))


class MyOrgsListBeforeInviteOrgAdmin(MyOrgsList):
  """Component for listing the organizations of the current user, just before
  he or she creates a new org admin invite.
  """

  def _setIdx(self):
    self.idx = 5

  def _getContext(self):
    org_list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx, preload_list=False)

    return {
        'name': 'invite_org_admin',
        'title': 'Invite Org Admin',
        'lists': [org_list],
        'description': ugettext('Invite org admins to be part of your '
            'organization. Please note that once they accept your invitation, '
            'they will become mentors too.')}

  def _setRowAction(self, request, data):
    r = data.redirect

    self._list_config.setRowAction(
        lambda e, *args: r.invite('org_admin', e)
            .urlOf(url_names.GCI_SEND_INVITE))


class MyOrgsScoresList(MyOrgsList):
  """Component for listing all organizations for which the current user may
  see scores of the students.
  """

  def _setIdx(self):
    self.idx = 12

  def _setRowAction(self, request, data):
    # TODO(nathaniel): squeeze this back into a lambda expression in the
    # call to setRowAction below.
    def RowAction(e, *args):
      # TODO(nathaniel): make this .organization call unnecessary.
      data.redirect.organization(organization=e)

      return data.redirect.urlOf(url_names.GCI_ORG_SCORES)

    self._list_config.setRowAction(RowAction)

  def getListData(self):
    if lists.getListIndex(self.data.request) != self.idx:
      return None

    q = GCIOrganization.all()
    q.filter('__key__ IN', self.data.profile.org_admin_for)
    q.filter('status IN', ['new', 'active'])

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, lists.keyStarter)

    return response_builder.build()

  def _getContext(self):
    org_list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx, preload_list=False)

    return {
        'name': 'orgs_scores',
        'title': 'Student scores for my organizations',
        'lists': [org_list],
        'description': ugettext('See the students who have completed'
            'at least one task for your organizations.')}


class MyOrgsMentorsList(Component):
  """Component for listing the mentors of the orgs of the current user.
  """

  def __init__(self, data):
    """Initializes the component.

    Args:
      data: The RequestData object
    """
    super(MyOrgsMentorsList, self).__init__(data)

    list_config = lists.ListConfiguration()

    list_config.addSimpleColumn('public_name', 'Name')
    list_config.addSimpleColumn('link_id', 'Username')
    list_config.addSimpleColumn('email', 'Email')

    self._list_config = list_config

  def templatePath(self):
    """Returns the path to the template that should be used in render().
    """
    return'modules/gci/dashboard/list_component.html'

  def context(self):
    """Returns the context of this component.
    """
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=6, preload_list=False)

    return {
        'name': 'all_orgs_mentors',
        'title': 'All mentors for my organizations',
        'lists': [list],
        'description': ugettext('List of all mentors for my organizations'),
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    if lists.getListIndex(self.data.request) != 6:
      return None

    q = GCIProfile.all()
    q.filter('mentor_for IN', self.data.org_admin_for)

    starter = lists.keyStarter

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, starter)

    return response_builder.build()


class MyOrgsListBeforeOrgProfile(MyOrgsList):
  """Component for listing the orgs of the current user, just before
  create/edit org's profile.
  """

  def _setIdx(self):
    # TODO(nathaniel): Magic number.
    self.idx = 7

  def _getContext(self):
    org_list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx, preload_list=False)

    return {
        'name': 'edit_org_profile',
        'title': 'Edit organization profile',
        'lists': [org_list],
        'description': ugettext('Edit organization profile. Since you may '
            'belong to more than one organizations, you need to choose one '
            'organization you will edit the profile for.')}

  def _setRowAction(self, request, data):
    # TODO(nathaniel): squeeze this back into a lambda expression in the
    # call to setRowAction below.
    def RowAction(e, *args):
      # TODO(nathaniel): make this .organization call unnecessary.
      data.redirect.organization(organization=e)

      return data.redirect.urlOf(url_names.EDIT_GCI_ORG_PROFILE, secure=True)

    self._list_config.setRowAction(RowAction)


class OrgAdminInvitesList(Component):
  """Template for list of invites that have been sent by the organizations
  that the current user is organization admin for.
  """

  def __init__(self, data):
    self.data = data
    r = data.redirect

    # GCIRequest entities have user entities as parents, so the keys
    # for the list items should be parent scoped.
    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addPlainTextColumn('key', 'Key',
        (lambda ent, *args: "%s/%s" % (
            ent.parent().key().name(), ent.key().id())), hidden=True)
    list_config.addPlainTextColumn('to', 'To',
        lambda entity, *args: entity.user.name)
    list_config.addSimpleColumn('status', 'Status')

    # organization column should be added only if the user is an administrator
    # for more than one organization
    if len(self.data.org_admin_for) > 1:
      list_config.addPlainTextColumn('org', 'From',
        lambda entity, *args: entity.org.name)

    list_config.setRowAction(
        lambda e, *args: r.userId(e.parent_key().name(), e.key().id())
            .urlOf(url_names.GCI_MANAGE_INVITE))

    self.idx = 9
    self._list_config = list_config

  def getListData(self):
    if lists.getListIndex(self.data.request) != self.idx:
      return None

    q = GCIRequest.all()
    q.filter('type', 'Invitation')
    q.filter('org IN', [e.key() for e in self.data.org_admin_for])

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, lists.keyStarter)

    return response_builder.build()

  def context(self):
    invite_list = lists.ListConfigurationResponse(
        self.data, self._list_config, self.idx)

    return {
        'name': 'outgoing_invitations',
        'title': 'Outgoing Invitations',
        'lists': [invite_list],
        'description': ugettext(
            'See all the invitations that have been sent '
            'by your organizations.')
    }

  def templatePath(self):
    return 'modules/gci/dashboard/list_component.html'


class DocumentComponent(Component):
  """Component listing all the documents for the current user.
  """

  IDX = 10

  def __init__(self, data):
    """Initializes this component.
    """
    self.data = data
    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn(
        'title', 'Title', lambda ent, *args: ent.name())

    list_config.setRowAction(
        lambda e, *args: self.data.redirect.document(e).urlOf(
            'show_gci_document'))

    self._list_config = list_config

    super(DocumentComponent, self).__init__(data)

  def templatePath(self):
    return'modules/gci/dashboard/list_component.html'

  def getListData(self):
    idx = lists.getListIndex(self.data.request)

    if idx != self.IDX:
      return None

    visibilities = gsoc_document_logic.getVisibilities(self.data)
    q = document_logic.getDocumentQueryForRoles(self.data, visibilities)

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, q, lists.keyStarter)
    return response_builder.build()

  def context(self):
    list_config = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.IDX, preload_list=False)

    return {
        'name': 'documents',
        'title': 'Important documents',
        'lists': [list_config],
        'description': ugettext('List of important documents'),
    }
