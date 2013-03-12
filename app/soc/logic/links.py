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

from django.core import urlresolvers

from soc.models import program as program_model


class Linker(object):
  """URL creator for Melange."""

  def site(self, url_name):
    """Returns the URL of a named page on the site.

    Args:
      url_name: The name with which a url was registered with Django
        (such as "edit_site_settings").

    Returns:
      The url of the site-wide page matching the given name.
    """
    return urlresolvers.reverse(url_name)

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
        'sponsor': program.scope.key().name()
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
