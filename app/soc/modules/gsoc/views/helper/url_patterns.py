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

"""Module for constructing GSoC related URL patterns
"""

__authors__ = [
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


from django.conf.urls.defaults import url as django_url

from soc.models import linkable


def url(regex, view, kwargs=None, name=None):
  """Constructs an url pattern prefixed with ^gsoc/.

  Args: see django.conf.urls.defaults.url
  """
  return django_url('^gsoc/%s' % regex, view, kwargs=kwargs, name=name)


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


def namedIdBasedPattern(names):
  """Returns a url pattern consisting of named parts whose last element
  is a numeric id.
  """

  return r'/'.join([namedLinkIdPattern(names), r'(?P<id>(\d+))'])


def namedKeyBasedPattern(names):
  """Returns a url pattern consisting of named parts whose last element
  is a string representation of a Key instance.
  """

  return r'/'.join([namedLinkIdPattern(names), r'(?P<key>([\w-]+))'])


_role = r'(?P<role>%s)/' % ("student|mentor|org_admin")
_document = ''.join([
    captureLinkId('prefix'), '/',
    '(',
      "(%s/)|" % captureLinkId('scope'),
      '(',
        "%s/" % captureLinkId('sponsor'),
        '(',
        "%s/" % captureLinkId('program'),
          "(%s/)?" % captureLinkId('organization'),
        ')?',
      ')',
    ')',
    captureLinkId('document'),
])
_mentor_role = r'(?P<role>%s)/' % ("org_admin|mentor")

ID        = namedIdBasedPattern(['sponsor', 'program'])
KEY       = namedKeyBasedPattern(['sponsor', 'program'])
SPONSOR   = namedLinkIdPattern(['sponsor'])
PROGRAM   = namedLinkIdPattern(['sponsor', 'program'])
CREATE_PROFILE = _role + namedLinkIdPattern(['sponsor', 'program'])
PROFILE   = namedLinkIdPattern(['sponsor', 'program', 'user'])
DOCUMENT  = _document
SURVEY    = namedLinkIdPattern(['sponsor', 'program', 'survey'])
PROPOSAL  = namedIdBasedPattern(['sponsor', 'program'])
REVIEW    = namedIdBasedPattern(['sponsor', 'program', 'user'])
ORG       = namedLinkIdPattern(['sponsor', 'program', 'organization'])
INVITE    = _mentor_role + ORG
PROJECT   = namedIdBasedPattern(['sponsor', 'program', 'user'])
SURVEY_RECORD = namedIdBasedPattern(['sponsor', 'program', 'survey', 'user'])
