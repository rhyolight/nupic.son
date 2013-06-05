# Copyright 2008 the Melange authors.
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

"""Site (Model) query functions."""

from google.appengine.api import memcache

from melange.appengine import system
from soc.logic.helper import xsrfutil
from soc.models import site


def singleton():
  """Return singleton Site settings entity, since there is always only one."""
  return site.Site.get_or_insert('site')


def xsrfSecretKey(settings):
  """Return the secret key for use by the XSRF middleware.

  If the Site entity does not have a secret key, this method will also create
  one and persist it.

  Args:
    settings: the singleton Site entity

  Returns:
    a secret key.
  """
  if not settings.xsrf_secret_key:
    key = xsrfutil.newXsrfSecretKey()
    if not memcache.add("new_xsrf_secret_key", key):
      key = memcache.get("new_xsrf_secret_key")
    settings.xsrf_secret_key = key
    settings.put()
  return settings.xsrf_secret_key


def getHostname(data=None):
  """Returns the hostname (taking into account site hostname settings).

  Args:
    data: A RequestData object.

  Returns:
    The site hostname.
  """
  settings = data.site if data else singleton()
  return settings.hostname if settings.hostname else system.getRawHostname()


def isSecondaryHostname(data=None):
  """Identifies if the current request is from the secondary hostname.

  Args:
    data: A RequestData object.

  Returns:
    True if the current request is from the secondary hostname; False
      otherwise.
  """
  settings = data.site if data else singleton()
  return settings.hostname and settings.hostname in system.getRawHostname()
