# Copyright 2011 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing the Org Homepage view.
"""

from soc.views.helper import url_patterns
from soc.views.template import Template

from soc.modules.gci.views.base import RequestHandler
from soc.modules.gci.views.helper.url_patterns import url


class AboutUs(Template):
  """About us template.
  """
  def __init__(self, data):
    self.data = data
    
  def context(self):
    return {
        'description': self.data.organization.description,
    }
  
  def templatePath(self):
    return 'v2/modules/gci/org_home/_about_us.html'


class ContactUs(Template):
  """Organization Contact template.
  """

  def __init__(self, data):
    self.data = data

  def context(self):
    return {
        'organization': self.data.organization,
    }

  def templatePath(self):
    return "v2/modules/gci/org_home/_contact_us.html"


class OrgHomepage(RequestHandler):
  """Encapsulates all the methods required to render the org homepage.
  """
  def templatePath(self):
    return 'v2/modules/gci/org_home/base.html'

  def djangoURLPatterns(self):
    return [
        url(r'org/%s$' % url_patterns.ORG, self,
            name='gci_org_homepage'),
    ]
    
  def checkAccess(self):
    pass
  
  def context(self):
    context = {
        'page_name': '%s - Home page' % (self.data.organization.name),
        'about_us': AboutUs(self.data),
        'contact_us': ContactUs(self.data),
    }
    
    return context