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

"""Module containing the Students Info view for the admin.
"""


from google.appengine.ext import db

from django.utils.dateformat import format
from django.utils.translation import ugettext

from soc.logic.exceptions import AccessViolation
from soc.views.helper import lists
from soc.views.helper import url_patterns

from soc.modules.gci.models.profile import GCIStudentInfo
from soc.modules.gci.models.score import GCIScore
from soc.modules.gci.templates.student_list import StudentList
from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper.url_patterns import url
from soc.modules.gci.views.helper import url_names


class AllParticipatingStudentList(StudentList):
  """Component for listing all the students participating in GCI.
  """

  def __init__(self, request, data):
    super(AllParticipatingStudentList, self).__init__(request, data)
    # Each individual item in the list of students for the host now redirect
    # to the profile show page for that student that which is available only
    # to hosts. The super class redirected the list items to the list of
    # tasks completed by the student and that link is now moved to the profile
    # show page.
    self._list_config.setRowAction(
        lambda e, sp, *args: data.redirect.profile(
            sp[e.parent_key()].link_id).urlOf(url_names.GCI_PROFILE_SHOW_ADMIN))

  def context(self):
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx)

    return {
        'name': 'students',
        'title': 'Participating students',
        'lists': [list],
        'description': ugettext(
            'List of all participating students'),
    }


class StudentsInfoPage(RequestHandler):
  """View for the students info page for the admin.
  """

  def templatePath(self):
    return 'v2/modules/gci/students_info/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'admin/students_info/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_STUDENTS_INFO),
    ]

  def checkAccess(self):
    self.check.isHost()

  def jsonContext(self):
    list_content = AllParticipatingStudentList(
        self.request, self.data).getListData()

    if not list_content:
      raise AccessViolation(
          'You do not have access to this data')
    return list_content.content()

  def context(self):
    return {
        'page_name': "List of Students for %s" % self.data.program.name,
        'students_info_list': AllParticipatingStudentList(
            self.request, self.data),
    }
