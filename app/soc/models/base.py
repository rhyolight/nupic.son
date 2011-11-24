#!/usr/bin/env python2.5
#
# Copyright 2008 the Melange authors.
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

"""Module containing enhanced db.Model classes.

The classes in this module are intended to serve as base classes for all
Melange Datastore Models.
"""


from google.appengine.ext import db

from soc.logic import dicts

class ModelWithFieldAttributes(db.Model):
  """TODO(ljvderijk): Delete this base class.
  """

  toDict = dicts.toDict
