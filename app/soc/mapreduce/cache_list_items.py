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

from mapreduce import context
from mapreduce import base_handler
from mapreduce import mapreduce_pipeline

import json

import pickle


NO_OF_SHARDS = 4


def mapProcess(entity):
  # TODO: (Aruna) Fix this import
  from melange.utils import lists

  ctx = context.get()
  params = ctx.mapreduce_spec.mapper.params

  list_id = params['list_id']
  col_funcs = [(c.name, c.col_func) for c in lists.getList(list_id)._columns]
  query_pickle = params['query_pickle']

  query = pickle.loads(query_pickle)
  data_id = lists.getDataId(query)

  if(query.filter('__key__', entity.key()).get()):
    item = json.dumps(lists.toListItemDict(entity, col_funcs))

    yield (data_id, item)


def reduceProcess(list_id, entities):
  ndb.transaction(
      lambda: cached_list.cacheItems(list_id, map(json.loads, entities)))


class CacheListsPipeline(base_handler.PipelineBase):
  """A pipeline to read datastore entities and cache them for lists.

  Args:
    list_id: A unique id to identify the list.
    entity_kind: Kind of the entity the DatastoreInputReader should read.
    query_pickle: A pickled Query object that is used to filter entities that
      should be cached.
  """

  def run(self, list_id, entity_kind, query_pickle):

    yield mapreduce_pipeline.MapreducePipeline(
      'cache_list_items',
      'soc.mapreduce.cache_list_items.mapProcess',
      'soc.mapreduce.cache_list_items.reduceProcess',
      'mapreduce.input_readers.DatastoreInputReader',
      mapper_params={
          'list_id': list_id,
          'entity_kind': entity_kind,
          'query_pickle': query_pickle
      },
      shards=NO_OF_SHARDS)