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

from django.forms import util
from django.template.defaultfilters import filesizeformat
from django.utils import translation

from melange.request import access
from melange.request import exception
from soc.models import static_content
from soc.views import template
from soc.views import base_templates
from soc.views.helper import blobstore as bs_helper
from soc.views.helper import lists
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

  content = gci_forms.FileField(required=True)

  def addFileRequiredError(self):
    """Appends a form error message indicating that the file field is required.
    """
    if not self._errors:
      self._errors = util.ErrorDict()

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

  # Allow only program hosts to upload static content.
  access_checker = access.PROGRAM_ADMINISTRATOR_ACCESS_CHECKER

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

    # TODO(nathaniel): make this .program() call unnecessary.
    data.redirect.program()

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

    return data.redirect.to(url_names.GCI_CONTENT_UPLOAD, validated=True)


class StaticContentDownload(base.GCIRequestHandler):
  """View for downloading the static content."""

  def djangoURLPatterns(self):
    """The URL pattern for the view."""
    return [
        url(r'content/download/%s$' % url_patterns.STATIC_CONTENT, self,
            name=url_names.GCI_CONTENT_DOWNLOAD)]

  def checkAccess(self, data, check, mutator):
    """Allows public anonymous downloads when program is visible."""
    check.isProgramVisible()

  def get(self, data, check, mutator):
    """Allows public to download the content anonymously."""
    content_id = data.kwargs.get('content_id')
    if not content_id:
      raise exception.NotFound(message=DEF_CONTENT_NOT_FOUND)

    q = static_content.StaticContent.all()
    q.filter('content_id', content_id)
    entity = q.get()
    if not entity:
      raise exception.NotFound(message=DEF_CONTENT_NOT_FOUND)

    return bs_helper.sendBlob(entity.content)


class StaticContentList(template.Template):
  """List that displays all the publicly anonymously downloadable content."""

  IDX = 0

  def __init__(self, data):
    """Initializes a new object.

    Args:
      data: RequestData object associated with the request
    """
    self.data = data
    self.data.redirect.program()

    list_config = lists.ListConfiguration()
    list_config.addPlainTextColumn('name', 'Name',
        lambda entity, *args: entity.content.filename)
    list_config.addPlainTextColumn('size', 'Size',
        lambda entity, *args: filesizeformat(entity.content.size))
    list_config.setDefaultSort('name')

    list_config.setRowAction(lambda e, *args: self.data.redirect.staticContent(
        e.content_id).urlOf(url_names.GCI_CONTENT_DOWNLOAD))

    self._list_config = list_config

  def context(self):
    list_configuration_response = lists.ListConfigurationResponse(
        self.data, self._list_config, idx=self.IDX,
        description='Downloads - %s' % (
            self.data.program.name))

    return {
        'lists': [list_configuration_response],
        }

  def getListData(self):
    """Returns the list data as requested by the current request.

    If the lists as requested is not supported by this component None is
    returned.
    """
    idx = lists.getListIndex(self.data.request)
    if idx == self.IDX:
      starter = lists.keyStarter
      query = static_content.StaticContent.all()
      query.ancestor(self.data.program)

      response_builder = lists.RawQueryContentResponseBuilder(
          self.data.request, self._list_config, query, starter)
      return response_builder.build()
    else:
      return None

  def templatePath(self):
    return 'modules/gci/static_content/_list.html'


class StaticContentListPage(base.GCIRequestHandler):
  """View that lists all the static content uploaded for the program."""

  def djangoURLPatterns(self):
    """The URL pattern for the view."""
    return [
        url(r'content/list/%s$' % url_patterns.PROGRAM, self,
            name=url_names.GCI_CONTENT_LIST)]

  def checkAccess(self, data, check, mutator):
    """Allows public anonymous access when program is visible."""
    check.isProgramVisible()

  def jsonContext(self, data, check, mutator):
    list_content = StaticContentList(data).getListData()
    if list_content:
      return list_content.content()
    else:
      raise exception.Forbidden(message='You do not have access to this data')

  def context(self, data, check, mutator):
    return {
        'page_name': "Downloads - %s" % data.program.name,
        'static_content_list': StaticContentList(data),
        'program_select': base_templates.ProgramSelect(
            data, url_names.GCI_CONTENT_LIST),
    }

  def templatePath(self):
    return 'modules/gci/static_content/list_page.html'
