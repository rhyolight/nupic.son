# Copyright 2010 the Melange authors.
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

"""Middleware to process blobstore http request.

This middleware will check the wsgi.input http request stream and process
all the data since the bug in the blobstore API as referenced in the issue
http://code.google.com/p/googleappengine/issues/detail?id=2515 doesn't provide
the request data as specified in wsgi.input.

TODO: Remove this middleware as soon as the above mentioned issue in Appengine
is fixed.
"""

from soc.views.helper import blobstore as bs_helper


class BlobStoreMiddleware(object):
  """Middleware for building request POST data for blobstore.

  This class implements the specification defined at
  https://docs.djangoproject.com/en/dev/topics/http/middleware/.
  """

  def process_request(self, request):
    """Process wsgi.input on POST requests.

    Args:
      request: A django.http.HttpRequest.

    Returns:
      None.
    """
    request.file_uploads = {}

    # we only care about POST and which has form data with file.
    if request.method == 'POST' and (
        'multipart/form-data' in request.META.get('CONTENT_TYPE', '')):
      # rewrite request.POST with the form data with file_uploads
      # blob info as a dictionary in request.file_uploads
      bs_helper.cacheUploads(request)

    return None
