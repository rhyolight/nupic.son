# Copyright 2009 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing the core callback."""

from soc.views import legacy
from soc.tasks import mailer
from soc.views import oauth
from soc.views import site
from soc.views import user
from soc.views import warmup


class Callback(object):
  """Callback object that handles interaction between the core."""

  # This constant is required by soc.modules.core module. If its values
  # does not match the one defined there, the callback is rejected.
  API_VERSION = 1

  def __init__(self, core):
    """Initializes a new Callback object for the specified core."""

    self.core = core
    self.views = []

  def registerViews(self):
    """Instantiates all view objects."""
    self.views.append(legacy.Legacy())
    self.views.append(mailer.MailerTask())
    self.views.append(oauth.PopupOAuthRedirectPage())
    self.views.append(oauth.PopupOAuthVerified())
    self.views.append(site.EditSitePage())
    self.views.append(site.SiteHomepage())
    self.views.append(user.CreateUserPage())
    self.views.append(user.EditUserPage())
    self.views.append(warmup.WarmupPage())

  def registerWithSitemap(self):
    """Called by the server when sitemap entries should be registered."""
    self.core.requireUniqueService('registerWithSitemap')

    # Redesigned view registration
    for view in self.views:
      self.core.registerSitemapEntry(view.djangoURLPatterns())
