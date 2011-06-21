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

"""Module for the GSoC statistics page."""

__authors__ = [
  '"Daniel Hans" <dhans@google.com>',
]


from google.appengine.ext import db

from django.utils import simplejson
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext

from soc.views import forms
from soc.views.template import Template
from soc.views.toggle_button import ToggleButtonTemplate

from soc.modules.gsoc.models.statistic import GSoCStatistic
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.helper.url_patterns import url

from soc.modules.gsoc.statistics import mapping
from soc.modules.gsoc.statistics.presentation import GvizPresenter
from soc.modules.gsoc.statistics.presentation import JsonPresenter


class ManageActions(Template):
  """Template to render the left side admin actions.
  """

  IS_VISIBLE_HELP_MSG = ugettext(
      'Whether this statistic is publicly visible to all users or not.')


  def context(self):
    self.toggle_buttons = [
        ToggleButtonTemplate(
            self.data, 'on_off', 'Is visible', 'is-visible-statistic',
            None,
            checked=True,
            help_text=self.IS_VISIBLE_HELP_MSG,
            labels = {
                'checked': 'Yes',
                'unchecked': 'No',
        })]
    
    return {
        'toggle_buttons': self.toggle_buttons
    }

  def templatePath(self):
    return "v2/modules/gsoc/proposal/_user_action.html"

class UnsupportedFormatException(Exception):
  pass


class StatisticDashboard(RequestHandler):
  """View for the statistic page.
  """

  def djangoURLPatterns(self):
    return [
         url(r'statistic/dashboard$', self, name='gsoc_statistic_dashboard'),
    ]

  def templatePath(self):
    return 'v2/modules/gsoc/statistic/base.html'

  def checkAccess(self):
    pass

  def context(self):
    return {
        'fetch_urls': self._constructFetchUrls(),
        'manage_urls': self._constructManageUrls(),
        'statistics': mapping.STATISTICS,
        'visualizations': mapping.VISUALIZATIONS,
        'manage_actions': ManageActions(self.data)
        }

  def _constructFetchUrls(self):
    fetch_urls = {}
    for name in mapping.STATISTIC_NAMES:
      fetch_urls[name] = reverse(
          'gsoc_statistic_fetch', kwargs={'key_name': name})

    return fetch_urls

  def _constructManageUrls(self):
    manage_urls = {}
    for name in mapping.STATISTIC_NAMES:
      manage_urls[name] = reverse(
          'gsoc_statistic_manage', kwargs={'key_name': name})
    return manage_urls

class StatisticFetcher(RequestHandler):
  """Loads data for a particular statistic.
  """

  def __init__(self):
    self._presenter = None

  def checkAccess(self):
    pass

  def djangoURLPatterns(self):
    return [
         url(r'statistic/fetch/(?P<key_name>(\w+))$', self,
             name='gsoc_statistic_fetch'),
    ]

  def _getPresentation(self, key_name):
    type = self.data.GET.get('type', 'json')

    if type == 'json':
      self.response['Content-Type'] = 'application/json'
      self._presenter = JsonPresenter()
    elif type == 'gviz':
      self.response['Content-Type'] = 'application/json'
      self._presenter = GvizPresenter()
    else:
      raise UnsupportedFormatException('Requested format is not supported.')

    return self._presenter.get(key_name)
    
  def jsonContext(self):
    key_name = self.data.kwargs['key_name']
    presentation = self._getPresentation(key_name)
    return presentation


class StatisticManager(RequestHandler):
  """Manages the statistic entities.
  """

  def checkAccess(self):
    key_name = self.data.kwargs['key_name']
    self.data.statistic = GSoCStatistic.get_by_key_name(key_name)

    self.check.isStatisticValid()

  def djangoURLPatterns(self):
    return [
         url(r'statistic/manage/(?P<key_name>(\w+))$', self,
             name='gsoc_statistic_manage'),
    ]

  def post(self):
    value = self.data.POST.get('value')
    if value == 'checked':
      is_visible = True
    elif value == 'unchecked':
      is_visible = False
    else:
      raise AccessViolation('Unsupported value sent to the server')

    if self.data.statistic.is_visible ^ is_visible:
      self.data.statistic.is_visible = is_visible
      db.put(self.data.statistic)
