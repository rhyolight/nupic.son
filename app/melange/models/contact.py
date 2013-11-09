# Copyright 2013 the Melange authors.
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

"""This module contains a model that stores web-based contact information."""

from google.appengine.ext import ndb

from melange.appengine import db


class Contact(ndb.Model):
  """Class that represents various web-based contact channels."""

  #: Field storing email address.
  email = ndb.StringProperty(validator=db.email_validator)

  #: Field storing URL to a web page.
  web_page = ndb.StringProperty(validator=db.link_validator)

  #: Field storing email address or URL to a mailing list.
  mailing_list = ndb.StringProperty()

  #: Field storing IRC channel.
  irc_channel = ndb.StringProperty()

  #: Field storing Feed URL.
  feed_url = ndb.StringProperty(validator=db.link_validator)

  #: Field storing URL to Google Plus page.
  google_plus = ndb.StringProperty(validator=db.link_validator)

  #: Field storing URL to Facebook page.
  facebook = ndb.StringProperty(validator=db.link_validator)

  #: Field storing URL to a blog page.
  blog = ndb.StringProperty(validator=db.link_validator)

  #: Field storing URL to Twitter profile.
  twitter = ndb.StringProperty(validator=db.link_validator)
