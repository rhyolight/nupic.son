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
# TODO(daniel): this mapper may be removed once the update is done

"""Program model updating MapReduce."""

from mapreduce import operation


def process(program):
  program.program_id = program.link_id
  program.sponsor = program.scope

  yield operation.db.Put(survey)
  yield operation.counters.Increment("program_updated")
