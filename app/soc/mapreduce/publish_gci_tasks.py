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

"""Surveys model updating MapReduce."""

from mapreduce import context
from mapreduce import operation

from soc.modules.gci.models import task as task_model
from soc.modules.gci.models.program import GCIProgram


def process(task):
  ctx = context.get()
  params = ctx.mapreduce_spec.mapper.params
  program_key = params['program_key']

  program = GCIProgram.get_by_key_name(program_key)

  if (task.program.key() == program.key() and
      (task.status == task_model.UNAPPROVED or task.status == 'Unpublished')):
    task.status = 'Open'
    yield operation.db.Put(task)

    yield operation.counters.Increment("task_updated")

  yield operation.counters.Increment("task_not_updated")
