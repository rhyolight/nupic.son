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

"""Tasks related to syncing shipment tracking data.
"""

import StringIO
import csv
import datetime
import json
import logging
import re

from django import http
from django.conf.urls import url as django_url

from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.runtime import DeadlineExceededError

from melange.logic import profile as profile_logic
from melange.models import profile
from summerofcode.models.shipment import StudentShipment
from summerofcode.models.shipment_tracking import ShipmentInfo
from summerofcode.request import links

from soc.logic import dicts
from soc.tasks import responses
from soc.tasks.helper.timekeeper import Timekeeper
from soc.modules.gsoc.views.helper import url_names



DATE_SHIPPED_FORMAT = '%d/%m/%Y'


class ColumnNotFoundError(Exception):
  """Error to be raised when an expected column is not found in the row.
  """

  pass


class SyncTask(object):
  """Base class for sync tasks.
  """

  def findColumnIndexes(self, first_row, expected_columns):
    """Find column indexes in the first row for expected columns.

    Args:
      first_row: List for raw header row data of the sheet. Each element
                 of the list will be turned into variable like names.
                 e.g. 'Shipment Address 2 (35)' turns to 'shipment_address_2'
      expected_columns: List of expected columns in the first row. All
                        elements of the list are expected to be found in the
                        first row.
    """
    column_indexes = {}

    #sluggify first row elements (columns) into variable like names
    new_first_row = []
    for column_name in first_row:
      #lower characters: 'Shipment Address 2' > 'shipment address 2 (35)'
      column_name = column_name.lower()
      #remove paranthesis: 'address 2 (35)' > 'address 2'
      column_name = re.sub(r'[(].*[)]', '', column_name).strip()
      #remove unwanted characters
      column_name = re.sub(r'[^a-z1-9_ ]', '', column_name).strip()
      #replace whitespaces with '_': 'address 2' > 'address_2'
      column_name = re.sub(r'[ ]', '_', column_name)

      new_first_row.append(column_name)

    first_row = new_first_row

    for column_name in expected_columns:
      try:
        column_index = first_row.index(column_name)
      except ValueError:
        msg = '%s not found in %s' % (str(column_name), str(first_row))
        raise ColumnNotFoundError, msg
      column_indexes[column_name] = column_index

    return column_indexes


  def getRowData(self, row, column_indexes):
    data = {}
    for column_name, column_index in column_indexes.items():
      data[column_name] = row[column_index]

    return data


