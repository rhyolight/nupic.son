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

"""Module containing the Students Info view for the admin."""

from django.utils.translation import ugettext

from melange.request import access
from melange.request import exception
from soc.views.helper import lists
from soc.views.helper import url_patterns

from soc.modules.gci.templates import student_list
from soc.modules.gci.views import base
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper import url_patterns as gci_url_patterns


class AllParticipatingStudentsList(student_list.StudentList):
  """Component for listing all the students participating in GCI."""

  def __init__(self, data):
    super(AllParticipatingStudentsList, self).__init__(data)

    def formVerified(verified_prop):
      """Returns Yes/No based on whether the form verified property's value."""
      return "Yes" if verified_prop else "No"

    # Columns that display whether the student forms are already verified.
    self._list_config.addPlainTextColumn(
        'is_consent_form_verified', 'Consent Verified',
        lambda entity, *args:
            formVerified(entity.student_data.is_consent_form_verified))
    self._list_config.addPlainTextColumn(
        'is_enrollment_form_verified', 'Enrollment Verified',
        lambda entity, *args:
            formVerified(entity.student_data.is_enrollment_form_verified))

    # Each individual item in the list of students for the host now redirect
    # to the profile show page for that student that which is available only
    # to hosts. The super class redirected the list items to the list of
    # tasks completed by the student and that link is now moved to the profile
    # show page.
    self._list_config.setRowAction(
        lambda entity, *args: data.redirect.profile(
            entity.profile_id).urlOf(url_names.GCI_PROFILE_SHOW_ADMIN))

  def context(self):
    all_participating_students_list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx)

    return {
        'name': 'students',
        'title': 'Participating students',
        'lists': [all_participating_students_list],
        'description': ugettext('List of all participating students'),
    }


class StudentsInfoPage(base.GCIRequestHandler):
  """View for the students info page for the admin."""

  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def templatePath(self):
    return 'modules/gci/students_info/base.html'

  def djangoURLPatterns(self):
    return [
        gci_url_patterns.url(r'admin/students_info/%s$' % url_patterns.PROGRAM,
                             self, name=url_names.GCI_STUDENTS_INFO),
    ]

  def jsonContext(self, data, check, mutator):
    all_participating_students_list = AllParticipatingStudentsList(data)
    list_content = all_participating_students_list.getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    return {
        'page_name': 'List of Students for %s' % data.program.name,
        'students_info_list': AllParticipatingStudentsList(data),
    }
