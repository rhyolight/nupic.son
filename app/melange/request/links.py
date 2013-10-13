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

from django.core import urlresolvers

from melange.appengine import system

from soc.logic import program as program_logic
from soc.logic import site as site_logic
from soc.models import profile as profile_model


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
  if secure:
    protocol = 'https'
    hostname = system.getSecureHostname()
  else:
    protocol = 'http'

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
    # TODO(daniel): program's key should be acquired in a more efficient way
    program = profile.program
    kwargs = {
        'program': program.program_id,
        'sponsor': program.sponsor.key().name(),
        'user': profile.parent_key().name()
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
    kwargs = {'user': user.key().name()}
    return urlresolvers.reverse(url_name, kwargs=kwargs)

  def userOrg(self, profile, org, url_name):
    """Returns the URL of a page whose address contains parts associated
    with the specified profile and organization.

    Args:
      profile: profile entity.
      org: organization entity.
      url_name: the name with which a URL was registered with Django.

    Returns:
      The URL of the page matching the given names for the given profile
      and organization.
    """
    program = profile.program
    kwargs = {
        'sponsor': program_logic.getSponsorKey(program).name(),
        'program': program.program_id,
        'user': profile.parent_key().name(),
        'organization': org.link_id,
        }
    return urlresolvers.reverse(url_name, kwargs=kwargs)

  def userId(self, profile, entity_id, url_name):
    """Returns the URL of a page whose address contains parts associated
    with the specified profile and numeric identifier of some other entity.

    Args:
      profile: Profile entity.
      entity_id: Numeric ID of entity.
      url_name: The name with which a URL was registered with Django.

    Returns:
      The URL of the page matching the given names for the given profile
      and organization.
    """
    # TODO(daniel): it should be moved to a utility function; maybe even
    # in Profile model
    program_key = profile_model.Profile.program.get_value_for_datastore(
        profile)
    sponsor_id, program_id = program_key.name().split('/')

    kwargs = {
        'sponsor': sponsor_id,
        'program': program_id,
        'user': profile.parent_key().name(),
        'id': entity_id,
        }
    return urlresolvers.reverse(url_name, kwargs=kwargs)

  def organization(self, org, url_name):
    """Returns the URL of an organization's named page.

    Args:
      org: organization entity.
      url_name: the name with which a URL was registered with Django.

    Returns:
      The URL of the page matching the given name for the given organization.
    """
    program = org.program
    kwargs = {
        'sponsor': program_logic.getSponsorKey(program).name(),
        'program': program.program_id,
        'organization': org.link_id
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

  def userId(self, profile, entity_id, url_name, secure=False):
    """Returns the absolute URL of a page whose address contains parts
    associated with the specified profile and numeric identifier
    of some other entity.

    Args:
      profile: Profile entity.
      entity_id: Numeric ID of entity.
      url_name: The name with which a URL was registered with Django.
      secure: Whether the returned URL should support HTTPS or not.

    Returns:
      The URL of the page matching the given names for the given profile
      and organization.
    """
    relative_url = self._linker.userId(profile, entity_id, url_name)
    return getAbsoluteUrl(relative_url, self._hostname, secure=secure)

# TODO(daniel): hostname should not be obtained via interaction with database
# at module loading time.
ABSOLUTE_LINKER = AbsoluteLinker(LINKER, site_logic.getHostname())
