# Copyright 2014 the Melange authors.
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

"""Module contains models for shipment tracking information.
"""

from google.appengine.ext import ndb

from django.utils.translation import ugettext


class ShipmentInfo(ndb.Model):
  """Model for storing shipment info created by program admin.

  Stores Google spreadsheets id that is used for syncing.
  """

  #: string property field for storing shipment name
  name = ndb.StringProperty(required=True,
                           verbose_name=ugettext('Name Of Shipment'))

  #: Google spreadsheet id for student shipment tracking
  spreadsheet_id = ndb.StringProperty(
      required=True,
      verbose_name=ugettext('Spreadsheet id'))
  spreadsheet_id.help_text = ugettext(
      'Id of the Google spreadsheet that holds shipment data. '
      'Click input field to select a document.')

  #: status property for syncing
  status = ndb.StringProperty(
      required=True, default='idle',
      choices=['idle', 'syncing', 'half-complete', 'error'])

  #: datetime property for storing last sync time
  last_sync_time = ndb.DateTimeProperty(required=False)
