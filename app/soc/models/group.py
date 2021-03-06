# Copyright 2008 the Melange authors.
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

"""This module contains the Group Model."""


from google.appengine.ext import db

from django.utils.translation import ugettext

import soc.models.linkable
import soc.models.user


class Group(soc.models.linkable.Linkable):
  """Common data fields for all groups.
  """

  #: Required field storing name of the group.
  name = db.StringProperty(required=True,
      verbose_name=ugettext('Name'))
  name.help_text = ugettext('Complete, formal name of the group.')
  name.group = ugettext("1. Public Info")

  #: Required field storing short name of the group.
  #: It can be used for displaying group as sidebar menu item.
  short_name = db.StringProperty(required=True,
      verbose_name=ugettext('Short name'))
  short_name.help_text = ugettext('Short name used for sidebar menu')
  short_name.group = ugettext("1. Public Info")

  #: Required field storing a home page URL of the group.
  home_page = db.LinkProperty(required=True,
      verbose_name=ugettext('Home Page URL'))
  home_page.group = ugettext("1. Public Info")

  #: Required email address used as the "public" contact mechanism for
  #: the Group
  email = db.EmailProperty(required=True,
      verbose_name=ugettext('Email'))
  email.help_text = ugettext(
      "Enter an email address to be used by would-be members seeking "
      "additional information. This can be an individual's email address or a "
      "mailing list address; use whichever will work best for you.")
  email.group = ugettext("1. Public Info")

  #: Required field storing description of the group.
  description = db.TextProperty(required=True,
      verbose_name=ugettext('Description'))
  description.group = ugettext("1. Public Info")

  #: Optional public mailing list.
  pub_mailing_list = db.StringProperty(required=False,
      verbose_name=ugettext('Public Mailing List'))
  pub_mailing_list.help_text = ugettext(
      'Mailing list email address, URL to sign-up page, etc.')
  pub_mailing_list.group = ugettext("1. Public Info")

  #: Optional public IRC channel.
  irc_channel = db.StringProperty(required=False,
      verbose_name=ugettext('Public IRC Channel (and Network)'))
  irc_channel.group = ugettext("1. Public Info")

  #: Optional public feed URL
  feed_url = db.LinkProperty(verbose_name=ugettext('Feed URL'))
  feed_url.help_text = ugettext(
      'The URL should be a valid ATOM or RSS feed. '
      'Feed entries are shown on the home page.')
  feed_url.group = ugettext("1. Public Info")

  #: Required property showing the current status of the group
  #: new: the group has not been active yet
  #: active: the group is active
  #: invalid: the group has been marked as removed or banned
  status = db.StringProperty(required=True, default='active',
      choices=['new', 'active', 'invalid'])

  #: Custom message from the organization which will be displayed to
  #: the users, when they choose to apply to become org admin or mentor
  role_request_message = db.TextProperty(required=False,
      verbose_name=ugettext('Message for role requests.'))
  role_request_message.help_text = ugettext(
      'Here you can set a custom message that will be displayed to '
      'all users who apply to become either a mentor or an org admin for '
      'this organization.')
  role_request_message.group = ugettext('4. Organization Preferences')
