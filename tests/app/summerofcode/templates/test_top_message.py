# Copyright 2014 the Melange authors.
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

"""Tests for top message module."""

import unittest

from soc.views.helper import request_data

from summerofcode.templates import top_message

from tests import program_utils
from tests import timeline_utils


class OrgMemberRegistrationTopMessage(unittest.TestCase):
  """Unit tests for orgMemberRegistrationTopMessage function."""

  def setUp(self):
    """See unittest.TestCase.setUp for specification."""
    sponsor = program_utils.seedSponsor()
    self.program = program_utils.seedProgram(sponsor_key=sponsor.key())

    kwargs = {
        'sponsor': sponsor.key().name(),
        'program': self.program.program_id,
        }
    self.data = request_data.RequestData(None, None, kwargs)

  def testBeforeStudentSignUp(self):
    """Tests that correct message is returned before student sign-up."""
    self.program.timeline.student_signup_start = timeline_utils.future()
    self.program.timeline.put()

    message = top_message.orgMemberRegistrationTopMessage(self.data)
    self.assertEqual(
        message._message,
        top_message._ORG_MEMBER_REGISTER_MESSAGE_BEFORE_STUDENT_SIGN_UP %
            self.program.timeline.student_signup_start)

  def testDuringStudentSignUp(self):
    """Tests that correct message is returned during student sign-up."""
    self.program.timeline.student_signup_start = timeline_utils.past()
    self.program.timeline.student_signup_end = timeline_utils.future()
    self.program.timeline.put()

    message = top_message.orgMemberRegistrationTopMessage(self.data)

    # TODO(daniel): host should be obtained dynamically.
    register_url = (
        'http://some.testing.host.tld/gsoc/profile/register/student/%s' %
            self.program.key().name())
    self.assertEqual(
        message._message,
        top_message._ORG_MEMBER_REGISTER_MESSAGE_ACTIVE_STUDENT_SIGN_UP %
            register_url)

  def testAfterStudentSignUp(self):
    """Tests that correct message is returned after student sign-up."""
    self.program.timeline.student_signup_start = timeline_utils.past(delta=150)
    self.program.timeline.student_signup_end = timeline_utils.past(delta=100)
    self.program.timeline.put()

    message = top_message.orgMemberRegistrationTopMessage(self.data)
    self.assertIsNone(message)
