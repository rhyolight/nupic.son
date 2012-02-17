#!/usr/bin/python2.5
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


"""Mapreduce that moves inactive entites to active status.
"""


from mapreduce import operation


def process(entity):
  if entity.status == 'inactive':
    entity.status = 'active'
    yield operation.db.Put(entity)

    yield operation.counters.Increment('entity_unfrozen')

  yield operation.counters.Increment('entity_not_unfrozen')
