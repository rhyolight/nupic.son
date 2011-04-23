#!/usr/bin/env python2.5
#
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

"""Module for constructing core URL patterns
"""

__authors__ = [
  '"Madhusudan.C.S" <madhusudancs@gmail.com>',
  ]


from soc.models import linkable

def captureLinkId(name):
  """Returns a capture group for a link id with the specified name.
  """
  return r'(?P<%s>%s)' % (name, linkable.LINK_ID_PATTERN_CORE)


def namedLinkIdPattern(names):
  """Returns a link ID pattern consisting of named parts.

  The returned pattern does not start or end with a /, the parts are however
  concatenated with a /.

  Args:
    names: The names that should be given to the different parts.
  """
  named_patterns = []
  for name in names:
    named_patterns.append(captureLinkId(name))

  return r'/'.join(named_patterns)


USER = namedLinkIdPattern(['link_id'])
