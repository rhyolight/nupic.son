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

from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.ext import db

from django import forms as djangoforms
from django import http
from django.utils import simplejson
from django.utils.translation import ugettext

from soc.logic import accounts
from soc.logic import cleaning
from soc.logic.exceptions import AccessViolation
from soc.logic.exceptions import BadRequest
from soc.views import forms
from soc.views.helper import lists
from soc.views.template import Template
from soc.models.user import User

from soc.modules.gsoc.models.grading_project_survey import GradingProjectSurvey
from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.models.profile import GSoCProfile
from soc.modules.gsoc.models.project_survey import ProjectSurvey
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.helper import url_patterns
from soc.modules.gsoc.views.helper.url_patterns import url


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
        url(r'admin/%s$' % url_patterns.PROGRAM,
         self, name='gsoc_admin_dashboard'),
    ]

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gsoc/admin/dashboard.html'

  def context(self):
    r = self.data.redirect
    r.program()

    context = {
        'page_name': 'Admin dashboard',
        'lookup_link': r.urlOf('lookup_gsoc_profile'),
        'slots_link': r.urlOf('gsoc_slots'),
        'slots_transfer_link': r.urlOf('gsoc_admin_slots_transfer'),
        'duplicates_link': r.urlOf('gsoc_view_duplicates'),
        'program_link': r.urlOf('edit_gsoc_program'),
        'timeline_link': r.urlOf('edit_gsoc_timeline'),
        'survey_reminder_link': r.urlOf('gsoc_survey_reminder_admin')
    }

    # HARDCODED
    survey_context = {
        'midterm_mentor_link': r.survey('midterm').urlOf(
            'gsoc_edit_mentor_evaluation'),
        'midterm_student_link': r.survey('midterm').urlOf(
            'gsoc_edit_student_evaluation'),
        'final_mentor_link': r.survey('final').urlOf(
            'gsoc_edit_mentor_evaluation'),
        'final_student_link': r.survey('final').urlOf(
            'gsoc_edit_student_evaluation'),
    }

    context.update(survey_context)
    return context

class LookupLinkIdPage(RequestHandler):
  """View for the participant profile.
  """

  def djangoURLPatterns(self):
    return [
        url(r'admin/lookup/%s$' % url_patterns.PROGRAM,
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
    options = [('', 'All'), ('true', 'New'), ('false', 'Veteran')]
    list_config.addSimpleColumn('new_org', 'New', width=25, options=options)
    list_config.addSimpleColumn('slots_desired', 'min', width=25)
    list_config.addSimpleColumn('max_slots_desired', 'max', width=25)
    list_config.addSimpleColumn('slots', 'Slots', width=50)
    list_config.setColumnEditable('slots', True)
    list_config.setColumnSummary('slots', 'sum', "<b>Total: {0}</b>")
    list_config.addSimpleColumn('note', 'Note')
    list_config.setColumnEditable('note', True) #, edittype='textarea')
    list_config.setDefaultPagination(False)
    list_config.setDefaultSort('name')
    list_config.addPostEditButton('save', "Save", "", [], refresh="none")

    self._list_config = list_config

  def context(self):
    description = 'List of organizations accepted into %s' % (
            self.data.program.name)

    list = lists.ListConfigurationResponse(
        self.data, self._list_config, 0, description)

    return {
        'lists': [list],
    }

  def post(self):
    idx = lists.getListIndex(self.request)
    if idx != 0:
      return False

    data = self.data.POST.get('data')

    if not data:
      raise BadRequest("Missing data")

    parsed = simplejson.loads(data)

    for key_name, properties in parsed.iteritems():
      note = properties.get('note')
      slots = properties.get('slots')

      if 'note' not in properties and 'slots' not in properties:
        logging.warning("Neither note or slots present in '%s'" % properties)
        continue

      if 'slots' in properties:
        if not slots.isdigit():
          logging.warning("Non-int value for slots: '%s'" % slots)
          properties.pop('slots')
        else:
          slots = int(slots)

      def update_org_txn():
        org = GSoCOrganization.get_by_key_name(key_name)
        if not org:
          logging.warning("Invalid org_key '%s'" % key_name)
          return
        if 'note' in properties:
          org.note = note
        if 'slots' in properties:
          org.slots = slots
        org.put()

      db.run_in_transaction(update_org_txn)

    return True

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
        url(r'admin/slots/%s$' % url_patterns.PROGRAM,
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
    slots_list = SlotsList(self.request, self.data)

    if not slots_list.post():
      raise AccessViolation(
          'You cannot change this data')

  def context(self):
    return {
      'page_name': 'Slots page',
      'slots_list': SlotsList(self.request, self.data),
    }

class SurveyReminderPage(RequestHandler):
  """Page to send out reminder emails to fill out a Survey.
  """

  def djangoURLPatterns(self):
    return [
        url(r'admin/survey_reminder/%s$' % url_patterns.PROGRAM,
            self, name='gsoc_survey_reminder_admin'),
    ]

  def checkAccess(self):
    self.check.isHost()

  def templatePath(self):
    return 'v2/modules/gsoc/admin/survey_reminder.html'

  def post(self):
    post_dict = self.request.POST

    task_params = {
        'program_key': self.data.program.key().id_or_name(),
        'survey_key': post_dict['key'],
        'survey_type': post_dict['type']
    }

    task = taskqueue.Task(url=self.data.redirect.urlOf('spawn_survey_reminders'),
                          params=task_params)
    task.add()

    self.response = http.HttpResponseRedirect(
        self.request.path+'?msg=Reminders are being sent')
    return

  def context(self):
    q = GradingProjectSurvey.all()
    q.filter('scope', self.data.program)
    mentor_surveys = q.fetch(1000)

    q = ProjectSurvey.all()
    q.filter('scope', self.data.program)
    student_surveys = q.fetch(1000)

    return {
      'page_name': 'Sending Evaluation Reminders',
      'mentor_surveys': mentor_surveys,
      'student_surveys': student_surveys,
      'msg': self.request.GET.get('msg', '')
    }
