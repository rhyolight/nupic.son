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

from django.utils.dateformat import format
from django.utils.translation import ugettext

from soc.views.helper import addresses
from soc.views.helper import lists
from soc.views.helper.url import urlize
from soc.views.template import Template

from soc.modules.gci.models.profile import GCIStudentInfo
from soc.modules.gci.models.score import GCIOrgScore
from soc.modules.gci.views.helper import url_names

DATE_FORMAT = 'd-m-Y'


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

    list_config = lists.ListConfiguration(add_key_column=False)
    list_config.addPlainTextColumn('key', 'Key', (lambda ent, *args: "%s" % (
        ent.parent().key().id_or_name())), hidden=True)

    list_config.setRowAction(
        lambda e, sp, *args: data.redirect.profile(
            sp[e.parent_key()].link_id).urlOf(url_names.GCI_STUDENT_TASKS))

    list_config.addPlainTextColumn(
        'name', 'Name', lambda e, sp, *args: sp[e.parent_key()].name())
    list_config.addPlainTextColumn(
        'link_id', 'Username', lambda e, sp, *args: sp[e.parent_key()].link_id)
    list_config.addPlainTextColumn(
        'email', 'Email', lambda e, sp, *args: sp[e.parent_key()].email)
    list_config.addPlainTextColumn('given_name', 'Given name',
        (lambda e, sp, *args: sp[e.parent_key()].given_name), hidden=True)
    list_config.addPlainTextColumn('surname', 'Surname',
        (lambda e, sp, *args: sp[e.parent_key()].surname), hidden=True)
    list_config.addPlainTextColumn('name_on_documents', 'Legal name',
        (lambda e, sp, *args: sp[e.parent_key()].name_on_documents),
        hidden=True)
    list_config.addPlainTextColumn(
        'birth_date', 'Birthdate',
        (lambda e, sp, *args: format(
            sp[e.parent_key()].birth_date, DATE_FORMAT)),
        hidden=True)
    list_config.addPlainTextColumn('gender', 'Gender',
        (lambda e, sp, *args: sp[e.parent_key()].gender))

    self._addAddressColumns(list_config)

    list_config.addPlainTextColumn('school_name', 'School name',
        (lambda e, sp, *args: sp[e.parent_key()].student_info.school_name),
        hidden=True)
    list_config.addPlainTextColumn('school_country', 'School Country',
        (lambda e, sp, *args: sp[e.parent_key()].student_info.school_country),
        hidden=True)
    list_config.addPlainTextColumn('school_type', 'School Type',
        (lambda e, sp, *args: sp[e.parent_key()].student_info.school_type),
        hidden=True)
    list_config.addPlainTextColumn('major', 'Major',
        (lambda e, sp, *args: sp[e.parent_key()].student_info.major),
        hidden=True)
    list_config.addPlainTextColumn('degree', 'Degree',
        (lambda e, sp, *args: sp[e.parent_key()].student_info.degree),
        hidden=True)
    list_config.addPlainTextColumn('grade', 'Grade',
        (lambda e, sp, *args: sp[e.parent_key()].student_info.grade),
        hidden=True)
    list_config.addPlainTextColumn('expected_graduation', 'Expected Graduation',
        (lambda e, sp, *args: sp[e.parent_key()].student_info.expected_graduation),
        hidden=True)

    list_config.addNumericalColumn('completed_tasks', 'Completed tasks',
        lambda e, *args: e.number_of_completed_tasks)

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
        (lambda e, sp, *args: formsSubmitted(e, sp, 'consent')))
    list_config.addPlainTextColumn(
        'student_id_form', 'Student ID Form Submitted',
        (lambda e, sp, *args: formsSubmitted(e, sp, 'student_id')))

    list_config.addPlainTextColumn('im_network', 'IM Network',
        (lambda e, sp, *args: sp[e.parent_key()].im_network),
        hidden=True)
    list_config.addPlainTextColumn('im_handle', 'IM Handle',
        (lambda e, sp, *args: sp[e.parent_key()].im_handle),
        hidden=True)
    list_config.addPlainTextColumn('home_page', 'Home Page',
        (lambda e, sp, *args: sp[e.parent_key()].home_page),
        hidden=True)
    list_config.addPlainTextColumn('blog', 'Blog',
        (lambda e, sp, *args: sp[e.parent_key()].blog),
        hidden=True)
    list_config.addPlainTextColumn('photo_url', 'Photo URL',
        (lambda e, sp, *args: urlize(sp[e.parent_key()].photo_url)),
        hidden=True)

    list_config.addPlainTextColumn('program_knowledge', 'Program Knowledge',
        (lambda e, sp, *args: sp[e.parent_key()].program_knowledge),
        hidden=True)

    list_config.addPlainTextColumn('created_on', 'Profile Created On',
        (lambda e, sp, *args: format(
            sp[e.parent_key()].created_on, DATE_FORMAT)),
        hidden=True)
    list_config.addPlainTextColumn('modified_on', 'Last Modified On',
        (lambda e, sp, *args: format(
            sp[e.parent_key()].modified_on, DATE_FORMAT)),
        hidden=True)

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
    return'v2/modules/gci/students_info/_students_list.html'

  def context(self):
    list = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.idx)

    return {
        'name': 'students',
        'title': 'Participating students',
        'lists': [list],
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
    list_config.addPlainTextColumn('res_street', 'Street',
        (lambda e, sp, *args: sp[e.parent_key()].res_street), hidden=True)
    list_config.addPlainTextColumn('res_street_extra', 'Street Extra', 
        (lambda e, sp, *args: sp[e.parent_key()].res_street_extra), hidden=True)
    list_config.addPlainTextColumn('res_city', 'City',
        (lambda e, sp, *args: sp[e.parent_key()].res_city), hidden=True)
    list_config.addPlainTextColumn('res_state', 'State',
        (lambda e, sp, *args: sp[e.parent_key()].res_state), hidden=True)
    list_config.addPlainTextColumn('res_country', 'Country',
        (lambda e, sp, *args: sp[e.parent_key()].res_country), hidden=True)
    list_config.addPlainTextColumn('res_postalcode', 'Postalcode',
        (lambda e, sp, *args: sp[e.parent_key()].res_postalcode), hidden=True)
    list_config.addPlainTextColumn('phone', 'Phone',
        (lambda e, sp, *args: sp[e.parent_key()].phone), hidden=True)
    list_config.addPlainTextColumn('ship_name', 'Ship Name',
        (lambda e, sp, *args: sp[e.parent_key()].shipping_name()), hidden=True)
    list_config.addPlainTextColumn('ship_street', 'Ship Street',
        (lambda e, sp, *args: sp[e.parent_key()].shipping_street()), hidden=True)
    list_config.addPlainTextColumn('ship_street_extra', 'Ship Street Extra',
        (lambda e, sp, *args: sp[e.parent_key()].shipping_street_extra()), 
        hidden=True)
    list_config.addPlainTextColumn('ship_city', 'Ship City',
        (lambda e, sp, *args: sp[e.parent_key()].shipping_city()), hidden=True)
    list_config.addPlainTextColumn('ship_state', 'Ship State', 
        (lambda e, sp, *args: sp[e.parent_key()].shipping_state()), hidden=True)
    list_config.addPlainTextColumn('ship_country', 'Ship Country',
        (lambda e, sp, *args: sp[e.parent_key()].shipping_country()), hidden=True)
    list_config.addPlainTextColumn('ship_postalcode', 'Ship Postalcode',
        (lambda e, sp, *args: sp[e.parent_key()].shipping_postalcode()), 
        hidden=True)
    list_config.addPlainTextColumn('tshirt_style', 'T-Shirt Style',
        (lambda e, sp, *args: sp[e.parent_key()].tshirt_style), hidden=True)
    list_config.addPlainTextColumn('tshirt_size', 'T-Shirt Size',
        (lambda e, sp, *args: sp[e.parent_key()].tshirt_size), hidden=True)
