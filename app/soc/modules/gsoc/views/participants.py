# Copyright 2013 the Melange authors.
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

"""Module containing the view for GSoC participants list page."""

from django.utils import translation

from google.appengine.ext import ndb

from melange.logic import profile as profile_logic
from melange.request import access
from melange.request import exception
from soc.views.helper import addresses
from soc.views.helper import url_patterns
from soc.views.helper import lists
from soc.views.template import Template
from soc.modules.gsoc.views.base import GSoCRequestHandler
from soc.modules.gsoc.views.helper.url_patterns import url

from summerofcode.logic import profile as soc_profile_logic
from summerofcode.request import links
from summerofcode.views.helper import urls


class MentorsList(Template):
  """Template for list of mentors for admins."""

  def __init__(self, data):
    self.data = data

    def getMentorFor(entity, *args):
      """Helper function to get value of mentor_for column."""
      return ', '.join(
          org.name for org in ndb.get_multi(entity.mentor_for) if org)

    def getAdminFor(entity, *args):
      """Helper function to get value of admin_for column."""
      return ', '.join(
          org.name for org in ndb.get_multi(entity.admin_for) if org)


    list_config = lists.ListConfiguration()

    list_config.addPlainTextColumn(
        'name', 'Name', lambda entity, *args: entity.public_name.strip())
    list_config.addSimpleColumn('profile_id', 'Username')
    list_config.addPlainTextColumn('is_admin', 'Is Admin',
        lambda entity, *args: 'Yes' if entity.is_admin else 'No', hidden=True)
    list_config.addPlainTextColumn(
        'email', 'Email', lambda entity, *args: entity.contact.email)
    list_config.addPlainTextColumn(
        'admin_for', 'Admin For', getAdminFor)
    list_config.addPlainTextColumn('mentor_for', 'Mentor For', getMentorFor)

    addresses.addAddressColumns(list_config)
    list_config.addPlainTextColumn(
        'tee_style', 'T-Shirt Style', lambda entity, *args: entity.tee_style)
    list_config.addPlainTextColumn(
        'tee_size', 'T-Shirt Size', lambda entity, *args: entity.tee_size)

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

    starter = lists.keyStarter
    # TODO(daniel): enable prefetching from ndb models
    # ('mentor_for', 'org_admin_for')
    prefetcher = None

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, query, starter,
        prefetcher=prefetcher)

    return response_builder.buildNDB()

  def templatePath(self):
    return 'modules/gsoc/participants/_mentors_list.html'


