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

"""Module for the GSoC organization profile page."""

from soc.views import forms

from django import forms as django_forms
from django.utils.translation import ugettext

from soc.views.helper import url_patterns
from soc.views import org_profile

from soc.modules.gsoc.models.organization import GSoCOrganization
from soc.modules.gsoc.views import base
from soc.modules.gsoc.views import forms as gsoc_forms
from soc.modules.gsoc.views.helper import url_names
from soc.modules.gsoc.views.helper.url_patterns import url

DEF_NO_ORG_ID_FOR_CREATE = ugettext(
    'There is no organization id specified to create a new organization.')

DEF_TAG_TOO_LONG = ugettext(
    'Each tag should be less than 450 characters, but tag "%s" has %d '
    'characters.')

PROFILE_EXCLUDE = org_profile.PROFILE_EXCLUDE + [
    'proposal_extra', 'tags',
]


class OrgProfileForm(org_profile.OrgProfileForm):
  """Django form for the organization profile."""

  def __init__(self, **kwargs):
    super(OrgProfileForm, self).__init__(
        gsoc_forms.GSoCBoundField, **kwargs)

    instance = self.instance

    field = self.fields['nonreq_proposal_extra']
    field.group = ugettext("4. Organization Preferences")
    field.initial = ', '.join(instance.proposal_extra) if instance else ''

    self.fields['tags'] = django_forms.CharField(
        required=False,
        label=ugettext('Tags'))
    self.fields['tags'].group = ugettext("1. Public Info")

    if self.instance:
      self.fields['tags'].initial = ', '.join(self.instance.tags)
      self.fields['tags'].group = org_profile.HOMEPAGE_INFO_GROUP
      self.fields['tags'].help_text = ugettext(
          'Comma separated list of organization tags. Each tag must be less '
          'than 450 characters.')

  class Meta:
    model = GSoCOrganization
    css_prefix = 'gsoc_org_page'
    exclude = PROFILE_EXCLUDE
    widgets = forms.choiceWidgets(GSoCOrganization,
        ['contact_country', 'shipping_country'])

  nonreq_proposal_extra = django_forms.CharField(
      label='Extra columns', required=False)
  nonreq_proposal_extra.help_text = ugettext('Comma separated list of values.')

  def clean_tags(self):
    tags = []
    for tag in self.data.get('tags').split(','):
      if tag:
        if len(tag) > 450:
          raise django_forms.ValidationError(
              DEF_TAG_TOO_LONG % (tag, len(tag)))
        tags.append(tag.strip())
    return tags

  def clean_nonreq_proposal_extra(self):
    values = self.cleaned_data['nonreq_proposal_extra']
    splitvalues = values.split(',')

    for value in splitvalues:
      if ' ' not in value.strip():
        continue

      raise django_forms.ValidationError(
          "Spaces not allowed in extra column mames.")

    return values

  def clean(self):
    if 'nonreq_proposal_extra' not in self.cleaned_data:
      return

    value = self.cleaned_data['nonreq_proposal_extra']

    if not value:
      self.cleaned_data['proposal_extra'] = []
    else:
      cols = [i.strip() for i in value.split(',') if i.strip()]
      self.cleaned_data['proposal_extra'] = cols

    # If there is a key called new_org in the form, probably maliciously
    # induced into the form data, since this field does not appear on the
    # org profile form, we need to make sure to remove it.
    self.cleaned_data.pop('new_org', None)

    return self.cleaned_data

  def clean_max_score(self):
    max_score = self.cleaned_data['max_score']
    if 1 <= max_score <= 12:
      return max_score
    raise django_forms.ValidationError("Specify a value between 1 and 12.")

  def templatePath(self):
    return gsoc_forms.TEMPLATE_PATH


class OrgCreateProfileForm(OrgProfileForm):
  """Django form to create the organization profile.
  """

  class Meta:
    model = GSoCOrganization
    css_prefix = 'gsoc_org_page'
    exclude = PROFILE_EXCLUDE
    widgets = forms.choiceWidgets(GSoCOrganization,
        ['contact_country', 'shipping_country'])


class OrgProfilePage(base.GSoCRequestHandler):
  """View for the Organization Profile page."""

  def djangoURLPatterns(self):
    return [
         url(r'profile/organization/%s$' % url_patterns.PROGRAM,
         self, name='create_gsoc_org_profile'),
         url(r'profile/organization/%s$' % url_patterns.ORG,
         self, name='edit_gsoc_org_profile'),
    ]

  def checkAccess(self, data, check, mutator):
    check.isProfileActive()
    check.isProgramVisible()

    if 'organization' in data.kwargs:
      check.isOrgAdminForOrganization(data.organization)
      #probably check if the org is active
    else:
      data.org_id = data.request.GET.get('org_id')

      mutator.orgAppRecord(data.org_id)

      if not data.org_id:
        check.fail(DEF_NO_ORG_ID_FOR_CREATE)
        return

      # For the creation of a new organization profile the org should not
      # exist yet.
      check.orgDoesnotExist(data.org_id)
      check.canCreateOrgProfile()

  def templatePath(self):
    return 'modules/gsoc/org_profile/base.html'

  def context(self, data, check, mutator):
    if not data.organization:
      form = OrgCreateProfileForm(data=data.POST or None)
    else:
      form = OrgProfileForm(data=data.POST or None, instance=data.organization)

    context = {
        'page_name': "Organization profile",
        'forms': [form],
        'error': bool(form.errors),
        }

    if data.organization:
      # TODO(nathaniel): make this .organization() unnecessary.
      data.redirect.organization()

      context['org_home_page_link'] = data.redirect.urlOf(
          url_names.GSOC_ORG_HOME)
      if (data.program.allocations_visible and
          data.timeline.beforeStudentsAnnounced()):
        context['slot_transfer_page_link'] = data.redirect.urlOf(
            'gsoc_slot_transfer')

    return context

  def post(self, data, check, mutator):
    org_profile = self.createOrgProfileFromForm(data)
    if org_profile:
      data.redirect.organization(organization=org_profile)
      return data.redirect.to('edit_gsoc_org_profile', validated=True)
    else:
      # TODO(nathaniel): problematic self-use.
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
      form.cleaned_data['scope'] = data.program
      form.cleaned_data['program'] = data.program
      form.cleaned_data['link_id'] = data.org_id
      form.cleaned_data['new_org'] = data.org_app_record.new_org
      key_name = '%s/%s' % (
          data.program.key().name(), form.cleaned_data['link_id'])
      # TODO(ljv): The backup admin is not assigned a role?
      entity = form.create(commit=True, key_name=key_name)
      data.profile.org_admin_for.append(entity.key())
      data.profile.is_org_admin = True
      data.profile.mentor_for.append(entity.key())
      data.profile.is_mentor = True
      data.profile.put()
    else:
      entity = form.save(commit=True)

    return entity
