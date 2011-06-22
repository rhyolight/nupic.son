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

"""Module containing views for Open Auth.
"""

__authors__ = [
  '"Orcun Avsar" <orc.avs@gmail.com>',
]


from django.conf.urls.defaults import url as django_url

from soc.views.helper.gdata_apis import gdocs_service_helper

from soc.modules.gsoc.views.base import RequestHandler


class OAuthRedirectPage(RequestHandler):
  """Redirect page to Google Documents.
  """

  def djangoURLPatterns(self):
    patterns = [
        django_url(r'^oauth/redirect$', self, name='oauth_redirect'),
    ]
    return patterns

  def checkAccess(self):
    self.check.isUser()

  def context(self):
    service = gdocs_service_helper.createGDocsService(self.request)
    next = '%s?next=%s' % (self.redirect.urlOf('oauth_verify'),
                           self.request.GET.get('next','/'))
    url = gdocs_service_helper.generateOAuthRedirectURL(
        service, self.data.user,
        next)
    context = {
        'approval_page_url': url,
        'page_name': 'Authorization Required',
    }
    return context

  def templatePath(self):
    """Override this method to define a rendering template
    """
    pass


class OAuthVerifyToken(RequestHandler):
  """Verify request token and redirect user.
  """

  def djangoURLPatterns(self):
    patterns = [
        django_url(r'^oauth/verify$', self, name='oauth_verify'),
    ]
    return patterns

  def get(self):
    service = gdocs_service_helper.createGDocsService(self.request)
    gdocs_service_helper.checkOAuthVerifier(service, self.request,
                                            self.data.user)
    next = self.request.GET.get('next','/')
    self.redirect.toUrl(next)
    return self.response
