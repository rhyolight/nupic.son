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

"""Module for the GCI view to bulk create GCITasks."""

from django import forms

from soc.views.helper import url_patterns

from soc.modules.gci.models.bulk_create_data import GCIBulkCreateData
from soc.modules.gci.tasks import bulk_create
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url


class BulkCreateForm(gci_forms.GCIModelForm):
  """Django form for the bulk create page.
  """

  class Meta:
    model = GCIBulkCreateData
    css_prefix = 'gci_bulk_create'
    fields = ['task_data']

  task_data = forms.CharField(label='Task Data', required=True,
                              widget=forms.Textarea)


class BulkCreate(GCIRequestHandler):
  """View for bulk creation of GCITasks.
  """

  def djangoURLPatterns(self):
    """The URL pattern for the view.
    """
    return [
        url(r'bulk/%s$' % url_patterns.ORG, self,
            name=url_names.GCI_TASK_BULK_CREATE)]

  def checkAccess(self, data, check, mutator):
    """Denies access if the currently logged user is not allowed to
    bulk create tasks.
    """
    check.isLoggedIn()
    check.canBulkCreateTask()

  def templatePath(self):
    """Returns the path to the template.
    """
    return 'modules/gci/bulk_create/base.html'

  def context(self, data, check, mutator):
    """Handler for default HTTP GET request."""
    context = {
        'page_name': 'Bulk upload tasks for %s' % data.organization.name,
        }

    # get a list of task type tags stored for the program entity
    tts = data.program.task_types
    context['types'] = ', '.join([str(x) for x in tts])

    if data.POST:
      form = BulkCreateForm(data=data.POST)
      context['form'] = form
    else:
      context['form'] = BulkCreateForm()

    return context

  def post(self, data, check, mutator):
    """Handles POST requests for the bulk create page."""
    form = BulkCreateForm(data=data.POST)

    if not form.is_valid():
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)

    bulk_create.spawnBulkCreateTasks(
        form.cleaned_data['task_data'], data.organization,
        data.ndb_profile)

    # TODO(nathaniel): make this .organization call unnecessary.
    data.redirect.organization(organization=data.organization)

    return data.redirect.to(
        url_names.GCI_TASK_BULK_CREATE, validated=True)