class ShipmentSyncTask(SyncTask):
  """Request handlers syncing shipments tracking data.
  """

  #Expected columns for USA and international student sheets
  USA_EXPECTED_COLUMNS = ['username', 'tracking']

  INTL_EXPECTED_COLUMNS = ['username', 'tracking']

  def __init__(self, *args, **kwargs):
    super(ShipmentSyncTask, self).__init__()

    self.program_key = None
    self.shipment_info = None

  def djangoURLPatterns(self):
    """Returns the URL patterns for the tasks in this module
    """
    patterns = [
        django_url(r'^tasks/gsoc/shipment_tracking/sync/start$',
                   self.startShipmentSync,
                   name=url_names.GSOC_SHIPMENT_TASK_START),
        django_url(r'^tasks/gsoc/shipment_tracking/sync/continue$',
                   self.continueShipmentSync,
                   name=url_names.GSOC_SHIPMENT_TASK_CONTINUE),
    ]
    return patterns

  def setProgram(self, program_key_str):
    self.program_key = db.Key(program_key_str)
    self.ndb_program_key = ndb.Key.from_old_key(self.program_key)

  def setShipmentInfo(self, shipment_info_id):
    self.shipment_info = ShipmentInfo.get_by_id(shipment_info_id,
                                                parent=self.ndb_program_key)

  def setShipmentInfoStatusToError(self):
    """Fallback function that sets shipment info status to 'error'.
    """
    if self.shipment_info:
      self.shipment_info.status = 'error'
      self.shipment_info.put()

  def startShipmentSync(self, request, *args, **kwargs):
    """Run _startShipmentSync while presuming an error for the fallback.
    """
    try:
      return self._startShipmentSync(request, *args, **kwargs)
    except Exception:
      self.setShipmentInfoStatusToError()
      raise

  def _startShipmentSync(self, request, *args, **kwargs):
    """Start syncing shipment data.

    POST Args:
      program_key: the key of the program which task is runnig for.
      sheet_content: sheet content data in JSON format.
      sheet_type: 'usa' or 'intl'
      shipment_info_id: id of the shipment info object that task is running
                        for.
    """
    params = dicts.merge(request.POST, request.GET)

    if 'program_key' not in params:
      logging.error("missing program_key in params: '%s'" % params)
      return responses.terminateTask()

    if 'sheet_content' not in params:
      logging.error("missing sheet_content in params: '%s'" % params)
      return responses.terminateTask()

    if 'sheet_type' not in params:
      logging.error("missing sheet_type in params: '%s'" % params)
      return responses.terminateTask()

    if 'shipment_info_id' not in params:
      logging.error("missing shipment_info_id in params: '%s'" % params)
      return responses.terminateTask()

    self.setProgram(params['program_key'])
    self.setShipmentInfo(int(params['shipment_info_id']))

    self.shipment_info.status = 'syncing'
    self.shipment_info.put()

    sheet_content = StringIO.StringIO(
        json.loads(params['sheet_content']))
    sheet_type = params['sheet_type']

    sheet_rows = [row for row in csv.reader(sheet_content)]

    if sheet_type == 'usa':
      column_indexes = self.findColumnIndexes(
          sheet_rows[0], self.USA_EXPECTED_COLUMNS)

    elif sheet_type == 'intl':
      column_indexes = self.findColumnIndexes(
          sheet_rows[0], self.INTL_EXPECTED_COLUMNS)

    params = {
        'program_key': params['program_key'],
        'shipment_info_id': params['shipment_info_id'],
        'column_indexes': json.dumps(column_indexes),
        'sheet_rows': json.dumps(sheet_rows[1:]),
    }

    task_continue_url = links.SOC_LINKER.site(url_names.GSOC_SHIPMENT_TASK_CONTINUE)
    taskqueue.add(url=task_continue_url, params=params)
    return responses.terminateTask()

  def continueShipmentSync(self, request, *args, **kwargs):
    """Run _continueShipmentSync while presuming an error for the fallback.
    """
    try:
      return self._continueShipmentSync(request, *args, **kwargs)
    except Exception:
      self.setShipmentInfoStatusToError()
      raise

  def _continueShipmentSync(self, request, *args, **kwargs):
    """Continue syncing shipment data.

    POST Args:
      program_key: the key of the program which sync is being done for.
      shipment_info_id: id of the shipment info object that task is running
                        for.
      column_indexes: column indexes for specific columns in JSON format.
      sheet_rows: spreadsheets CSV chunk data in JSON format.
    """
    timekeeper = Timekeeper(20000)
    params = dicts.merge(request.POST, request.GET)

    if 'program_key' not in params:
      logging.error("missing program_key in params: '%s'" % params)
      return responses.terminateTask()

    if 'shipment_info_id' not in params:
      logging.error("missing shipment_info_id in params: '%s'" % params)
      return responses.terminateTask()

    self.setProgram(params['program_key'])
    self.setShipmentInfo(int(params['shipment_info_id']))

    if 'sheet_rows' not in params:
      logging.error("missing sheet_rows data in params: '%s'" % params)
      return responses.terminateTask()

    if 'column_indexes' not in params:
      logging.error("missing column_indexes data in params: '%s'" % params)
      return responses.terminateTask()

    column_indexes = json.loads(params['column_indexes'])
    sheet_rows = json.loads(params['sheet_rows'])

    try:
      for remain, row in timekeeper.iterate(sheet_rows):

        if len(row) < len(column_indexes):
          row.extend((len(column_indexes) - len(row)) * [''])
        data = self.getRowData(row, column_indexes)
        username = data['username']

        profile = profile_logic.getProfileForUsername(username, self.program_key)

        if not profile:
          logging.error("Profile with username '%s' for program '%s' is not found" %
                        (username, self.ndb_program_key.id()))
          continue #continue to next row

        if not profile.is_student:
          logging.error("Profile with username '%s' is not a student" %
                        username)
          continue

        tracking = data['tracking']
        self.updateShipmentDataForStudent(profile, tracking)

    except DeadlineExceededError:
      if remain:
        remaining_rows = sheet_rows[(-1 * remain):]
        params = {
            'program_key': params.get('program_key'),
            'sheet_rows': json.dumps(remaining_rows),
            'column_indexes': params.get('column_indexes'),
            'shipment_info_id': params.get('shipment_info_id'),
        }
        task_continue_url = links.SOC_LINKER.site(url_names.GSOC_SHIPMENT_TASK_CONTINUE)
        taskqueue.add(url=task_continue_url, params=params)
        return responses.terminateTask()

    self.finishSync()
    return responses.terminateTask()

  def finishSync(self):
    self.shipment_info.last_sync_time = datetime.datetime.now()

    if self.shipment_info.status == 'syncing':
      self.shipment_info.status = 'half-complete'

    elif self.shipment_info.status == 'half-complete':
      self.shipment_info.status = 'idle'

    self.shipment_info.put()

  def updateShipmentDataForStudent(self, profile, tracking):

    q = StudentShipment.query(
        StudentShipment.shipment_info==self.shipment_info.key, ancestor=profile.key)
    student_shipment = q.get()

    if not student_shipment:
      student_shipment = StudentShipment(shipment_info=self.shipment_info.key,
                                         parent=profile.key)

    student_shipment.tracking = tracking
    student_shipment.put()
