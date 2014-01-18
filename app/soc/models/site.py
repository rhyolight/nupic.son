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

"""This module contains the Site Model."""


from google.appengine.ext import db

from django.utils.translation import ugettext

import soc.models.program


class Site(db.Model):
  """Model of a Site, which stores per site configuration.

  The Site Model stores configuration information unique to the Melange
  web site as a whole. There may exist at most one singleton
  instance per application.
  """

  #: Reference to Document containing optional Terms of Service
  tos = db.ReferenceProperty(
    reference_class=soc.models.document.Document,
    verbose_name=ugettext('Terms of Service'),
    collection_name='tos')
  tos.help_text = ugettext(
      'Document containing optional Terms of Service for participating.')

  #: The official name of the site
  site_name = db.StringProperty(default="Melange",
      verbose_name=ugettext('Site Name'))
  site_name.help_text = ugettext('The official name of the Site')

  #: A notice that should be displayed site-wide
  site_notice = db.StringProperty(verbose_name=ugettext('Site Notice'))
  site_notice.help_text = ugettext('A notice that will be displayed site-wide')

  maintenance_start = db.DateTimeProperty(
      verbose_name=ugettext('Maintenance start date'))

  maintenance_end = db.DateTimeProperty(
      verbose_name=ugettext('Maintenance end date'))

  #: Whether the site is in the maintenance mode
  maintenance_mode = db.BooleanProperty(verbose_name=ugettext(
      'Maintenance mode'))

  #: Valid Google Custom Search Engine key. Used to load the appropriate
  #: search box in the search page.
  cse_key = db.StringProperty(verbose_name=ugettext('Custom Search Engine key'))
  cse_key.help_text = ugettext(
      'Google Custom Search Engine key for embedding a '
      'CSE search box into the website.')

  #: Valid Google Analytics tracking number, if entered every page
  #: is going to have Google Analytics JS initialization code in
  #: the footer with the given tracking number.
  ga_tracking_num = db.StringProperty(
      verbose_name=ugettext('Google Analytics'))
  ga_tracking_num.help_text = ugettext(
      'Valid Google Analytics tracking number. If the number is '
      'entered every page is going to have Google Analytics '
      'initialization code in footer.')

  #: Valid Google Client ID. Used to embed Google services.
  google_client_id = db.StringProperty(verbose_name=ugettext('Google Client ID'))
  google_client_id.help_text = ugettext(
      'Numerical part of a valid Google Client ID (e.g. 6813750723.project.googleusercontent.com).'
      'Retrieved from https://cloud.google.com/console/')

  #: Valid Google Client secret. Used to embed Google services.
  google_client_secret = db.StringProperty(verbose_name=ugettext('Google Client Secret'))
  google_client_secret.help_text = ugettext(
      'Valid Google Client secret. Retrieved from https://cloud.google.com/console/'
      'by creating a new client id for a web application.')

  #: Valid Google API Key. Used to embed Google services.
  google_api_key = db.StringProperty(verbose_name=ugettext('Google API'))
  google_api_key.help_text = ugettext(
      'Valid Google API Key. This key is used for '
      'embedding Google services into the website.')

  #: Valid Google API Key. Used to embed Google services.
  secondary_google_api_key = db.StringProperty(verbose_name=ugettext('Secondary Google API'))
  secondary_google_api_key.help_text = ugettext(
      'Valid Google API Key. This secondary key is used for '
      'embedding Google services into the website when '
      'accessed through the "hostname" url.')

  #: No Reply Email address used for sending notification emails to site users
  noreply_email = db.EmailProperty(verbose_name=ugettext('No reply email'))
  noreply_email.help_text = ugettext(
      'No reply email address is used for sending emails to site users. '
      'Email address provided in this field needs to be added as Developer '
      'in GAE admin console.')

  #: Optional field storing the url of the site logo.
  logo_url = db.LinkProperty(
      verbose_name=ugettext('Site logo'))
  logo_url.help_text = ugettext(
      'URL of the site logo.')

  #: XSRF tokens are generated using a secret key.  This field is not visible in
  #: /site/edit because it is hidden in soc.views.models.site, and is populated
  #: automatically by soc.logic.models.site.
  xsrf_secret_key = db.StringProperty(multiline=False)
  xsrf_secret_key.help_text = ugettext('An automatically generated random '
      'value used to prevent cross-site request forgery attacks.')

  #: Optional field storing the hostname
  hostname = db.StringProperty(
      verbose_name=ugettext('Hostname'))
  hostname.help_text = ugettext(
      'URL of the hostname.')

  #: Reference to Program which is currently active
  active_program = db.ReferenceProperty(
      reference_class=soc.models.program.Program,
      verbose_name=ugettext('Active Program'))
  active_program.help_text = ugettext(
      'The Program which is currently active.')

  #: Last GSoC program
  latest_gsoc = db.StringProperty(
      verbose_name=ugettext('Latest GSoC'))
  latest_gsoc.help_text = ugettext(
      'The key of the latest GSoC program')

  #: Last GCI program
  latest_gci = db.StringProperty(
      verbose_name=ugettext('Latest GCI'))
  latest_gci.help_text = ugettext(
      'The key of the latest GCI program')

  #: Optional public mailing list.
  mailing_list = db.StringProperty(required=False,
      verbose_name=ugettext('Mailing List'))
  mailing_list.help_text = ugettext(
      'Mailing list email address, URL to sign-up page, etc.')

  #: Optional public IRC channel.
  irc_channel = db.StringProperty(required=False,
      verbose_name=ugettext('Public IRC Channel'))
  irc_channel.help_text = ugettext(
     'Address of a public IRC channel.')

  #: Blog page about the site.
  blog = db.StringProperty(required=False,
      verbose_name=ugettext('Blog'))
  blog.help_text = ugettext('Blog page about the site.')

  #: Google Plus page of the site.
  google_plus = db.StringProperty(required=False,
      verbose_name=ugettext('Google+ page'))
  google_plus.help_text = ugettext('Google+ page of the site.')

  #: Field storing description of the site.
  description = db.TextProperty(verbose_name=ugettext('Description'))
  description.help_text = ugettext(
      'Description of the site to be placed on the site header.')
