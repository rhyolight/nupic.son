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

"""Mapreduce to insert dummy data for GCI student data for safe-harboring."""

from google.appengine.ext import blobstore
from google.appengine.ext import db

from mapreduce import context
from mapreduce import operation

from soc.modules.gci.logic import profile as profile_logic


def process(student_info):
  ctx = context.get()
  params = ctx.mapreduce_spec.mapper.params

  program_key_str = params['program_key']

  program_key = db.Key.from_path('GCIProgram', program_key_str)

  # We can skip the student info entity not belonging to the given program.
  if student_info.program.key() != program_key:
    return

  entities, blobs = profile_logic.insertDummyData(student_info)
  blobstore.delete(filter(bool, blobs))

  for entity in entities:
    yield operation.db.Put(entity)
  yield operation.counters.Increment("profile dummy data inserted")
