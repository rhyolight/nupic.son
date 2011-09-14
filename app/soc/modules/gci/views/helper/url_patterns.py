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

"""Module for constructing GCI related URL patterns
"""

__authors__ = [
  '"Lennard de Rijk" <ljvderijk@gmail.com>',
  '"Selwyn Jacob" <selwynjacob90@gmail.com>',
  ]


from django.conf.urls.defaults import url as django_url

from soc.views.helper import url_patterns


def url(regex, view, kwargs=None, name=None):
  """Constructs an url pattern prefixed with ^gci/.

  Args: see django.conf.urls.defaults.url
  """
  return django_url('^gci/%s' % regex, view, kwargs=kwargs, name=name)


TASK = url_patterns.namedIdBasedPattern(['sponsor', 'program'])
