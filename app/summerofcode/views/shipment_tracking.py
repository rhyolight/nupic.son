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

"""Module for the shipment tracking views."""

import json
import logging

import httplib2

from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from google.appengine.ext import webapp

from apiclient.discovery import build
from django import forms as django_forms
from django import http
from django.conf.urls import url as django_url
from django.utils.dateformat import format
from oauth2client.appengine import OAuth2Decorator

from melange.request import access
from melange.request import exception

from soc.logic import site as site_logic
from soc.models import site
from soc.views import template
from soc.views.helper import context as context_helper
from soc.views.helper import lists
from soc.views.helper import url_patterns as soc_url_patterns

from soc.modules.gsoc.views import forms
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper import url_patterns
from soc.modules.gsoc.views.helper.url_patterns import url
from soc.modules.gsoc.views import base

from summerofcode.request import links
from summerofcode.models import shipment_tracking

# TODO(daniel): once Site has been migrated to ndb, update this to make sure
# it benefits from ndbs caching mechanisms.
site = site_logic.singleton()
decorator = OAuth2Decorator(
    client_id=site.google_client_id,
    client_secret=site.google_client_secret,
    scope='https://www.googleapis.com/auth/drive.file')

URL_FMT = ("https://docs.google.com/feeds/download/spreadsheets/Export" +
           "?key=%s&exportFormat=csv&gid=%d")


def redirect(self, uri):
  raise exception.Redirect(uri)


class CallbackPage(base.GSoCRequestHandler):
  """View with the document picker.
  """
  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.RequestHandler.getDjangoURLPatterns for specification."""
    callback_path = decorator.callback_path.lstrip('/')
    return [
        django_url(callback_path, self, name=url_names.GSOC_PICKER_CALLBACK),
    ]

  def get(self, data, check, mutator):
    response = webapp.Response()
    request = webapp.Request(data.request.environ)
    cls = decorator.callback_handler()
    cls.redirect = redirect
    handler = cls()
    handler.initialize(request, response)
    handler.get()
    response = http.HttpResponse(content=response.body)
    return response


NAME_LABEL_ = "Name"
NAME_HELP_TEXT = "Name Of Shipment"
SPREADSHEET_ID_LABEL = "Spreadsheet id"
SPREADSHEET_HELP_TEXT = (
      'Id of the Google spreadsheet that holds shipment data. '
      'Click input field to select a document.')


class ShipmentInfoForm(forms.GSoCModelForm):
  """Form for editing ShipmentInfo objects."""

  Meta = object()
  name = django_forms.CharField(
      required=True, label=NAME_LABEL_, help_text=NAME_HELP_TEXT)
  spreadsheet_id = django_forms.CharField(
      required=True, label=SPREADSHEET_ID_LABEL, help_text=SPREADSHEET_HELP_TEXT)


class CreateShipmentInfo(base.GSoCRequestHandler):
  """View with the document picker.
  """
  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.RequestHandler.getDjangoURLPatterns for specification."""
    return [
        url(r'admin/shipment_info/create/%s$' %
            soc_url_patterns.PROGRAM,
            self, name=url_names.GSOC_CREATE_SHIPMENT_INFO),
        url(r'admin/shipment_info/edit/%s' %
            url_patterns.SHIPMENT_INFO,
            self, name=url_names.GSOC_EDIT_SHIPMENT_INFO),
    ]

  def _getShipmentInfo(self, data):
    id_string = data.kwargs.get('id', '')
    shipment_id = int(id_string) if id_string.isalnum() else -1
    if shipment_id < 1:
      return None
    return shipment_tracking.ShipmentInfo.get_by_id(
        shipment_id, parent=ndb.Key.from_old_key(data.program.key()))

  def renderForm(self, data):
    response = webapp.Response()
    request = webapp.Request(data.request.environ)
    shipment_info = self._getShipmentInfo(data)
    impl = CreateShipmentInfoHandler(self.renderer, data, shipment_info)
    impl.initialize(request, response)
    impl.get()
    return response.body

  def get(self, data, check, mutator):
    rendered_form = self.renderForm(data)
    response = http.HttpResponse(content=rendered_form)
    return response

  def post(self, data, check, mutator):
    form = ShipmentInfoForm(data=data.POST)
    error = bool(form.errors)
    if error:
      rendered_form = self.renderForm(data)
      return http.HttpResponse(content=rendered_form)
    else:
      # TODO(daniel): find a better solution for creating entities from forms
      # that use ndb
      name = form.cleaned_data['name']
      spreadsheet_id = form.cleaned_data['spreadsheet_id']
      entity = shipment_tracking.ShipmentInfo(
          name=name, spreadsheet_id=spreadsheet_id,
          parent=ndb.Key.from_old_key(data.program.key()))
      entity.put()
      shipment_id = entity.key.id()
      edit_url = links.SOC_LINKER.shipmentInfo(
          data.program, shipment_id, url_names.GSOC_EDIT_SHIPMENT_INFO)
      raise exception.Redirect(edit_url)


