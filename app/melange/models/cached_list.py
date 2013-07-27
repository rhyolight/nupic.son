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

"""Contains the model of a cached list."""

from google.appengine.ext import ndb


class CachedList(ndb.Model):
  """The CachedList model, represents a list cached as a ndb entity."""

  # The list of items cached in the list in json format
  list_data = ndb.JsonProperty(repeated=True)

  # Whether datastore entities relevant to the list have changed.
  # If False, the cached list object contains stale data.
  valid = ndb.BooleanProperty()

  # A mapereduce pipeline id.
  # If not None a process is running collecting/adding data for this list.
  cache_process_id = ndb.StringProperty()
