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

"""Module containing template with a list of GCIOrganization entities.
"""


from google.appengine.ext import db

from django.utils.translation import ugettext

from soc.views.helper import addresses
from soc.views.helper import lists
from soc.views.helper.url import urlize
from soc.views.template import Template

from soc.modules.gci.models.profile import GCIStudentInfo
from soc.modules.gci.models.score import GCIOrgScore
from soc.modules.gci.views.helper import url_names


class StudentList(Template):
  """Component for listing all the students in GCI.
  """

  class ListPrefetcher(lists.Prefetcher):
    """Prefetcher for StudentList.

    See lists.Prefetcher for specification.
    """

    def prefetch(self, entities):
      """Prefetches GCIProfiles corresponding to the specified list of
      GCIStudentInfo entities.

      See lists.Prefetcher.prefetch for specification.

      Args:
        entities: the specified list of GCIStudentInfo instances

      Returns:
        prefetched GCIProfile entities in a structure whose format is
        described in lists.Prefetcher.prefetch
      """
      keys = []

      for entity in entities:
        key = entity.parent_key()
        if key:
          keys.append(key)

      profiles = db.get(keys)

      return (
          [dict((profile.key(), profile) for profile in profiles if profile)],
          {})

  def __init__(self, data):
    self.data = data
    self.idx = 1

    list_config = lists.ListConfiguration()

    list_config.setRowAction(
        lambda entity, sp, *args: data.redirect.profile(
            sp[entity.parent_key()].link_id).urlOf(url_names.GCI_STUDENT_TASKS))

    list_config.addSimpleParentColumn('name', 'Name')
    list_config.addParentColumn(
        'name', 'Name', (lambda entity, *args: entity.name()))
    list_config.addSimpleParentColumn('link_id', 'Username')
    list_config.addSimpleParentColumn('email', 'Email')
    list_config.addSimpleParentColumn('given_name', 'Given name', hidden=True)
    list_config.addSimpleParentColumn('surname', 'Surname', hidden=True)
    list_config.addSimpleParentColumn('name_on_documents', 'Legal name',
                                      hidden=True)
    list_config.addSimpleParentColumn(
        'birth_date', 'Birthdate', column_type=lists.BIRTHDATE, hidden=True)
    list_config.addSimpleParentColumn('gender', 'Gender')

    self._addAddressColumns(list_config)

    list_config.addParentColumn(
        'school_name', 'School name',
        (lambda entity, *args: entity.student_info.school_name),
        hidden=True)
    list_config.addParentColumn(
        'school_country', 'School Country',
        (lambda entity, *args: entity.student_info.school_country), hidden=True)
    list_config.addParentColumn(
        'school_type', 'School Type',
        (lambda entity, *args: entity.student_info.school_type), hidden=True)
    list_config.addParentColumn(
        'major', 'Major',
        (lambda entity, *args: entity.student_info.major), hidden=True)
    list_config.addParentColumn(
        'degree', 'Degree',
        (lambda entity, *args: entity.student_info.degree), hidden=True)
    list_config.addParentColumn(
        'grade', 'Grade',
        (lambda entity, *args: entity.student_info.grade), hidden=True)
    list_config.addParentColumn(
        'expected_graduation', 'Expected Graduation',
        (lambda entity, *args: entity.student_info.expected_graduation),
        hidden=True)
    list_config.addSimpleColumn(
        'number_of_completed_tasks', 'Completed tasks',
        column_type=lists.NUMERICAL)

    def formsSubmitted(e, sp, form):
      """Returns "Yes" if form has been submitted otherwise "No".

      form takes either 'consent' or 'student_id' as values which stand
      for parental consent form and student id form respectively.
      """
      info = sp[e.parent_key()].student_info
      if form == 'consent':
        consent = GCIStudentInfo.consent_form.get_value_for_datastore(info)
        if consent:
          return 'Yes'
      if form == 'student_id':
        student_id = GCIStudentInfo.student_id_form.get_value_for_datastore(info)
        if student_id:
          return 'Yes'
      return 'No'

    list_config.addPlainTextColumn(
        'consent_form', 'Consent Form Submitted',
        (lambda entity, sp, *args: formsSubmitted(entity, sp, 'consent')))
    list_config.addPlainTextColumn(
        'student_id_form', 'Student ID Form Submitted',
        (lambda entity, sp, *args: formsSubmitted(entity, sp, 'student_id')))

    list_config.addSimpleParentColumn('im_network', 'IM Network', hidden=True)
    list_config.addSimpleParentColumn('im_handle', 'IM Handle', hidden=True)
    list_config.addSimpleParentColumn('home_page', 'Home Page', hidden=True)
    list_config.addSimpleParentColumn('blog', 'Blog', hidden=True)
    list_config.addParentColumn(
        'photo_url', 'Photo URL',
        (lambda entity, *args: urlize(entity.photo_url)), hidden=True)
    list_config.addSimpleParentColumn('program_knowledge', 'Program Knowledge',
                                      hidden=True)
    list_config.addSimpleParentColumn(
        'created_on', 'Profile Created On',
        column_type=lists.DATE, hidden=True)
    list_config.addSimpleParentColumn(
        'modified_on', 'Last Modified On',
        column_type=lists.DATE, hidden=True)

    self._list_config = list_config

  def getListData(self):
    idx = lists.getListIndex(self.data.request)

    if idx != self.idx:
      return None

    query = GCIStudentInfo.all()
    query.filter('program', self.data.program)

    starter = lists.keyStarter
    prefetcher = StudentList.ListPrefetcher()

    response_builder = lists.RawQueryContentResponseBuilder(
        self.data.request, self._list_config, query, starter,
        prefetcher=prefetcher)

    return response_builder.build()

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

  def _addAddressColumns(self, list_config):
    """Adds address columns to the specified list config.

    Columns added:
      * res_street
      * res_street_extra
      * res_city
      * res_state
      * res_country
      * res_postalcode
      * phone
      * ship_name
      * ship_street
      * ship_street_extra
      * ship_city
      * ship_state
      * ship_country
      * ship_postalcode
      * tshirt_style
      * tshirt_size
    """
    list_config.addSimpleParentColumn('res_street', 'Street', hidden=True)
    list_config.addSimpleParentColumn('res_street_extra', 'Street Extra',
                                      hidden=True)
    list_config.addSimpleParentColumn('res_city', 'City', hidden=True)
    list_config.addSimpleParentColumn('res_state', 'State', hidden=True)
    list_config.addSimpleParentColumn('res_country', 'Country', hidden=True)
    list_config.addSimpleParentColumn('res_postalcode', 'Postalcode', hidden=True)
    list_config.addSimpleParentColumn('phone', 'Phone', hidden=True)
    list_config.addParentColumn(
        'ship_name', 'Ship Name',
        (lambda entity, *args: entity.shipping_name()), hidden=True)
    list_config.addParentColumn(
        'ship_street', 'Ship Street',
        (lambda entity, *args: entity.shipping_street()), hidden=True)
    list_config.addParentColumn(
        'ship_street_extra', 'Ship Street Extra',
        (lambda entity, *args: entity.shipping_street_extra()), hidden=True)
    list_config.addParentColumn(
        'ship_city', 'Ship City',
        (lambda entity, *args: entity.shipping_city()), hidden=True)
    list_config.addParentColumn(
        'ship_state', 'Ship State',
        (lambda entity, *args: entity.shipping_state()), hidden=True)
    list_config.addParentColumn(
        'ship_country', 'Ship Country',
        (lambda entity, *args: entity.shipping_country()), hidden=True)
    list_config.addParentColumn(
        'ship_postalcode', 'Ship Postalcode',
        (lambda entity, *args: entity.shipping_postalcode()), hidden=True)
    list_config.addSimpleParentColumn('tshirt_style', 'T-Shirt Style',
                                      hidden=True)
    list_config.addSimpleParentColumn('tshirt_size', 'T-Shirt Size',
                                      hidden=True)
