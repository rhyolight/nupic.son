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

"""Module containing views for Open Auth."""

from django.conf.urls.defaults import url as django_url

from soc.views.helper.gdata_apis import oauth as oauth_helper

# TODO(nathaniel): modules-gsoc code being imported in non modules-gsoc code.
from soc.modules.gsoc.views.base import GSoCRequestHandler


class OAuthRedirectPage(GSoCRequestHandler):
  """Redirect page to Google Documents."""

  def djangoURLPatterns(self):
    patterns = [
        django_url(r'^gdata/oauth/redirect$', self, name='gdata_oauth_redirect'),
    ]
    return patterns

  def checkAccess(self):
    self.check.isUser()

  def context(self):
    service = oauth_helper.createDocsService(self.data)
    next = '%s?next=%s' % (self.redirect.urlOf('gdata_oauth_verify'),
                           self.request.GET.get('next','/'))
    url = oauth_helper.generateOAuthRedirectURL(
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


class OAuthVerifyToken(GSoCRequestHandler):
  """Verify request token and redirect user."""

  def djangoURLPatterns(self):
    patterns = [
        django_url(r'^gdata/oauth/verify$', self, name='gdata_oauth_verify'),
    ]
    return patterns

  def get(self):
    service = oauth_helper.createDocsService(self.data)
    oauth_helper.checkOAuthVerifier(service, self.data)
    next = self.request.GET.get('next','/')
    self.response = self.redirect.toUrl(next)

    # TODO(nathaniel): This return value is currently ignored and not
    # actually part of the RequestHandler.get semantics.
    return self.response


class PopupOAuthRedirectPage(GSoCRequestHandler):
  """Redirects popup page to Google Documents."""

  def djangoURLPatterns(self):
    patterns = [
        django_url(r'^gdata/popup/oauth/redirect$', self,
                   name='gdata_popup_oauth_redirect'),
    ]
    return patterns

  def checkAccess(self):
    self.check.isUser()

  def get(self):
    access_token = oauth_helper.getAccessToken(self.data.user)
    if access_token:
      url = self.redirect.urlOf('gdata_popup_oauth_verified')
    else:
      service = oauth_helper.createDocsService(self.data)
      next = '%s?next=%s' % (self.redirect.urlOf('gdata_oauth_verify'),
                             self.redirect.urlOf('gdata_popup_oauth_verified'))
      url = oauth_helper.generateOAuthRedirectURL(
          service, self.data.user,
          next)
    self.response = self.redirect.toUrl(url)

    # TODO(nathaniel): This return value is currently ignored and not
    # actually part of the RequestHandler.get semantics.
    return self.response


class PopupOAuthVerified(GSoCRequestHandler):
  """ Calls parent window's methods to indicate successful login."""

  def djangoURLPatterns(self):
    patterns = [
        django_url(r'^gdata/popup/oauth/verified$', self,
                   name='gdata_popup_oauth_verified')
    ]
    return patterns

  def checkAccess(self):
    self.check.canAccessGoogleDocs()

  def get(self):
    html = (
        "<html><body><script type='text/javascript'>"
        "    window.opener.melange.gdata.loginSuccessful();"
        "    window.close();"
        "</script></body></html>"
    )
    self.response.write(html)
