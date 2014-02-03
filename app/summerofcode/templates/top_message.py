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

from django.utils import translation

from melange.request import links
from melange.templates import top_message

from summerofcode.views.helper import urls

TEMPLATE_PATH = 'summerofcode/_top_message.html'

_ORG_MEMBER_REGISTER_MESSAGE_ACTIVE_STUDENT_SIGN_UP = translation.ugettext(
    'Use the form below only to register as an organization member. '
    'If you want to participate as a student, please go to <a href="%s">'
    'the student registration page</a>. Keep in mind that if you have '
    'created an organization member profile, you <strong>will not</strong> '
    'be able to sign up as a student anymore.')

_ORG_MEMBER_REGISTER_MESSAGE_BEFORE_STUDENT_SIGN_UP = translation.ugettext(
    'Use the form below only to register as an organization member. '
    'If you want to participate as a student, please wait until the '
    'registration open on %s. Keep in mind that if you have created an '
    'organization member profile, you <strong>will not</strong> be able to '
    'sign up as a student anymore.')

def orgMemberRegistrationTopMessage(data):
  """Returns a top message to be displayed on the top of the page to register
  as an organization member.

  Args:
    data: request_data.RequestData for the current request.

  Returns:
    top_message.TopMessage to be displayed on the top of the page.
  """
  if data.timeline.beforeStudentSignupStart():
    return top_message.TopMessage(
        data, TEMPLATE_PATH,
        _ORG_MEMBER_REGISTER_MESSAGE_BEFORE_STUDENT_SIGN_UP %
            data.timeline.studentSignupStart())
  elif not data.timeline.afterStudentSignupEnd():
    return top_message.TopMessage(
        data, TEMPLATE_PATH,
        _ORG_MEMBER_REGISTER_MESSAGE_ACTIVE_STUDENT_SIGN_UP %
            links.ABSOLUTE_LINKER.program(
                data.program, urls.UrlNames.PROFILE_REGISTER_AS_STUDENT,
                secure=True))
  else:
    return None
