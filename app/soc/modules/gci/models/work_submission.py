#!/usr/bin/env python
#
# Copyright 2009 the Melange authors.
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

"""This module contains the GCI WorkSubmission Model.
"""


from google.appengine.ext import db

from django.utils.translation import ugettext

import soc.models.user_submission


class GCIWorkSubmission(soc.models.user_submission.UserSubmission):
  """Model for work submissions for a task by students.

  Parent:
    soc.modules.gci.models.task.GCITask
  """

  #: Property containing an URL to this work or more information about it
  url_to_work = db.LinkProperty(
      required=False, verbose_name=ugettext('URL to your Work'))
  url_to_work.help_text = ugettext(
      'URL to a resource containing your work or more information about it')
