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

"""Module for the organization profile page."""

from django.utils import translation

from soc.logic import cleaning
from soc.views import forms

PROFILE_EXCLUDE = [
    'status', 'scope', 'slots', 'note', 'new_org',
    'link_id', 'proposal_extra', 'program'
    ]

HOMEPAGE_INFO_GROUP = translation.ugettext(
    '1. Homepage Info (displayed on org homepage)')

HOMEPAGE_FIELDS = [
    'tags', 'name', 'feed_url', 'home_page', 'pub_mailing_list',
    'description', 'ideas', 'contrib_template',
    'facebook', 'twitter', 'blog', 'google_plus',
]


class OrgProfileForm(forms.ModelForm):
  """Django form for the organization profile."""

  def __init__(self, bound_field_class, **kwargs):
    super(OrgProfileForm, self).__init__(bound_field_class, **kwargs)

    for field in HOMEPAGE_FIELDS:
      if field in self.fields:
        self.fields[field].group = HOMEPAGE_INFO_GROUP

    feed_url = self.fields.pop('feed_url')
    self.fields.insert(len(self.fields), 'feed_url', feed_url)

  clean_description = cleaning.clean_html_content('description')
  clean_contrib_template = cleaning.clean_html_content('contrib_template')
  clean_facebook = cleaning.clean_url('facebook')
  clean_twitter = cleaning.clean_url('twitter')
  clean_blog = cleaning.clean_url('blog')
  clean_logo_url = cleaning.clean_url('logo_url')
  clean_ideas = cleaning.clean_url('ideas')
  clean_pub_mailing_list = cleaning.clean_mailto('pub_mailing_list')
  clean_irc_channel = cleaning.clean_irc('irc_channel')
