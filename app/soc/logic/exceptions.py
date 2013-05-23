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

"""Module containing the exceptions from the AccessChecker class."""

import httplib


class Error(Exception):
  """Error class for the access_exception module."""

  status = httplib.INTERNAL_SERVER_ERROR


class GDocsLoginRequest(Error):
  """GDocs login required."""

  url_name = 'gdata_oauth_redirect'

  def __init__(self, path):
    """Instance constructor.

    Args:
      path: The path to which to direct the user after log-in.
    """
    self.path = path
