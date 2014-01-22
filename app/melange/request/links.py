# Copyright 2012 the Melange authors.
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

"""Module for managing URL generation."""

from google.appengine.api import users
from google.appengine.ext import ndb

from django.core import urlresolvers

from melange.appengine import system
from melange.models import organization as org_model
from melange.models import profile as profile_model

from soc.logic import program as program_logic
from soc.logic import site as site_logic


def getAbsoluteUrl(relative_url, hostname, secure=False):
  """Constructs absolute URL based on the specified relative URL.

  Args:
    relative_url: Relative path to a resource.
    hostname: Name of the host.
    secure: Whether the URL should support HTTPS or not.

  Returns:
    A full path to the resource.
  """
  # TODO(nathaniel): consider using scheme-relative urls here?
  protocol = 'https' if secure and not system.isLocal() else 'http'

  return '%s://%s%s' % (protocol, hostname, relative_url)


class Linker(object):
  """URL creator for Melange."""

  def login(self, request):
    """Returns the URL to which the user should be directed to log in.

    Args:
      request: An http.HttpRequest describing the current request.

    Returns:
      The URL to which the user should be directed to log in.
    """
    return users.create_login_url(
        dest_url=request.get_full_path().encode('utf-8'))

  def logout(self, request):
    """Returns the URL to which the user should be directed to log out.

    Args:
      request: An http.HttpRequest describing the current request.

    Returns:
      The URL to which the user should be directed to log out.
    """
    return users.create_logout_url(request.get_full_path().encode('utf-8'))

  def site(self, url_name):
    """Returns the URL of a named page on the site.

    Args:
      url_name: The name with which a url was registered with Django
        (such as "edit_site_settings").

    Returns:
      The url of the site-wide page matching the given name.
    """
    return urlresolvers.reverse(url_name)

  def profile(self, profile, url_name):
    """Returns the URL of a profile's named page.

    Args:
      profile: A profile entity.
      url_name: The name with which a URL was registered with Django.

    Returns:
      The URL of the page matching the given name for the given profile.
    """
    if isinstance(profile, ndb.Model):
      profile_key = profile.key
    else:
      profile_key = profile.key()

    kwargs = {
        'program': profile_model.getProgramId(profile_key),
        'sponsor': profile_model.getSponsorId(profile_key),
        'user': profile_model.getUserId(profile_key)
         }
    return urlresolvers.reverse(url_name, kwargs=kwargs)

  def program(self, program, url_name):
    """Returns the URL of a program's named page.

    Args:
      program: A program.
      url_name: The name with which a URL was registered with Django.

    Returns:
      The URL of the page matching the given name for the given program.
    """
    kwargs = {
        'program': program.link_id,
        'sponsor': program_logic.getSponsorKey(program).name()
    }
    return urlresolvers.reverse(url_name, kwargs=kwargs)

  def sponsor(self, sponsor, url_name):
    """Returns the URL of a sponsor's named page.

    Args:
      sponsor: A sponsor.
      url_name: The name with which a URL was registered with Django.

    Returns:
      The URL of the page matching the given name for the given sponsor.
    """
    kwargs = {
        'sponsor': sponsor.key().name(),
    }
    return urlresolvers.reverse(url_name, kwargs=kwargs)

  def user(self, user, url_name):
    """Returns the URL of a user's named page.

    Args:
      user: User entity.
      url_name: The name with which a URL was registered with Django.

    Returns:
      The URL of the page matching the given name for the given user.
    """
    if isinstance(user, ndb.Model):
      user_id = user.key.id()
    else:
      user_id = user.key().name()
    kwargs = {'user': user_id}
    return urlresolvers.reverse(url_name, kwargs=kwargs)

  def userOrg(self, profile_key, org_key, url_name):
    """Returns the URL of a page whose address contains parts associated
    with the specified profile and organization.

    The specified profile and organization must come from the same program.

    Args:
      profile_key: Profile key.
      org: organization entity.
      url_name: the name with which a URL was registered with Django.

    Returns:
      The URL of the page matching the given names for the given profile
      and organization.
    """
    kwargs = {
        'sponsor': profile_model.getSponsorId(profile_key),
        'program': profile_model.getProgramId(profile_key),
        'user': profile_model.getUserId(profile_key),
        'organization': org_model.getOrgId(org_key),
        }
    return urlresolvers.reverse(url_name, kwargs=kwargs)

  def userId(self, profile_key, entity_id, url_name):
    """Returns the URL of a page whose address contains parts associated
    with the specified profile and numeric identifier of some other entity.

    Args:
      profile_key: Profile key.
      entity_id: Numeric ID of entity.
      url_name: The name with which a URL was registered with Django.

    Returns:
      The URL of the page matching the given names for the given profile
      and organization.
    """
    kwargs = {
        'sponsor': profile_model.getSponsorId(profile_key),
        'program': profile_model.getProgramId(profile_key),
        'user': profile_model.getUserId(profile_key),
        'id': entity_id,
        }
    return urlresolvers.reverse(url_name, kwargs=kwargs)

  def organization(self, org_key, url_name):
    """Returns the URL of an organization's named page.

    Args:
      org_key: Organization key.
      url_name: The name with which a URL was registered with Django.

    Returns:
      The URL of the page matching the given name for the given organization.
    """
    kwargs = {
        'sponsor': org_model.getSponsorId(org_key),
        'program': org_model.getProgramId(org_key),
        'organization': org_model.getOrgId(org_key)
        }
    return urlresolvers.reverse(url_name, kwargs=kwargs)

  def staticContent(self, program, content_id, url_name):
    """Returns the download URL for the given static content.

    Args:
      program: Program entity for which the requested static
          content belongs.
      content_id: The ID of the static content to be downloaded.
      url_name: The name with which a URL was registered with Django.
    """
    kwargs = {
        'sponsor': program_logic.getSponsorKey(program).name(),
        'program': program.link_id,
        'content_id': content_id
        }
    return urlresolvers.reverse(url_name, kwargs=kwargs)

