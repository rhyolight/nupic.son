#!/usr/bin/env python
#
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

"""Module that contains a model to store Blob submissions.
"""


from google.appengine.ext import blobstore
from google.appengine.ext import db

from django.utils.translation import ugettext

from soc.models.organization import Organization
from soc.models.program import Program
from soc.models.user import User


class UserSubmission(db.Model):
  """Model for Blob submissions made by users.
  """

  #: User who made this submission
  user = db.ReferenceProperty(
      reference_class=User, required=True,
      collection_name='submissions')

  #: Program to which this submission belongs to
  program = db.ReferenceProperty(
      reference_class=Program, required=True,
      collection_name='submissions')

  #: Organization to which this submission belongs to
  org = db.ReferenceProperty(
      reference_class=Organization, required=True,
      collection_name='submissions')

  #: Property allowing the user to store information about this submission
  information = db.TextProperty(
      required=False, verbose_name=ugettext('Info'))
  information.help_text = ugettext(
      'Information about the work you submit for this task')

  #: Property pointing to the work uploaded as a file or archive
  upload_of_work = blobstore.BlobReferenceProperty(
      required=False, verbose_name=ugettext('Upload of Work'))
  upload_of_work.help_text = ugettext(
      'Your work uploaded as a single file or as archive '
      '(max file size: 32 MB)')

  #: Property containing the date when the work was submitted
  submitted_on = db.DateTimeProperty(
      required=True, auto_now_add=True,
      verbose_name=ugettext('Submitted on'))
