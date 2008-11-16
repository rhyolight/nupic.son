#!/usr/bin/python2.5
#
# Copyright 2008 the Melange authors.
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

"""Views for Home Settings.
"""

__authors__ = [
    '"Sverre Rabbelier" <sverre@rabbelier.nl>',
  ]


from google.appengine.ext import db
from google.appengine.api import users

from django import forms
from django.utils.translation import ugettext_lazy

from soc.logic import dicts
from soc.logic import validate
from soc.logic.models import document as document_logic
from soc.views import helper
from soc.views.helper import widgets
from soc.views.models import base

import soc.models.home_settings
import soc.logic.models.home_settings
import soc.logic.dicts
import soc.views.helper
import soc.views.helper.widgets


class SettingsValidationForm(helper.forms.BaseForm):
  """Django form displayed when creating or editing Settings.
  
  This form includes validation functions for Settings fields.
  """

    # TODO(tlarsen): partial_path will be a hard-coded read-only
    #   field for some (most?) User Roles
  doc_partial_path = forms.CharField(required=False,
      label=soc.models.work.Work.partial_path.verbose_name,
      help_text=soc.models.work.Work.partial_path.help_text)

  # TODO(tlarsen): actually, using these two text fields to specify
  #   the Document is pretty cheesy; this needs to be some much better
  #   Role-scoped Document selector that we don't have yet
  doc_link_name = forms.CharField(required=False,
      label=soc.models.work.Work.link_name.verbose_name,
      help_text=soc.models.work.Work.link_name.help_text)

  def clean_feed_url(self):
    feed_url = self.cleaned_data.get('feed_url')

    if feed_url == '':
      # feed url not supplied (which is OK), so do not try to validate it
      return None
    
    if not validate.isFeedURLValid(feed_url):
      raise forms.ValidationError('This URL is not a valid ATOM or RSS feed.')

    return feed_url


class CreateForm(SettingsValidationForm):
  """Django form displayed when creating or editing Settings.
  """

  class Meta:
    """Inner Meta class that defines some behavior for the form.
    """
    #: db.Model subclass for which the form will gather information
    model = soc.models.home_settings.HomeSettings

    #: list of model fields which will *not* be gathered by the form
    exclude = ['inheritance_line', 'home']


class EditForm(CreateForm):
  """Django form displayed a Document is edited.
  """

  pass


class View(base.View):
  """View methods for the Document model
  """

  def __init__(self, original_params=None, original_rights=None):
    """Defines the fields and methods required for the base View class
    to provide the user with list, public, create, edit and delete views.

    Params:
      original_params: a dict with params for this View
      original_rights: a dict with right definitions for this View
    """

    params = {}
    rights = {}

    params['name'] = "Home Settings"
    params['name_short'] = "Home"
    params['name_plural'] = "Home Settings"

    params['edit_form'] = EditForm
    params['create_form'] = CreateForm

    # TODO(tlarsen) Add support for Django style template lookup
    params['edit_template'] = 'soc/models/edit.html'
    params['public_template'] = 'soc/home_settings/public.html'
    params['list_template'] = 'soc/models/list.html'

    params['lists_template'] = {
      'list_main': 'soc/list/list_main.html',
      'list_pagination': 'soc/list/list_pagination.html',
      'list_row': 'soc/home_settings/list/home_row.html',
      'list_heading': 'soc/home_settings/list/home_heading.html',
    }

    params['delete_redirect'] = '/home/list'

    params['save_message'] = [ugettext_lazy('Profile saved.')]

    params['edit_params'] = {
        self.DEF_SUBMIT_MSG_PARAM_NAME: self.DEF_SUBMIT_MSG_PROFILE_SAVED,
        }

    rights['list'] = [helper.access.checkIsDeveloper]
    rights['delete'] = [helper.access.checkIsDeveloper]

    params = dicts.merge(original_params, params)
    rights = dicts.merge(original_rights, rights)

    base.View.__init__(self, rights=rights, params=params)

    self._logic = soc.logic.models.home_settings.logic

  def _public(self, request, entity, context):
    """
    """

    if not entity:
      return

    try:
      home_doc = entity.home
    except db.Error:
      home_doc = None

    if home_doc:
      home_doc.content = helper.templates.unescape(home_doc.content)
      context['home_document'] = home_doc

  def _editGet(self, request, entity, form):
    """See base.View._editGet().
    """

    try:
      if entity.home:
        form.fields['doc_partial_path'].initial = entity.home.partial_path
        form.fields['doc_link_name'].initial = entity.home.link_name
    except db.Error:
      pass

  def _editPost(self, request, entity, fields):
    """See base.View._editPost().
    """

    doc_partial_path = fields['doc_partial_path']
    doc_link_name = fields['doc_link_name']

    # TODO notify the user if home_doc is not found
    home_doc = document_logic.logic.getFromFields(
    partial_path=doc_partial_path, link_name=doc_link_name)

    fields['home'] = home_doc


view = View()

create = view.create
edit = view.edit
delete = view.delete
list = view.list
public = view.public
