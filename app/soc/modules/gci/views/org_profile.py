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

"""Module for the GCI organization profile page."""

from google.appengine.ext import db

from melange.models import connection as connection_model
from melange.views import connection as connection_view

from soc.views.helper import url_patterns
from soc.views import org_profile

from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.gci.views.base import GCIRequestHandler
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url


PROFILE_EXCLUDE = org_profile.PROFILE_EXCLUDE + [
    'task_quota_limit', 'backup_winner', 'proposed_winners'
]


class OrgProfileForm(org_profile.OrgProfileForm):
  """Django form for the organization profile."""

  def __init__(self, **kwargs):
    super(OrgProfileForm, self).__init__(
        gci_forms.GCIBoundField, **kwargs)

  class Meta:
    model = GCIOrganization
    css_prefix = 'gci_org_page'
    exclude = PROFILE_EXCLUDE

  def templatePath(self):
    return gci_forms.TEMPLATE_PATH


class OrgCreateProfileForm(OrgProfileForm):
  """Django form to create the organization profile."""

  class Meta:
    model = GCIOrganization
    css_prefix = 'gci_org_page'
    exclude = PROFILE_EXCLUDE


class OrgProfilePage(GCIRequestHandler):
  """View for the Organization Profile page."""

  def djangoURLPatterns(self):
    return [
         url(r'profile/organization/%s$' % url_patterns.PROGRAM,
         self, name=url_names.CREATE_GCI_ORG_PROFILE),
         url(r'profile/organization/%s$' % url_patterns.ORG,
         self, name=url_names.EDIT_GCI_ORG_PROFILE),
    ]

  def checkAccess(self, data, check, mutator):
    check.isLoggedIn()
    check.isProgramVisible()

    if 'organization' in data.kwargs:
      check.isProfileActive()
      check.isOrgAdminForOrganization(data.organization)
      #probably check if the org is active
    else:
      data.organization = None
      mutator.orgAppFromOrgId()
      check.isOrgAppAccepted()
      check.isUserAdminForOrgApp()
      check.hasProfileOrRedirectToCreate('org_admin',
          get_params={'org_id': data.GET['org_id']})

  def templatePath(self):
    return 'modules/gci/org_profile/base.html'

  def context(self, data, check, mutator):
    if not data.organization:
      form = OrgCreateProfileForm(data=data.POST or None)
    else:
      form = OrgProfileForm(
          data=data.POST or None, instance=data.organization)

    context = {
        'page_name': "Organization profile",
        'forms': [form],
        'error': bool(form.errors),
        }

    if data.organization:
      # TODO(nathaniel): make this .organization() call unnecessary.
      data.redirect.organization()
      context['org_home_page_link'] = data.redirect.urlOf('gci_org_home')

    return context

  def post(self, data, check, mutator):
    org_profile = self.createOrgProfileFromForm(data)
    if org_profile:
      # TODO(nathaniel): make this .organization call unnecessary.
      data.redirect.organization(organization=org_profile)

      return data.redirect.to('edit_gci_org_profile', validated=True)
    else:
      # TODO(nathaniel): problematic self-call.
      return self.get(data, check, mutator)

  def createOrgProfileFromForm(self, data):
    """Creates a new organization based on the data inserted in the form.

    Args:
      data: A RequestData describing the current request.

    Returns:
      a newly created organization entity or None
    """
    if data.organization:
      form = OrgProfileForm(data=data.POST, instance=data.organization)
    else:
      form = OrgCreateProfileForm(data=data.POST)

    if not form.is_valid():
      return None

    if not data.organization:
      org_id = data.GET['org_id']
      form.cleaned_data['scope'] = data.program
      form.cleaned_data['program'] = data.program
      form.cleaned_data['link_id'] = org_id
      key_name = '%s/%s' % (data.program.key().name(), org_id)
      entity = createOrganizationTxn(data, data.profile.key(), form, key_name)
    else:
      entity = form.save()

    return entity


@db.transactional(xg=True)
def createOrganizationTxn(data, profile_key, form, key_name):
  """Creates a new organization in a transaction.

  Args:
    data: request_data.RequestData for the current request.
    profile_key: Profile key of an admin for the new organization.
    form: Form with organization data.
    key_name: Key name of the organization to create.

  Returns:
    Newly created organization entity.
  """
  organization = form.create(key_name=key_name)
  connection_view.createConnectionTxn(
      data, profile_key, organization,
      org_role=connection_model.ORG_ADMIN_ROLE,
      user_role=connection_model.ROLE)
  return organization
