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

"""Tests for views used in the context of user and server errors."""

import contextlib

from django.conf import settings

from soc.views import errors

from tests import test_utils


# TODO(nathaniel): Is this really the best way to do this?
# TODO(nathaniel): Can this be eliminated post-Django-1.2?
@contextlib.contextmanager
def _debugFalse():
  """Sets django.conf.settings.DEBUG temporarily False."""
  old_debug_setting = settings.DEBUG
  settings.DEBUG = False
  yield
  settings.DEBUG = old_debug_setting


class NotFoundViewTest(test_utils.DjangoTestCase):
  """Tests Melange's response to an absent page."""

  def testUnheardOfPath(self):
    """Tests that some unheard-of URL gets a well-formed response."""
    with _debugFalse():
      response = self.get('/there-is-nothing-at-this-path')
      self.assertResponseNotFound(response)

# TODO(nathaniel): "ServerErrorViewTest" (test of a page containing a bug).
