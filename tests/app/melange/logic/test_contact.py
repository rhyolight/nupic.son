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

"""Tests for contact logic."""

import unittest

from melange.logic import contact as contact_logic

TEST_EMAIL = 'test@example.com'
TEST_WEB_PAGE = 'http://www.test.page.com'
TEST_MAILING_LIST = 'mailinglist@example.com'
TEST_IRC_CHANNEL = 'irc://irc.freenode.net/test'
TEST_FEED_URL = 'http://www.test.feed.com'
TEST_GOOGLE_PLUS = 'http://www.test.google.plus.com'
TEST_FACEBOOK = 'http://www.test.facebook.com'
TEST_BLOG = 'http://www.test.blog.com'
TEST_TWITTER = 'http://www.test.twitter.com'

class CreateContactTest(unittest.TestCase):
  """Unit tests for createContact function."""

  def testValidData(self):
    """Tests that contact entity is created properly if all data is valid."""
    result = contact_logic.createContact(
        email=TEST_EMAIL, web_page=TEST_WEB_PAGE,
        mailing_list=TEST_MAILING_LIST, irc_channel=TEST_IRC_CHANNEL,
        feed_url=TEST_FEED_URL, google_plus=TEST_GOOGLE_PLUS,
        facebook=TEST_FACEBOOK, blog=TEST_BLOG, twitter=TEST_TWITTER)
    self.assertTrue(result)

    contact = result.extra
    self.assertEqual(contact.email, TEST_EMAIL)
    self.assertEqual(contact.web_page, TEST_WEB_PAGE)
    self.assertEqual(contact.irc_channel, TEST_IRC_CHANNEL),
    self.assertEqual(contact.mailing_list, TEST_MAILING_LIST)
    self.assertEqual(contact.feed_url, TEST_FEED_URL)
    self.assertEqual(contact.google_plus, TEST_GOOGLE_PLUS)
    self.assertEqual(contact.facebook, TEST_FACEBOOK)
    self.assertEqual(contact.blog, TEST_BLOG)
    self.assertEqual(contact.twitter, TEST_TWITTER)

  def testInvalidData(self):
    """Tests that contact entity is not created if data is not valid."""
    # email is not valid
    result = contact_logic.createContact(email='test@example')
    self.assertFalse(result)

    # email is an URL
    result = contact_logic.createContact(email='http://invalid.email.com')
    self.assertFalse(result)

    # web_page is not valid
    result = contact_logic.createContact(web_page='invalid')
    self.assertFalse(result)

    # web_page is an email
    result = contact_logic.createContact(web_page='invalid@example.com')
    self.assertFalse(result)

    # feed_url is not valid
    result = contact_logic.createContact(feed_url='invalid')
    self.assertFalse(result)

    # feed_url is an email
    result = contact_logic.createContact(feed_url='invalid@example.com')
    self.assertFalse(result)

    # google_plus is not valid
    result = contact_logic.createContact(google_plus='invalid')
    self.assertFalse(result)

    # google_plus is an email
    result = contact_logic.createContact(google_plus='invalid@example.com')
    self.assertFalse(result)

    # facebook is not valid
    result = contact_logic.createContact(facebook='invalid')
    self.assertFalse(result)

    # facebook is an email
    result = contact_logic.createContact(facebook='invalid@example.com')
    self.assertFalse(result)

    # blog is not valid
    result = contact_logic.createContact(blog='invalid')
    self.assertFalse(result)

    # blog is an email
    result = contact_logic.createContact(blog='invalid@example.com')
    self.assertFalse(result)

    # twitter is not valid
    result = contact_logic.createContact(twitter='invalid')
    self.assertFalse(result)

    # twitter is an email
    result = contact_logic.createContact(twitter='invalid@example.com')
    self.assertFalse(result)
