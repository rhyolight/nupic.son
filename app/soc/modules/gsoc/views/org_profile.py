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

"""Module for the GSoC organization profile page.
"""

__authors__ = [
  '"Daniel Hans" <daniel.m.hans@gmail.com>',
  ]


from soc.views import forms

from django import forms as djangoforms
from django.conf.urls.defaults import url
from django import forms as django_forms

from soc.logic import cleaning
from soc.logic.exceptions import NotFound

from soc.modules.gsoc.models.organization import GSoCOrganization

from soc.modules.gsoc.logic import cleaning as gsoc_cleaning
from soc.modules.gsoc.views.base import RequestHandler
from soc.modules.gsoc.views.base_templates import LoggedInMsg
from soc.modules.gsoc.views.helper import url_patterns


class OrgProfileForm(forms.ModelForm):
  """Django form for the organization profile.
  """

  def __init__(self, *args, **kwargs):
    super(OrgProfileForm, self).__init__(*args, **kwargs)

    fields = ['tags', 'name', 'feed_url', 'home_page', 'pub_mailing_list',
              'description', 'ideas', 'contrib_template',
              'facebook', 'twitter', 'blog']

    for field in fields:
      self.fields[field].group = '1. Homepage Info (displayed on org homepage)'

    feed_url = self.fields.pop('feed_url')
    self.fields.insert(len(self.fields), 'feed_url', feed_url)

  class Meta:
    model = GSoCOrganization
    css_prefix = 'gsoc_org_page'
    exclude = [
        'status', 'scope', 'scope_path', 'founder', 'founder', 'slots', 'note',
        'slots_calculated', 'nr_applications', 'nr_mentors', 'link_id',
        'proposal_extra',
    ]
    widgets = forms.choiceWidgets(GSoCOrganization,
        ['contact_country', 'shipping_country'])

  tags = djangoforms.CharField(label='Tags')
  clean_tags = gsoc_cleaning.cleanTagsList(
      'tags', gsoc_cleaning.COMMA_SEPARATOR)
  clean_description = cleaning.clean_html_content('description')
  clean_contrib_template = cleaning.clean_html_content('contrib_template')
  clean_facebook = cleaning.clean_url('facebook')
  clean_twitter = cleaning.clean_url('twitter')
  clean_blog = cleaning.clean_url('blog')
  clean_logo_url = cleaning.clean_url('logo_url')
  clean_ideas = cleaning.clean_url('ideas')
  clean_pub_mailing_list = cleaning.clean_mailto('pub_mailing_list')
  clean_irc_channel = cleaning.clean_irc('irc_channel')

  def clean_max_score(self):
    max_score = self.cleaned_data['max_score']
    if 1 <= max_score <= 12:
      return max_score
    raise django_forms.ValidationError("Specify a value between 1 and 12.")



class OrgCreateProfileForm(OrgProfileForm):
  """Django form to create the organization profile.
  """

  class Meta:
    model = GSoCOrganization
    css_prefix = 'gsoc_org_page'
    exclude = [
        'status', 'scope', 'scope_path', 'founder', 'founder', 'slots', 'note',
        'slots_calculated', 'nr_applications', 'nr_mentors', 'scoring_disabled',
        'proposal_extra',
    ]

    widgets = forms.choiceWidgets(GSoCOrganization,
        ['contact_country', 'shipping_country'])


class OrgProfilePage(RequestHandler):
  """View for the Organization Profile page.
  """

  def djangoURLPatterns(self):
    return [
         url(r'^gsoc/profile/organization/%s$' % url_patterns.PROGRAM,
         self, name='create_gsoc_org_profile'),
         url(r'^gsoc/profile/organization/%s$' % url_patterns.ORG,
         self, name='edit_gsoc_org_profile'),
    ]

  def checkAccess(self):
    self.check.isLoggedIn()
    self.check.isProgramActive()

    if 'organization' in self.data.kwargs:
      self.check.isProfileActive()
      key_name = '%s/%s/%s' % (
          self.data.kwargs['sponsor'],
          self.data.kwargs['program'],
          self.data.kwargs['organization']
          )
      self.data.org = GSoCOrganization.get_by_key_name(key_name)
      if not self.data.org:
        NotFound('Organization does not exist.')
      self.check.isOrgAdminForOrganization(self.data.org)
      #probably check if the org is active
    else:
      self.data.org = None
      self.check.fail("Org creation is not supported at this time")

  def templatePath(self):
    return 'v2/modules/gsoc/org_profile/base.html'

  def context(self):
    if not self.data.org:
      form = OrgCreateProfileForm(self.data.POST or None)
    else:
      form = OrgProfileForm(self.data.POST or None, instance=self.data.org)

    if self.data.org.org_tag:
      tags = self.data.org.tags_string(self.data.org.org_tag)
      form.fields['tags'].initial = tags

    return {
        'page_name': "Organization profile",
        'form_top_msg': LoggedInMsg(self.data, apply_link=False),
        'forms': [form],
        'error': bool(form.errors),
        }

  def post(self):
    org_profile = self.createOrgProfileFromForm()
    if org_profile:
      self.redirect.organization(org_profile)
      self.redirect.to('edit_gsoc_org_profile', validated=True)
    else:
      self.get()

  def putWithOrgTags(self, form, entity):
    fields = form.cleaned_data

    entity.org_tag = {
        'tags': fields['tags'],
        'scope': entity.scope if entity else fields['scope']
    }

    entity.put()

  def createOrgProfileFromForm(self):
    """Creates a new organization based on the data inserted in the form.

    Returns:
      a newly created organization entity or None
    """

    if self.data.org:
      form = OrgProfileForm(self.data.POST, instance=self.data.org)
    else:
      form = OrgCreateProfileForm(self.data.POST)

    if not form.is_valid():
      return None

    if not self.data.org:
      form.cleaned_data['founder'] = self.data.user
      form.cleaned_data['scope'] = self.data.program
      form.cleaned_data['scope_path'] = self.data.program.key().name() 
      key_name = '%s/%s' % (
          self.data.program.key().name(),
          form.cleaned_data['link_id']
          )
      entity = form.create(commit=False, key_name=key_name)
      self.putWithOrgTags(form, entity)
      self.data.profile.org_admin_for.append(entity.key())
      self.data.profile.put()
    else:
      entity = form.save(commit=False)
      self.putWithOrgTags(form, entity)

    return entity