class CreateShipmentInfoHandler(webapp.RequestHandler):
  """Implementation of the view with the document picker."""

  def __init__(self, renderer, data, shipment_info):
    self.renderer = renderer
    self.data = data
    self.shipment_info = shipment_info

  # TODO(nathaniel): Remove the lint suppression when
  # https://code.google.com/p/googleappengine/issues/detail?id=10518 is
  # resolved.
  def redirect(self, uri, permanent=False):  # pylint: disable=arguments-differ
    raise exception.Redirect(uri)

  @decorator.oauth_required
  def get(self):
    template_path = 'summerofcode/shipment_tracking/picker.html'
    result_url = links.SOC_LINKER.program(
        self.data.program, url_names.GSOC_CREATE_SHIPMENT_INFO)
    context = context_helper.default(self.data)
    form_dict = self.shipment_info.to_dict() if self.shipment_info else None
    form_data = self.data.POST or form_dict
    form = ShipmentInfoForm(data=form_data)
    error = bool(form.errors)
    context.update({
        'access_token': decorator.credentials.access_token,
        'client_id': decorator.credentials.client_id,
        'developer_key': "AIzaSyCf5d-klzRMYCninhqaWx5zFp8GiHI6TWM",
        'error': error,
        'forms': [form],
        'page_name': 'Select a tracking spreadsheet',
        'result_url': result_url,
    })
    response_content = self.renderer.render(self.data, template_path, context)
    self.response.write(response_content)


class ShipmentInfoList(template.Template):
  """Template for the list of ShipmentInfo objects.
  """

  def __init__(self, request, data):
    self.request = request
    self.data = data

    list_config = lists.ListConfiguration()
    list_config.addSimpleColumn('name', 'Name')
    list_config.addSimpleColumn('status', 'Status')
    list_config.addPlainTextColumn(
        'last_sync_time', 'Last Sync Time',
        lambda ent, *args: format(
          ent.last_sync_time, lists.DATETIME_FORMAT) if \
          ent.last_sync_time else 'N/A')

    self._list_config = list_config

    def rowAction(entity, *args):
      entity_id = entity.key.id()

      return links.SOC_LINKER.shipmentInfo(
          data.program, entity_id, url_names.GSOC_EDIT_SHIPMENT_INFO)

    self._list_config.setRowAction(rowAction)

  def templatePath(self):
    return 'summerofcode/shipment_tracking/_list.html'

  def context(self):
    description = 'List of shipment informations for %s' % \
                  self.data.program.name

    list_response = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)
    return {
        'list_name': 'Shipment Informations',
        'lists': [list_response],
    }

  def getListData(self):
    idx = lists.getListIndex(self.request)
    if idx != 0:
      return None

    q = shipment_tracking.ShipmentInfo.query(
        ancestor=ndb.Key.from_old_key(self.data.program.key()))
    starter = lists.keyStarter
    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, q, starter)

    return response_builder.build()


class ShipmentInfoListPage(base.GSoCRequestHandler):
  """Admin view for listing all shipment infos for a specific program.
  """
  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url(r'admin/shipment_tracking/records/%s' %
            soc_url_patterns.PROGRAM,
            self, name='gsoc_shipment_info_records'),
    ]

  def templatePath(self):
    return 'summerofcode/shipment_tracking/records.html'

  def context(self, data, check, mutator):
    context = {
        'page_name': 'Shipment informations for %s' % data.program.name,
        'list': ShipmentInfoList(data.request, data),
    }
    return context

  def jsonContext(self, data, check, mutator):
    list_content = ShipmentInfoList(data.request, data).getListData()
    if not list_content:
      raise exception.Forbidden(
          'You do not have access to this data')
    return list_content.content()


