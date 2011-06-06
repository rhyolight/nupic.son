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


from django.utils import simplejson
from django.core.urlresolvers import reverse

from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.helper.url_patterns import url

from soc.modules.gsoc.statistics import mapping
from soc.modules.gsoc.statistics.presentation import GvizPresenter
from soc.modules.gsoc.statistics.presentation import JsonPresenter


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
    action_urls = self._constructActionUrls()
    return {
        'urls': str(action_urls),
        'statistics': mapping.STATISTICS,
        }

  def _constructActionUrls(self):
    action_urls = {}
    for name in mapping.STATISTIC_NAMES:
      action_urls[name] = reverse(
          'gsoc_statistic_fetch', kwargs={'key_name': name})

    return action_urls

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