class MentorsListAdminPage(GSoCRequestHandler):
  """View for the organization admin and mentors page for admin."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gsoc/participants/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'admin/list/mentors/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_list_mentors'),
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


class StudentsList(Template):
  """List configuration for listing all the students involved with the program.
  """

  def __init__(self, request, data, linker, url_names):
    """Initializes this component."""
    self.data = data
    self.linker = linker
    self.url_names = url_names

    def taxFormSubmitted(entity, *args):
      """Helper function to get value of tax_form_submitted column."""
      if not soc_profile_logic.hasProject(entity):
        return 'N/A'
      elif entity.student_data.tax_form:
        return 'Yes'
      else:
        return 'No'

    def enrollmentFormSubmitted(entity, *args):
      """Helper function to get value of enrollment_form_submitted column."""
      if not soc_profile_logic.hasProject(entity):
        return 'N/A'
      elif entity.student_data.enrollment_form:
        return 'Yes'
      else:
        return 'No'

    def allFormsSubmitted(entity, *args):
      """Helper function to get value of all_forms_submitted column."""
      if not soc_profile_logic.hasProject(entity):
        return 'N/A'
      elif entity.student_data.enrollment_form and entity.student_data.tax_form:
        return 'Yes'
      else:
        return 'No'

    def projectsForOrgs(entity, *args):
      """Helper function to get value of projects_for_orgs column."""
      if not soc_profile_logic.hasProject(entity):
        return 'N/A'
      else:
        return ', '.join(
            org_key.get().name
            for org_key in entity.student_data.project_for_orgs)

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn(
        'name', 'Name', lambda entity, *args: entity.public_name.strip())
    list_config.addSimpleColumn('profile_id', 'Username')
    list_config.addPlainTextColumn(
        'email', 'Email', lambda entity, *args: entity.contact.email)
    list_config.addSimpleColumn('gender', 'Gender', hidden=True)
    list_config.addSimpleColumn(
        'birth_date', 'Birthdate', column_type=lists.BIRTHDATE, hidden=True)
    list_config.addPlainTextColumn(
        'tax_form_submitted', 'Tax form submitted',
        taxFormSubmitted, hidden=True)
    list_config.addPlainTextColumn(
        'enrollment_form_submitted', 'Enrollment form submitted',
        enrollmentFormSubmitted, hidden=True)
    list_config.addPlainTextColumn(
        'all_forms_submitted', 'All Forms submitted', allFormsSubmitted)

    addresses.addAddressColumns(list_config)
    list_config.addPlainTextColumn(
        'tee_style', 'T-Shirt Style', lambda entity, *args: entity.tee_style)
    list_config.addPlainTextColumn(
        'tee_size', 'T-Shirt Size', lambda entity, *args: entity.tee_size)

    list_config.addPlainTextColumn(
        'school_name', 'School Name',
        lambda entity, *args: entity.student_data.education.school_id,
        hidden=True)
    list_config.addPlainTextColumn(
        'school_country', 'School Country',
        lambda entity, *args: entity.student_data.education.school_country,
        hidden=True)
    list_config.addPlainTextColumn(
        'school_web_page', 'School Web Page',
        lambda entity, *args: entity.student_data.education.web_page,
        hidden=True)
    list_config.addPlainTextColumn(
        'major', 'Major',
        lambda entity, *args: entity.student_data.education.major,
        hidden=True)
    list_config.addPlainTextColumn(
        'degree', 'Degree',
        lambda entity, *args: entity.student_data.education.degree,
        hidden=True)
    list_config.addPlainTextColumn(
        'expected_graduation', 'Expected Graduation',
        lambda entity, *args: entity.student_data.education.expected_graduation,
        hidden=True)
    list_config.addPlainTextColumn(
        'number_of_proposals', 'Number Of Proposals',
        lambda entity, *args: entity.student_data.number_of_proposals,
        hidden=True)
    list_config.addNumericalColumn(
        'number_of_projects', 'Number Of Projects',
        lambda entity, *args: entity.student_data.number_of_projects,
        hidden=True)
    list_config.addNumericalColumn(
        'number_of_passed_evaluations', 'Passed Evaluations',
        lambda entity, *args: entity.student_data.number_of_passed_evaluations,
        hidden=True)
    list_config.addNumericalColumn(
        'number_of_failed_evaluations', 'Failed Evaluations',
        lambda entity, *args: entity.student_data.number_of_failed_evaluations,
        hidden=True)
    list_config.addPlainTextColumn(
        'project_for_orgs', 'Projects For Organizations', projectsForOrgs)

    list_config.setRowAction(
        lambda profile, *args: self.linker.profile(
            profile, self.url_names.PROFILE_ADMIN))

    self._list_config = list_config

  def templatePath(self):
    """See template.Template.templatePath for specification."""
    return 'modules/gsoc/dashboard/list_component.html'

  def getListData(self):
    idx = lists.getListIndex(self.data.request)

    if idx != 0:
      return None

    query = profile_logic.queryAllStudentsForProgram(self.data.program.key())

    starter = lists.keyStarter

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, query, starter)

    return response_builder.build()

  def context(self):
    """See template.Template.context for specification."""
    description = translation.ugettext('List of participating students')
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=0, description=description)

    return {
        'name': 'students',
        'title': 'Participating students',
        'lists': [list_configuration_response],
    }


class StudentsListPage(GSoCRequestHandler):
  """View that lists all the students associated with the program."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    return [
        url(r'admin/students/%s$' % url_patterns.PROGRAM, self,
            name='gsoc_students_list_admin'),
    ]

  def templatePath(self):
    """See base.RequestHandler.template_path for specification."""
    return 'modules/gsoc/admin/list.html'

  def jsonContext(self, data, check, mutator):
    """See base.RequestHandler.jsonContext for specification."""
    list_content = StudentsList(
        data.request, data, links.SOC_LINKER, urls.UrlNames).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    return {
      'page_name': 'Students list page',
      # TODO(nathaniel): Drop the first parameter of StudentsList.
      'list': StudentsList(data.request, data, links.SOC_LINKER, urls.UrlNames),
    }

