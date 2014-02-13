# Copyright 2012 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing template with a list of GCIOrganization entities."""

from django.utils.translation import ugettext

from melange.logic import profile as profile_logic

from soc.views.helper import addresses
from soc.views.helper import lists
from soc.views.helper.url import urlize
from soc.views.template import Template

from soc.modules.gci.models.profile import GCIStudentInfo
from soc.modules.gci.views.helper import url_names


class StudentList(Template):
  """Component for listing all the students in GCI."""


  def __init__(self, data):
    self.data = data
    self.idx = 1

    list_config = lists.ListConfiguration()

    list_config.setRowAction(
        lambda entity, *args: data.redirect.profile(
            entity.profile_id).urlOf(url_names.GCI_STUDENT_TASKS))

    list_config.addSimpleColumn('public_name', 'Public Name')

    list_config.addSimpleColumn('profile_id', 'Username')
    list_config.addPlainTextColumn(
        'email', 'Email', lambda entity, *args: entity.contact.email)
    list_config.addSimpleColumn('first_name', 'First Name', hidden=True)
    list_config.addSimpleColumn('last_name', 'Last Name')
    list_config.addBirthDateColumn(
        'birth_date', 'Birth date', lambda entity, *args: entity.birth_date,
        hidden=True)
    list_config.addSimpleColumn('gender', 'Gender')

    addresses.addAddressColumns(list_config)

    list_config.addPlainTextColumn(
        'school_id', 'School name',
        lambda entity, *args: entity.student_data.education.school_id,
        hidden=True)
    list_config.addPlainTextColumn(
        'school_country', 'School Country',
        lambda entity, *args: entity.student_data.education.school_country,
        hidden=True)
    list_config.addPlainTextColumn(
        'grade', 'Grade',
        lambda entity, *args: entity.student_data.education.grade, hidden=True)
    list_config.addPlainTextColumn(
        'expected_graduation', 'Expected Graduation',
        lambda entity, *args: entity.student_data.education.expected_graduation,
        hidden=True)
    list_config.addPlainTextColumn(
        'number_of_completed_tasks', 'Completed tasks',
        lambda entity, *args: entity.student_data.number_of_completed_tasks)

    def formsSubmitted(entity, form_type):
      """Returns "Yes" if form has been submitted otherwise "No".

      form takes either 'consent' or 'student_id' as values which stand
      for parental consent form and student id form respectively.
      """
      if form_type == 'consent':
        return 'Yes' if entity.student_data.consent_form else 'No'
      elif form_type == 'enrollment':
        return 'Yes' if entity.student_data.enrollment_form else 'No'
      else:
        raise ValueError('Unsupported form type: %s' % form_type)

    list_config.addPlainTextColumn(
        'consent_form', 'Consent Form Submitted',
        lambda entity, *args: formsSubmitted(entity, 'consent'))
    list_config.addPlainTextColumn(
        'enrollment_form', 'Student ID Form Submitted',
        lambda entity, *args: formsSubmitted(entity, 'enrollment'))

    list_config.addPlainTextColumn(
        'home_page', 'Home Page',
        lambda entity, *args: entity.contact.web_page, hidden=True)
    list_config.addPlainTextColumn(
        'blog', 'Blog',
        lambda entity, *args: entity.contact.blog, hidden=True)
    list_config.addSimpleColumn('tee_style', 'T-Shirt Style')
    list_config.addSimpleColumn('tee_size', 'T-Shirt Size')

    list_config.addHtmlColumn(
        'photo_url', 'Photo URL',
        (lambda entity, *args: urlize(entity.photo_url)), hidden=True)
    list_config.addSimpleColumn(
        'program_knowledge', 'Program Knowledge', hidden=True)

    self._list_config = list_config

  def getListData(self):
    idx = lists.getListIndex(self.data.request)

    if idx != self.idx:
      return None

    query = profile_logic.queryAllStudentsForProgram(self.data.program.key())

    starter = lists.keyStarter

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, query, starter)

    return response_builder.buildNDB()

  def templatePath(self):
    return'modules/gci/students_info/_students_list.html'

  def context(self):
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx)

    return {
        'name': 'students',
        'title': 'Participating students',
        'lists': [list_configuration_response],
        'description': ugettext(
            'List of participating students'),
    }