class SyncData(base.GSoCRequestHandler):
  """Admin view that shows syncing tasks.
  """
  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  DEF_BATCH_SIZE = 100

  def djangoURLPatterns(self):
    return [
        url(r'admin/shipment_tracking/sync/%s$' % soc_url_patterns.PROGRAM,
            self, name=url_names.GSOC_SHIPMENT_LIST),
    ]

  def templatePath(self):
    return 'summerofcode/shipment_tracking/sync_data.html'

  def context(self, data, check, mutator):
    def getUrl(shipment_info):
      return links.SOC_LINKER.shipmentInfo(
          data.program, shipment_info.key.id(), url_names.GSOC_SHIPMENT_SYNC)
    query = shipment_tracking.ShipmentInfo.query(
        ancestor=ndb.Key.from_old_key(data.program.key()))
    list_data = [(getUrl(i), i) for i in query.fetch(self.DEF_BATCH_SIZE)]
    return {
        'page_name': 'Sync Trackings Data for %s' % data.program.name,
        'shipment_infos': list_data,
    }


class ShipmentTrackingPage(base.GSoCRequestHandler):
  """View with the document picker.
  """
  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

  def djangoURLPatterns(self):
    """See base.RequestHandler.getDjangoURLPatterns for specification."""
    return [
        url(r'admin/shipment_tracking/sync/%s$' %
            url_patterns.SHIPMENT_INFO,
            self, name=url_names.GSOC_SHIPMENT_SYNC),
    ]

  def get(self, data, check, mutator):
    response = webapp.Response()
    request = webapp.Request(data.request.environ)
    impl = ShipmentTrackingPageImpl(self.renderer, data)
    impl.initialize(request, response)
    impl.handle()
    response = http.HttpResponse(content=response.body)
    return response

  def post(self, data, check, mutator):
    return self.get(data, check, mutator)


class ShipmentTrackingPageImpl(webapp.RequestHandler):
  """Implementation of the view with the document picker.
  """
  def __init__(self, renderer, data):
    self.renderer = renderer
    self.data = data

  # TODO(nathaniel): Remove the disabled lint inspection when
  # https://code.google.com/p/googleappengine/issues/detail?id=10518 is
  # resolved.
  def redirect(self, uri, permanent=False):  # pylint:disable=arguments-differ
    raise exception.Redirect(uri)

  @decorator.oauth_required
  def handle(self):
    http = httplib2.Http()
    credentials = decorator.get_credentials()
    http = credentials.authorize(http)
    drive_service = build('drive', 'v2', http=http)
    shipment_info_id = int(self.data.kwargs['id'])
    program_key = ndb.Key.from_old_key(self.data.program.key())
    shipment_info = shipment_tracking.ShipmentInfo.get_by_id(
        shipment_info_id, parent=program_key)
    usa_url = URL_FMT % (shipment_info.spreadsheet_id, 0)
    intl_url = URL_FMT % (shipment_info.spreadsheet_id, 1)

    #get sheet content for USA students
    resp, usa_sheet_content = drive_service._http.request(usa_url)
    if resp.status != 200:
      logging.error('An error occurred: %s', resp)

    resp, intl_sheet_content = drive_service._http.request(intl_url)
    if resp.status != 200:
      logging.error('An error occurred: %s', resp)

    task_start_url = links.SOC_LINKER.site(url_names.GSOC_SHIPMENT_TASK_START)

    #start task for USA students
    params = {
        'program_key': str(self.data.program.key()),
        'sheet_content': json.dumps(usa_sheet_content),
        'sheet_type': 'usa',
        'shipment_info_id': shipment_info_id,
    }
    taskqueue.add(url=task_start_url, params=params)

    #start task for international students
    params = {
        'program_key': str(self.data.program.key()),
        'sheet_content': json.dumps(intl_sheet_content),
        'sheet_type': 'intl',
        'shipment_info_id': shipment_info_id,
    }
    taskqueue.add(url=task_start_url, params=params)

    #return back to sync data page
    result_url = links.SOC_LINKER.program(
        self.data.program, url_names.GSOC_SHIPMENT_LIST)
    raise exception.Redirect(result_url)
