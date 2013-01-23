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

"""Module for the site global pages."""

import httplib

from django import http
from django.conf.urls import defaults


class WarmupPage(object):
  """A do-nothing view for handling App Engine's warmup requests."""

  def djangoURLPatterns(self):
    return [
        defaults.url(r'^_ah/warmup$', self, name='warmup'),
    ]

  def __call__(self, request, *args, **kwargs):
    """Does nothing and returns a 204 No Content response.

    Args:
      request: Ignored.
      *args: Ignored.
      **kwargs: Ignored.
    """
    return http.HttpResponse(status=httplib.NO_CONTENT)