# Since Linker is stateless, there might as well be just one of it.
LINKER = Linker()


# TODO(daniel): replace this class probably with something that can handle
# not only absolute URLs but also some other options, like GET arguments.
class AbsoluteLinker(object):
  """Absolute URL creator for Melange."""

  def __init__(self, linker, hostname):
    """Initializes a new instance of this class.

    Args:
      linker: Linker instance to create relative URLs.
      hostname: Hostname of the application defined as a string.
    """
    self._linker = linker
    self._hostname = hostname

  def program(self, program, url_name, secure=False):
    """Returns the absolute URL of a program's named page.

    Args:
      program: A program.
      url_name: The name with which a URL was registered with Django.
      secure: Whether the returned URL should support HTTPS or not.

    Returns:
      The URL of the page matching the given name for the given program.
    """
    relative_url = self._linker.program(program, url_name)
    return getAbsoluteUrl(relative_url, self._hostname, secure=secure)

  def userId(self, profile_key, entity_id, url_name, secure=False):
    """Returns the absolute URL of a page whose address contains parts
    associated with the specified profile and numeric identifier
    of some other entity.

    Args:
      profile: Profile key.
      entity_id: Numeric ID of entity.
      url_name: The name with which a URL was registered with Django.
      secure: Whether the returned URL should support HTTPS or not.

    Returns:
      The URL of the page matching the given names for the given profile
      and organization.
    """
    relative_url = self._linker.userId(profile_key, entity_id, url_name)
    return getAbsoluteUrl(relative_url, self._hostname, secure=secure)

# TODO(daniel): hostname should not be obtained via interaction with database
# at module loading time.
ABSOLUTE_LINKER = AbsoluteLinker(LINKER, site_logic.getHostname())
