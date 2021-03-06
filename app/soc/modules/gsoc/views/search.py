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

"""Module for the GSoC search page."""

import os

from melange.request import access
from soc.views.helper import url_patterns

from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper.url_patterns import url


class SearchGsocPage(base.GSoCRequestHandler):
  """View for the search gsoc page."""

  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def djangoURLPatterns(self):
    return [
        url(r'search/%s$' % url_patterns.PROGRAM, self, name='search_gsoc'),
    ]

  def context(self, data, check, mutator):
    return {
        'app_version': os.environ.get('CURRENT_VERSION_ID', '').split('.')[0],
        'page_name': 'Search GSoC',
        'cse_key': data.site.cse_key
    }

  def templatePath(self):
    return 'modules/gsoc/search.html'
