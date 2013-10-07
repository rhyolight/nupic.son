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

"""Module containing the StaticContent model."""

from google.appengine.ext import blobstore
from google.appengine.ext import db

from django.utils import translation


class StaticContent(db.Model):
  """Static content name and its blobstore key.

  Parent:
    soc.modules.gsoc.models.program.GSoCProgram or
    soc.modules.gci.models.program.GCIProgram
  """

  #: Identifier of the content which is the last part of its unique key name
  content_id = db.StringProperty(required=True,
      verbose_name=translation.ugettext('Content ID'))
  content_id.help_text = translation.ugettext(
      'Used as part of URL link to access this content.')

  #: Property pointing to the work uploaded as a file or archive
  content = blobstore.BlobReferenceProperty(
      required=True, verbose_name=translation.ugettext('Content'))
  content.help_text = translation.ugettext(
      'Static content as a single file or as archive (max file size: 32 MB)')

  #: Property containing the date when the content was first uploaded
  created_on = db.DateTimeProperty(
      required=True, auto_now_add=True,
      verbose_name=translation.ugettext('Created on'))

  #: Property containing the date when the content was updated
  updated_on = db.DateTimeProperty(
      required=True, auto_now=True,
      verbose_name=translation.ugettext('Updated on'))
