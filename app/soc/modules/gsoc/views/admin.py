#!/usr/bin/env python2.5
#
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

"""Module for the admin pages.
"""

__authors__ = [
  '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


import logging

from google.appengine.api import users
from google.appengine.ext import db

from django import forms as djangoforms
from django.conf.urls.defaults import url
from django.utils import simplejson
from django.utils.translation import ugettext

from soc.logic import accounts
from soc.logic import cleaning
from soc.logic import dicts
from soc.logic.exceptions import BadRequest
from soc.views import forms
from soc.views import readonly_template
from soc.views.template import Template

from soc.models.user import User

from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import lists
from soc.modules.gsoc.views.helper import url_patterns


class LookupForm(forms.ModelForm):
  """Django form for the invite page.
  """

  class Meta:
    model = None

  def __init__(self, request_data, *args):
    super(LookupForm, self).__init__(*args)
    self.request_data = request_data

  email = djangoforms.CharField(label='Email')

  def clean_email(self):
    email_cleaner = cleaning.clean_email('email')

    try:
      email_address = email_cleaner(self)
    except djangoforms.ValidationError, e:
      if e.code != 'invalid':
        raise
      msg = ugettext(u'Enter a valid email address.')
      raise djangoforms.ValidationError(msg, code='invalid')

    account = users.User(email_address)
    user_account = accounts.normalizeAccount(account)
    user = User.all().filter('account', user_account).get()

    if not user:
      raise djangoforms.ValidationError(
          "There is no user with that email address")

    self.cleaned_data['user'] = user

    q = GSoCProfile.all()
    q.filter('scope', self.request_data.program)
    q.ancestor(user)
    self.cleaned_data['profile'] = q.get()


class DashboardPage(RequestHandler):
  """Dashboard for admins.
  """

  def djangoURLPatterns(self):
    return [
        url(r'^gsoc/admin/%s$' % url_patterns.PROGRAM,
         self, name='gsoc_admin_dashboard'),
    ]

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gsoc/admin/dashboard.html'

  def context(self):
    r = self.data.redirect
    r.program()

    return {
        'page_name': 'Admin dashboard',
        'lookup_link': r.urlOf('lookup_gsoc_profile'),
        'slots_link': r.urlOf('gsoc_slots'),
    }


class LookupLinkIdPage(RequestHandler):
  """View for the participant profile.
  """

  def djangoURLPatterns(self):
    return [
        url(r'^gsoc/admin/lookup/%s$' % url_patterns.PROGRAM,
         self, name='lookup_gsoc_profile'),
    ]

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gsoc/admin/lookup.html'

  def post(self):
    self.get()

  def context(self):
    form = LookupForm(self.data, self.data.POST or None)
    error = bool(form.errors)

    forms = [form]
    profile = None

    if not form.errors and self.data.request.method == 'POST':
      profile = form.cleaned_data.get('profile')

    if profile:
      self.redirect.profile(profile.link_id)
      self.redirect.to('gsoc_profile_admin')

    return {
      'forms': forms,
      'error': error,
      'posted': error,
      'page_name': 'Lookup profile',
    }


class SlotsList(Template):
  """Template for list of accepted organizations.
  """

  def __init__(self, request, data):
    self.request = request
    self.data = data

    list_config = lists.ListConfiguration()
    list_config.addColumn('name', 'Name',
        (lambda e, *args: e.short_name.strip()), width=75)
    list_config.addSimpleColumn('link_id', 'Link ID', hidden=True)
    list_config.addSimpleColumn('slots_desired', 'min', width=25)
    list_config.addSimpleColumn('max_slots_desired', 'max', width=25)
    list_config.addSimpleColumn('slots', 'Slots', width=50)
    list_config.setColumnEditable('slots', True)
    list_config.addSimpleColumn('note', 'Note')
    list_config.setColumnEditable('note', True) #, edittype='textarea')
    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('name')
    bounds = ['0', 'all']
    fields = ['key', 'slots', 'note']
    list_config.addPostButton('save', "Save", "#", bounds, fields)

    self._list_config = list_config

  def context(self):
    description = 'List of organizations accepted into %s' % (
            self.data.program.name)

    list = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)

    return {
        'lists': [list],
    }

  def getListData(self):
    idx = lists.getListIndex(self.request)
    if idx != 0:
      return None

    q = GSoCOrganization.all().filter('scope', self.data.program)

    starter = lists.keyStarter

    response_builder = lists.RawQueryContentResponseBuilder(
        self.request, self._list_config, q, starter)

    return response_builder.build()

  def templatePath(self):
    return "v2/modules/gsoc/admin/_slots_list.html"


class SlotsPage(RequestHandler):
  """View for the participant profile.
  """

  def djangoURLPatterns(self):
    return [
        url(r'^gsoc/admin/slots/%s$' % url_patterns.PROGRAM,
         self, name='gsoc_slots'),
    ]

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gsoc/admin/slots.html'

  def jsonContext(self):
    list_content = SlotsList(self.request, self.data).getListData()

    if not list_content:
      raise AccessViolation(
          'You do not have access to this data')

    return list_content.content()

  def post(self):
    data = self.data.POST.get('data')

    if not data:
      raise BadRequest("Missing data")

    parsed = simplejson.loads(data)

    for properties in parsed:
      if not all(i in properties for i in ['key', 'note', 'slots']):
        logging.warning("Missing value in '%s'" % properties)
        continue

      key_name = properties['key']
      note = properties['note']
      slots = properties['slots']

      if not slots.isdigit():
        logging.warning("Non-int value for slots: '%s'" % slots)
        continue

      slots = int(slots)

      def update_org_txn():
        org = GSoCOrganization.get_by_key_name(key_name)
        if not org:
          logging.warning("Invalid org_key '%s'" % key_name)
          return
        org.note = note
        org.slots = slots
        org.put()

      db.run_in_transaction(update_org_txn)

  def context(self):
    return {
      'page_name': 'Slots page',
      'slots_list': SlotsList(self.request, self.data),
    }
