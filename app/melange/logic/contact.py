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

"""Logic for contacts."""

from melange.models import contact as contact_model
from melange.utils import rich_bool


def createContact(email=None, web_page=None, mailing_list=None,
    irc_channel=None, feed_url=None, google_plus=None, facebook=None,
    blog=None, twitter=None):
  """Creates a new contact based on the specified channels.

  Args:
    email: Email address.
    web_page: URL to a web page.
    mailing_list: Email address or URL to a mailing list.
    irc_channel: IRC channel.
    feed_url: Feed URL.
    google_plus: URL to Google Plus page.
    facebook: URL to Facebook page.
    blog: URL to a blog page.
    twitter: URL to Twitter profile.

  Returns:
    RichBool whose value is set to True if contact entity has been successfully
    created. In that case, extra part points to  the newly created object.
    Otherwise, RichBool whose value is set to False and extra part is a string
    that represents the reason why the action could not be completed.
  """
  try:
    return rich_bool.RichBool(True, contact_model.Contact(
        email=email, web_page=web_page, mailing_list=mailing_list,
        irc_channel=irc_channel, feed_url=feed_url, google_plus=google_plus,
        facebook=facebook, blog=blog, twitter=twitter))
  except ValueError as e:
    return rich_bool.RichBool(False, str(e))
