# Copyright 2009 the Melange authors.
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

"""Module containing the GCI Callback.
"""

__authors__ = [
  '"Madhusudan C.S." <madhusudancs@gmail.com>',
  '"Daniel Hans" <dhans@google.com>',
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


from soc.modules.gci.tasks import bulk_create
from soc.modules.gci.tasks import org_app_survey as org_app_survey_tasks
from soc.modules.gci.tasks import parental_forms
from soc.modules.gci.tasks import ranking_update
from soc.modules.gci.tasks import task_update


class Callback(object):
  """Callback object that handles interaction between the core.
  """

  API_VERSION = 1

  def __init__(self, core):
    """Initializes a new Callback object for the specified core.
    """

    self.core = core

  def registerWithSitemap(self):
    """Called by the server when sitemap entries should be registered.
    """

    self.core.requireUniqueService('registerWithSitemap')

    # register GCI GAE Tasks URL's
    self.core.registerSitemapEntry(bulk_create.getDjangoURLPatterns())
    self.core.registerSitemapEntry(org_app_survey_tasks.getDjangoURLPatterns())
    self.core.registerSitemapEntry(parental_forms.getDjangoURLPatterns())
    self.core.registerSitemapEntry(ranking_update.getDjangoURLPatterns())
    self.core.registerSitemapEntry(task_update.getDjangoURLPatterns())
