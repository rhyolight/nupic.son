# Copyright 2013 the Melange authors.
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

"""Module containing views for the Summer Of Code organization homepage."""

from django.utils import translation

from melange.request import access

from soc.views.helper import url_patterns

from soc.modules.gsoc.views import base
from soc.modules.gsoc.views.helper import url_patterns as soc_url_patterns

from summerofcode.views.helper import urls


ORG_HOME_PAGE_TITLE = translation.ugettext('%s')


class OrgHomePage(base.GSoCRequestHandler):
  """View to display organization homepage."""

  access_checker = access.ALL_ALLOWED_ACCESS_CHECKER

  def templatePath(self):
    """See base.RequestHandler.templatePath for specification."""
    return 'modules/gsoc/org_home/base.html'

  def djangoURLPatterns(self):
    """See base.RequestHandler.djangoURLPatterns for specification."""
    # TODO(daniel): should we keep all these legacy patterns here?
    # TODO(daniel): remove '2' when old view is not ready
    return [
        soc_url_patterns.url(r'org2/%s$' % url_patterns.ORG, self,
            name=urls.UrlNames.ORG_HOME),
        soc_url_patterns.url(r'org2/show/%s$' % url_patterns.ORG, self),
        soc_url_patterns.url(r'org2/home/%s$' % url_patterns.ORG, self),
    ]

  def context(self, data, check, mutator):
    """See base.RequestHandler.context for specification."""
    context = {
        'page_name': ORG_HOME_PAGE_TITLE % data.url_ndb_org.name,
        'organization': data.url_ndb_org,
    }
    return context
