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

"""GSoCProfile updating MapReduce."""

import logging

from google.appengine.ext import db
from mapreduce import operation


def process(profile_key):
  def convert_profile_txn():
    profile = db.get(profile_key)
    if not profile:
      logging.error('Missing profile for key %s.' % profile_key)
      return False
    
    profile.program = profile.scope
    profile.put()
    return True

  result = db.run_in_transaction(convert_profile_txn)

  if result:
    yield operation.counters.Increment('updated_profile')
  else:
    yield operation.counters.Increment('missing_profile')
