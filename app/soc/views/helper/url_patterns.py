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

"""Module for constructing core URL patterns."""


from django.conf.urls import url as django_url

from soc.models import linkable


def url(prefix, regex, view, kwargs=None, name=None):
  """Constructs an url pattern prefixed with an arbitrary prefix

  Args: see django.conf.urls.url
  """
  return django_url('^%s/%s' % (prefix, regex), view, kwargs=kwargs, name=name)


class UrlPatternConstructor(object):
  """Interface which defines methods to construct URL patterns to be
  registered with Django.
  """

  def construct(self, regex, view, kwargs=None, name=None):
    """Constructs a new URL pattern for registration with Django.

    Args:
      regex: Regular expression associated with the pattern. Only URLs which do
        match the specified expression may be
      view: Actual subclass of base.RequestHandler to which the request is
        dispatched provided it matches the regular expression.
      kwargs: TODO(daniel): figure out what the hell is that here.
      name: Name with which the pattern is registered with Django. If specified,
        it may be used for reverse lookup, i.e. construction of actual URL
        based on the name of the matching pattern and kwargs.

    Returns:
      django.core.urlresolvers.RegexURLPattern to serve as a Django pattern.
    """
    raise NotImplementedError


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

  return r'/'.join([namedLinkIdPattern(names), r'(?P<key>(\w+))'])


_role = r'(?P<role>%s)/' % ("student|mentor|org_admin")
_document = ''.join([
    '(?P<prefix>%s)/',
    captureLinkId('sponsor'), '/',
    captureLinkId('program'), '/',
    captureLinkId('document'),
])
_org_document = ''.join([
    '(?P<prefix>%s)/',
    captureLinkId('sponsor'), '/',
    captureLinkId('program'), '/',
    captureLinkId('organization'), '/',
    captureLinkId('document'),
])
_mentor_role = r'(?P<role>%s)/' % ("org_admin|mentor")

ID = namedIdBasedPattern(['sponsor', 'program'])
KEY = namedKeyBasedPattern(['sponsor', 'program'])
SPONSOR = namedLinkIdPattern(['sponsor'])
PROGRAM = namedLinkIdPattern(['sponsor', 'program'])
CREATE_PROFILE = _role + namedLinkIdPattern(['sponsor', 'program'])
PROFILE = namedLinkIdPattern(['sponsor', 'program', 'user'])
MESSAGE = namedIdBasedPattern(['sponsor', 'program', 'user'])
DOCUMENT_FMT = _document
ORG_DOCUMENT_FMT = _org_document
ORG = namedLinkIdPattern(['sponsor', 'program', 'organization'])
INVITE = _mentor_role + ORG
REQUEST = _mentor_role + ORG

USER = namedLinkIdPattern(['user'])
USER_ID = namedIdBasedPattern(['sponsor', 'program', 'user'])
USER_ORG = namedLinkIdPattern(['sponsor', 'program', 'user', 'organization'])
CONNECT = namedLinkIdPattern(['sponsor', 'program', 'organization', 'link_id'])
SHOW_CONNECTION = namedIdBasedPattern(['sponsor', 'program', 'organization', 'user'])
ANONYMOUS_CONNECTION = _mentor_role + namedKeyBasedPattern(['sponsor', 'program'])
STATIC_CONTENT = namedLinkIdPattern(['sponsor', 'program', 'content_id'])
