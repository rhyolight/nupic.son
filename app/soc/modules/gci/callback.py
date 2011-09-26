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


from soc.modules.gci.tasks.updates import role_conversion


class Callback(object):
  """Callback object that handles interaction between the core.
  """

  API_VERSION = 1

  def __init__(self, core):
    """Initializes a new Callback object for the specified core.
    """

    self.core = core
    self.views = []

  def registerViews(self):
    """Instantiates all view objects.
    """
    from soc.modules.gci.views import bulk_create
    from soc.modules.gci.views import dashboard
    from soc.modules.gci.views import document
    from soc.modules.gci.views import homepage
    from soc.modules.gci.views import org_app
    from soc.modules.gci.views import profile
    from soc.modules.gci.views import program
    from soc.modules.gci.views import task

    self.views.append(bulk_create.BulkCreate())
    self.views.append(dashboard.Dashboard())
    self.views.append(document.DocumentPage())
    self.views.append(document.EditDocumentPage())
    self.views.append(document.EventsPage())
    self.views.append(homepage.Homepage())
    self.views.append(org_app.GCIOrgAppEditPage())
    self.views.append(org_app.GCIOrgAppPreviewPage())
    self.views.append(org_app.GCIOrgAppShowPage())
    self.views.append(org_app.GCIOrgAppTakePage())
    self.views.append(profile.GCIProfilePage())
    self.views.append(program.ProgramPage())
    self.views.append(program.TimelinePage())
    self.views.append(task.TaskViewPage())

    # Google Appengine Tasks
    from soc.modules.gci.tasks.bulk_create import BulkCreateTask
    from soc.modules.gci.tasks.task_update import TaskUpdate

    self.views.append(BulkCreateTask())
    self.views.append(TaskUpdate())

  def registerWithSitemap(self):
    """Called by the server when sitemap entries should be registered.
    """

    self.core.requireUniqueService('registerWithSitemap')

    # Redesigned view registration
    for view in self.views:
      self.core.registerSitemapEntry(view.djangoURLPatterns())

    self.core.registerSitemapEntry(role_conversion.getDjangoURLPatterns())

  def registerWithProgramMap(self):
    """Called by the server when program_map entries should be registered.
    """

    self.core.requireUniqueService('registerWithProgramMap')

    from soc.modules.gci.models.program import GCIProgram
    program_entities = GCIProgram.all().fetch(1000)
    map = ('GCI Programs', [
        (str(e.key()), e.name) for e in program_entities])

    self.core.registerProgramEntry(map)
