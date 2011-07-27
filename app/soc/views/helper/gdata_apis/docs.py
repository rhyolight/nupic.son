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

"""Generic tools for GDocs. Contains helper functions to handle documents.
"""

__authors__ = [
  '"Orcun Avsar" <orc.avs@gmail.com>',
  ]


import StringIO

import gdata.docs


def find_documents(service, title='', categories=[]):
  """Finds and returns documents for given gdocs service.
  """

  q = gdata.docs.service.DocumentQuery(categories=categories)
  q['title'] = title
  feed = service.Query(q.ToUri())
  return feed


def get_content(service, resource_id, return_as):
  """Returns content of given entry.
  """

  stream_content = StringIO.StringIO()
  service.Export(resource_id, 'sample_file.'+return_as, file_handler=stream_content)
  return stream_content.getvalue()
