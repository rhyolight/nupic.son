# Copyright 2013 the Melange authors.
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

"""Module for uploading GCI's static resource files."""

from google.appengine.ext import blobstore

from django.utils import translation

from melange.request import exception
from soc.models import static_content
from soc.views.helper import blobstore as bs_helper
from soc.views.helper import url_patterns

from soc.modules.gci.views import base
from soc.modules.gci.views import forms as gci_forms
from soc.modules.gci.views.helper import url_names
from soc.modules.gci.views.helper.url_patterns import url


CONTENT_KEY_NAME_FMT = '%(program_key_name)s/%(content_id)s'

DEF_CONTENT_NOT_FOUND = translation.ugettext('Content with given ID not found')

DEF_NO_UPLOAD = translation.ugettext('An error occurred, please upload a file.')


class ContentUploadForm(gci_forms.GCIModelForm):
  """Django form to upload a static file.
  """

  class Meta:
    model = static_content.StaticContent
    css_prefix = 'gci_static_content'
    fields = ['content_id', 'content']

  content = gci_forms.FileField(required=False)

  def addFileRequiredError(self):
    """Appends a form error message indicating that the file field is required.
    """
    if not self._errors:
      self._errors = ErrorDict()

    self._errors['content'] = self.error_class([DEF_NO_UPLOAD])

  def clean_upload_of_work(self):
    """Ensure that file field has data."""
    cleaned_data = self.cleaned_data

    upload = cleaned_data.get('content')

    # Although we need the ValidationError exception the message there
    # is dummy because it won't pass through the Appengine's Blobstore
    # API. We use the same error message when adding the form error.
    # See self.addFileRequiredError method.
    if not upload:
      raise gci_forms.ValidationError(DEF_NO_UPLOAD)

    return upload


class StaticContentUpload(base.GCIRequestHandler):
  """View for uploading static content."""

  def djangoURLPatterns(self):
    """The URL pattern for the view.
    """
    return [
        url(r'content/upload/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_CONTENT_UPLOAD)]

  def checkAccess(self, data, check, mutator):
    """Allows access only to program host."""
    check.isHost()

  def templatePath(self):
    """Returns the path to the template."""
    return 'modules/gci/static_content/base.html'

  def jsonContext(self, data, check, mutator):
    """Returns the blobstore upload URL on an XHR."""
    # TODO(nathaniel): make this .program() call unnecessary.
    data.redirect.program()

    url = data.redirect.urlOf(url_names.GCI_CONTENT_UPLOAD, secure=True)
    return {
        'upload_link': blobstore.create_upload_url(url),
        }

  def context(self, data, check, mutator):
    """Handler for default HTTP GET request."""
    context = {
        'page_name': 'Static content upload'
        }

    upload_form = ContentUploadForm()

    # TODO(ljvderijk): This can be removed when AppEngine supports 200 response
    # in the BlobStore API.
    if data.GET:
      for key, error in data.GET.iteritems():
        if not key.startswith('error_'):
          continue
        field_name = key.split('error_', 1)[1]
        upload_form.errors[field_name] = upload_form.error_class([error])

    context['form'] = upload_form

    return context

  def post(self, data, check, mutator):
    """Handles POST requests for uploading static content."""
    form = ContentUploadForm(data=data.POST, files=data.request.file_uploads)

    if not form.is_valid():
      # we are not storing this form, remove the uploaded blobs from the cloud
      for f in data.request.file_uploads.itervalues():
        f.delete()

      # since this is a file upload we must return a 300 response
      extra_args = []
      for field, error in form.errors.iteritems():
        extra_args.append('error_%s=%s' %(field, error.as_text()))

      return data.redirect.to(url_names.GCI_CONTENT_UPLOAD, extra=extra_args)

    # delete existing data
    cleaned_data = form.cleaned_data
    r = data.request.file_uploads
    for field_name in data.request.file_uploads.keys():
      if field_name in cleaned_data and form.instance:
        existing = getattr(form.instance, field_name)
        if existing:
          existing.delete()

    if form.instance:
      form.save()
    else:
      form.create(key_name=CONTENT_KEY_NAME_FMT % {
          'program_key_name': data.program.key().name(),
          'content_id': form.cleaned_data.get('content_id'),
        }, parent=data.program)

    # TODO(nathaniel): make this .program() call unnecessary.
    data.redirect.program()

    return data.redirect.to(url_names.GCI_CONTENT_UPLOAD)


class StaticContentDownload(base.GCIRequestHandler):
  """View for downloading the static content."""

  def djangoURLPatterns(self):
    """The URL pattern for the view."""
    return [
        url(r'content/%s$' % url_patterns.STATIC_CONTENT, self,
            name=url_names.GCI_CONTENT_DOWNLOAD)]

  def checkAccess(self, data, check, mutator):
    """Allows public anonymous downloads when program is visible."""
    check.isProgramVisible()

  def get(self, data, check, mutator):
    """Allows public to download the content anonymously."""
    content_id = data.kwargs.get('content_id')
    if not content_id:
      diaf
      raise exception.NotFound(message=DEF_CONTENT_NOT_FOUND)

    q = static_content.StaticContent.all()
    q.filter('content_id', content_id)
    entity = q.get()
    if not entity:
      diaf
      raise exception.NotFound(message=DEF_CONTENT_NOT_FOUND)

    return bs_helper.sendBlob(entity.content)
