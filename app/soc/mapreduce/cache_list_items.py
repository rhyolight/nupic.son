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

"""Mapreduce to cache datastore entities for lists."""

from google.appengine.ext import ndb

from melange.logic import cached_list
from melange.utils import lists

from mapreduce import context
from mapreduce import base_handler
from mapreduce import mapreduce_pipeline

import json


NO_OF_SHARDS = 4


def mapProcess(entity):
  ctx = context.get()
  params = ctx.mapreduce_spec.mapper.params

  list_id_func = eval(params['list_id_func'])
  column_defs = eval(params['column_defs'])

  item = json.dumps(lists.toListItemDict(entity, column_defs))

  list_id = list_id_func(entity)

  yield (list_id, item)


def reduceProcess(list_id, entities):
  ndb.transaction(
      lambda: cached_list.cacheItems(list_id, map(json.loads, entities)))


class CacheListsPipeline(base_handler.PipelineBase):
  """A pipeline to read datastore entities and cache them for lists.

  Args:
    kind: Kind of the entity the DatastoreInputReader should read.
    list_id_func: A string representation of a lambda function. This function
      should take one parameter, the entity relevant to one list item. It should
      create an id for the list that list item should belong to.
    column_defs: A string representation of a dictionary that has column names
      of the list as keys, and lambda functions that create the value for that
      column for a list item as values. These functions should take one
      parameter, the entity relevant to one list item.
  """

  def run(self, kind, list_id_func, column_defs):
    yield mapreduce_pipeline.MapreducePipeline(
      'cache_list_items',
      'soc.mapreduce.cache_list_items.mapProcess',
      'soc.mapreduce.cache_list_items.reduceProcess',
      'mapreduce.input_readers.DatastoreInputReader',
      mapper_params={
          'entity_kind': kind,
          'list_id_func': list_id_func,
          'column_defs': column_defs
      },
      shards=NO_OF_SHARDS)
