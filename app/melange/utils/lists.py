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

"""Module containing list utilities."""

import datetime
import pickle

from google.appengine.datastore import datastore_query
from google.appengine.ext import ndb
from google.appengine.ext import db

from melange import key_column_id_const

from soc.mapreduce import cache_list_items
from soc.modules.gsoc.models import project as project_model
from soc.views.helper import url as url_helper

from melange.logic import cached_list

# These imports are needed for the toListItemDict function, to avoid
# 'KindError' by func(entity) if func access a db.ReferenceProperty of the
# entity.
# pylint: disable=unused-import
from soc.modules.gsoc.models.program import GSoCProgram
from soc.modules.gsoc.models.timeline import GSoCTimeline
# pylint: enable=unused-import

# string that is used as the next_key parameter in the final batch.
FINAL_BATCH = 'done'


class List(object):
  """Represents a list."""

  def __init__(self, list_id, index, model_class, columns, datastore_reader,
               cache_reader=None, valid_period=datetime.timedelta(1)):
    """Initialize a list object.

    Args:
      list_id: A unique id for the list.
      index: Index of the list in the page it is displayed.
      model_class: Model class of the entities used to create list items.
      columns: A list of Column objects describing columns in the list.
      datastore_reader: A ListReader to read data from the datastore.
      cache_reader: A ListReader to read list data from the cache.
      valid_period: datetime.timedelta value indicating the time period a list's
       cache data should be valid, after a caching process completes.
    """
    self._list_id = list_id
    self._index = index
    self.model_class = model_class
    self.columns = columns
    self._cache_reader = cache_reader
    self._datastore_reader = datastore_reader
    self.valid_period = valid_period

  def getListData(self, query, start=None, limit=50):
    """Get a set of list items of this list.

    Args:
      query: Query that can be used to fetch items for this list. Entities
        related to all the list items in this list, satisfy filters in this
        query.
      start: The key of the object that should be the first in the list.
      limit: Number of the elements that should be returned.

    Returns: A ListData entity with data regarding the query.
    """
    if self._cache_reader:
      list_data = self._cache_reader.getListData(
          self._list_id, query, start, limit)
      if not list_data:
        # A cache miss. Fetch data using the datastore reader.
        list_data = self._datastore_reader.getListData(
            self._list_id, query, start, limit)
    else:
      list_data = self._datastore_reader.getListData(
          self._list_id, query, start, limit)

    return list_data


class ListData(object):
  """A response from list data readers."""

  def __init__(self, data, next_key):
    """Initializes a ListData object

    Args:
      data: A list of dicts each representing a list item.
      next_key: A key to the entity that should be fetched firstly in the next
        batch.
    """
    self.data = data
    self.next_key = next_key


class ListDataReader(object):
  """Base class for list data readers."""

  def getListData(self, list_id, query, start, limit):
    """Get list items for a list.

    Implementing subclasses must override this method.

    Args:
      list_id: The id of the list this reader reads data for.
      query: Query that will be used to fetch datastore entities relevant to the
        list.
      start: The key of the object that should be the first in the list.
      limit: Number of the elements that should be returned.

    Returns:
      A ListData entity with data regarding the query. None if the list items
      cannot be read.
    """
    raise NotImplementedError


class CacheReader(ListDataReader):
  """List reader for reading list data from cache."""

  def getListData(self, list_id, query, start=None, limit=50):
    """See ListDataReader.getListData for specification."""
    data_id = getDataId(query)
    if cached_list.isCachedListExists(data_id):
      if cached_list.isValid(data_id):
        return ListData(cached_list.getCachedItems(data_id), FINAL_BATCH)
      else:
        if not cached_list.isProcessing(data_id):
          self._start_caching(list_id, data_id, query)

        # return None because cache is not hit
        return None

    else:
      self._start_caching(list_id, data_id, query)

      # return None because cache is not hit
      return None

  def _start_caching(self, list_id, data_id, query):
    def prepareCachingTransaction():
      if cached_list.isCachedListExists(data_id):
        if cached_list.isProcessing(data_id):
          return False
        else:
          cached_list.setProcessing(data_id)
          return True
      else:
        cached_list.createEmptyProcessingList(data_id)
        return True

    if not ndb.transaction(prepareCachingTransaction):
      return

    entity_kind = '%s.%s' % \
        (query._model_class.__module__, query._model_class.__name__)
    query_pickle = pickle.dumps(query)

    cache_list_pipline = cache_list_items.CacheListsPipeline(
        list_id, entity_kind, query_pickle)

    cache_list_pipline.start()


class DatastoreReaderForDB(ListDataReader):
  """List reader for reading list data from datastore using db queries."""

  def getListData(self, list_id, query, start=None, limit=50):
    """See ListDataReader.getListData for specification."""
    if start:
      query.filter('__key__ >=', db.Key(start))

    entities = query.fetch(limit + 1)

    if len(entities) == limit + 1:
      next_key = str(entities[-1].key())
    else:
      next_key = FINAL_BATCH

    col_funcs = [(c.col_id, c.getValue) for c in getList(list_id).columns]
    items = [toListItemDict(entity, col_funcs) for entity in entities]
    return ListData(items[:limit], next_key)


class DatastoreReaderForNDB(ListDataReader):
  """List reader for reading list data from datastore using ndb queries."""

  def getListData(self, list_id, query, start=None, limit=50):
    """See ListDataReader.getListData for specification."""
    start_cursor = datastore_query.Cursor(urlsafe=start)
    entities, next_cursor, more = query.fetch_page(
        limit, start_cursor=start_cursor)

    next_cursor = next_cursor.urlsafe() if more else FINAL_BATCH

    col_funcs = [(c.col_id, c.getValue) for c in getList(list_id).columns]
    items = [toListItemDict(entity, col_funcs) for entity in entities]
    return ListData(items[:limit], next_cursor)


class JqgridResponse(object):
  """Provide methods to prepare list data to be sent to a jqgrid list."""

  def __init__(self, list_id, buttons=None, row=None):
    """Initializes a JQGridResponse object.

    Args:
      list_id: A list_id to a List instance which defines the model of the list
        and is used to get list data.
      buttons: A list of Button objects defining the buttons in the list.
      row: A Row object defining the row behavior of the list.
    """
    self._list = getList(list_id)
    self._buttons = buttons
    self._custom_buttons = None

    if buttons:
      self._custom_buttons = filter(
          lambda(e): isinstance(e, RedirectCustomButton), buttons)

    self._row = row

  def getOperations(self):
    """Get 'operations' section of the json object expected by jqgrid.

    Specification of the json object can be found at
    http://code.google.com/p/soc/wiki/Lists.

    Returns: A dict containing the list operations.
    """
    operations = {}
    if self.buttons:
      operations['buttons'] = [
          button.getOperations() for button in self.buttons]
    if self.row:
      operations['row'] = self.row.getOperations()
    return operations

  def getData(self, query, start=None, limit=50):
    """Get 'data' section of the json object expected by jqgrid.

    Specification of the json object can be found at
    http://code.google.com/p/soc/wiki/Lists.

    Returns: A dict containing the list data.
    """
    list_data = self._list.getListData(query)

    items = []

    for data in list_data.data:
      item = {}
      item['columns'] = data
      item['operations'] = {}

      custom_button_operations = self._getCustomButtonOperations(item)
      if custom_button_operations:
        item['operations']['buttons'] = self._getCustomButtonOperations(item)

      custom_row_operations = self._getCustomRowOperations(item)
      if custom_row_operations:
        item['operations']['row'] = self._getCustomRowOperations(item)

      items.append(item)

    if not start:
      start = ''

    return {'data': {start: items}, 'next': list_data.next_key}

  def _getCustomButtonOperations(self, item):
    """Get custom parameters regarding operation of buttons in this list.

    Some buttons on a list could behave differently for different rows. This
    method identifies parameters which define those behaviors.

    Args:
      item: A dict representing a particular list item.

    Returns:
      A dict containing button ids as keys and another dict containing each
      button's custom parameters as the value of each key. None if the list does
      not contain custom buttons.
    """
    if self._custom_buttons:
      operations = {}

      for button in self._custom_buttons:
        operations[button.button_id] = button.getCustomParameters(item)

      return operations

  def _getCustomRowOperations(self, item):
    """Get custom parameters regarding row operations in this list.

    If each row in the list behaves differently, this method identifies
    parameters regarding those behaviors.

    Args:
      item: A dict representing a particular list item.

    Returns:
      A dict containing custom parameters of a row. None if the list does not
      define custom row operations.
    """
    if self._row:
      return self._row.getCustomParameters(item)

def getDataId(query):
  """Get a unique 'data id' for a cached list related to a query.

  This id is used to identify data in a list. Two lists with the same data
  should have the same 'data id'.

  Args:
    query: A query used to create a list.

  Returns:
    A string containing an id that is unique for the given query.
  """
  if isinstance(query, ndb.Query):
    return repr(query)
  elif isinstance(query, db.Query):
    return 'kind=%s filters=%r' % (
        query._model_class.__name__, query._get_query())


class Column(object):
  """Base class for a column in a list.

  Args:
    col_id: A unique identifier of this column.
    name: The header of the column that is shown to the user.
    width: The width of the column.
    resizable: Whether the width of the column should be resizable by the
      end user.
    hidden: Whether the column should be hidden by default.
    searchhidden: Whether this column should be searchable when hidden.
  """
  def __init__(self, col_id, name, width=None, resizable=True, hidden=False,
               searchhidden=True, options=None):
    self.col_id = col_id
    self.name = name
    self.width = width
    self.resizable = resizable
    self.hidden = hidden
    self.searchhidden = hidden
    self.options = options

  def getValue(self, entity):
    """This method is called when rendering the column for a single entity.

    This must be overridden by implementing subclasses.

    Args:
      entity: The entity from which data for this column is taken from.

    Returns:
      A rendered value for the column.
    """
    raise NotImplementedError


class Row(object):
  """Base class for a row in a list."""

  def __init__(self, row_type):
    """Initializes a Row object.

    Args:
      row_type: A string indicating the type of the row. Currently
        'redirect_custom' is the only supported type.
    """
    self.row_type = row_type

  def getOperations(self):
    """Returns the operations regarding this row.

    This method can be used to create the 'operations/row' sub object of the
    json object expected by jqgrid. Specification of the json object can be found at
    http://code.google.com/p/soc/wiki/Lists.

    Returns:
      A dict containing data for operations/row/parameters sub object.
    """
    return {
        'type': self.row_type,
        'parameters': self._getParameters()
    }

  def _getParameters(self):
    """Get 'parameters' sub section of the json object expected by jqgrid.

    Specification of the json object can be found at
    http://code.google.com/p/soc/wiki/Lists. This method creates data for
    operations/row/parameters sub object.

    This must be overridden by implementing subclasses.

    Returns:
      A dict containing parameters that can be used in operations/row sub
      object.
    """
    raise NotImplementedError


class Button(object):
  """Base class for a button inside a list."""

  def __init__(self, button_id, caption, bounds, button_type):
    """Initializes a Button object.

    See 'Operations' section of http://code.google.com/p/soc/wiki/Lists
    for more information about args.

    Args:
      button_id: A string indicating a unique id for this button.
      caption: A string defining what caption the button should show.
      bounds: A sequence of size two with two integers or an integer and the
        string 'all'. This indicates how many rows need to be selected for the
        button to be enabled.
      button_type: A string indicating the type of the button. Supported types
        are 'redirect_simple', 'redirect_custom' and 'post'.
    """
    self.button_id = button_id
    self.caption = caption
    self.bounds = bounds
    self.button_type = button_type

  def _getParameters(self):
    """Get 'parameters' for 'operations' of the json object expected by jqgrid.

    This must be overridden by implementing subclasses.

    Specification of the json object can be found at
    http://code.google.com/p/soc/wiki/Lists. This method creates data for
    parameters sub object of a button in operations/buttons json array.

    Returns: A dict with data for parameters sub object of a button object in
      operations/buttons json array.
    """
    raise NotImplementedError

  def getOperations(self):
    """Returns the operations regarding this row.

    This method can be used to create the 'operations/row' sub object of the
    json object expected by jqgrid. Specification of the json object can be
    found at http://code.google.com/p/soc/wiki/Lists.

    Returns: A dict with data for operations/row sub object expected by jqgrid.
    """
    return {
        'bounds': self.bounds,
        'id': self.button_id,
        'caption': self.caption,
        'type': self.button_type,
        'parameters': self._getParameters()
    }


class RedirectCustomRow(Row):
  """Represents a row which redirects user to a custom page when clicked.

  The link that will be used to redirection is custom to each row.
  """

  def __init__(self, new_window=None):
    """Initializes a RedirectCustomRow object.

    Args:
      new_window: If specified to True, the redirected page should be
        loaded in a new window.
    """
    super(RedirectCustomRow, self).__init__('redirect_custom')
    self.new_window = bool(new_window)

  def _getParameters(self):
    """See Row._getParameters for specification"""
    return {'new_window': self.new_window}

  def getCustomParameters(self, item):
    """Returns parameters custom to this row.

    This method can be used to create the 'operations' sub object regarding this
    row in the 'data/row' sub object of the json object expected by jqgrid.
    Specification of the json object can be found at
    http://code.google.com/p/soc/wiki/Lists.

    Args:
      item: A dict representing a particular list item.

    Returns:
     A dict with data for 'operations' sub object regarding this row in the
     'data/row' sub object expected by jqgrid.
    """
    return {'link': self.getLink(item)}

  def getLink(self, item):
    """Returns the link to which user will be redirected when row is clicked.

    This must be overridden by implementing subclasses.

    Args:
      item: A dict representing a particular list item.

    Returns:
      A string indicating the link to which user will be redirected when row is
      clicked.
    """
    raise NotImplementedError


class RedirectSimpleButton(Button):
  """Represents a button which redirects user when clicked.

  The link that will be used to redirection is custom to each row.
  """

  def __init__(self, button_id, caption, bounds, link, new_window):
    """Initializes a RedirectSimpleButton object.

    Args:
      link: The link to which the user will be redirected.
      new_window: A bool indicating whether the redirected page should be
        loaded in a new window, when the button is clicked.
    """
    super(RedirectSimpleButton, self).__init__(
        button_id, caption, bounds, 'redirect_simple')
    self.new_window = new_window
    self.link = link

  def _getParameters(self):
    """See Button._getParameters for specification"""
    return {
        'link': self.link,
        'new_window': self.new_window
    }


class RedirectCustomButton(Button):
  """Represents a button which redirects user to a custom page when clicked.

  The link that will be used to redirection is custom to each row.
  """

  def __init__(self, button_id, caption, bounds, new_window):
    """Initializes a RedirectCustomButton object.

    Args:
      new_window: A bool indicating whether the redirected page should be
        loaded in a new window, when the button is clicked.
    """
    super(RedirectCustomButton, self).__init__(
        button_id, caption, bounds, 'redirect_custom')
    self.new_window = new_window

  def _getParameters(self):
    """See Button._getParameters for specification"""
    return {'new_window': self.new_window}

  def getCustomParameters(self, item):
    """Returns parameters custom to this button.

    This method can be used to create the 'operations' sub object regarding this
    row in the 'data/buttons' sub object of the json object expected by jqgrid.
    Specification of the json object can be found at
    http://code.google.com/p/soc/wiki/Lists.

    Args:
      item: A dict representing a particular list item.

    Returns:
      A dict with data for 'operations' sub object regarding this button in the
      'data/buttons' sub object expected by jqgrid.
    """
    return {
        'link': self.getLink(item),
        'caption': self.getCaption(item)
    }

  def getLink(self, item):
    """Returns the link to which user will be redirected when row is clicked.

    This must be overridden by implementing subclasses.

    Args:
      item: A dict representing a particular list item.

    Returns:
      A string indicating the link to which user will be redirected when this
      button is clicked.
    """
    raise NotImplementedError

  def getCaption(self, item):
    """Returns what caption the button should show.

    This must be overridden by implementing subclasses.

    Args:
      item: A dict representing a particular list item.

    Returns:
      A string indicating the caption the button should show.
    """
    raise NotImplementedError


class PostButton(Button):
  """A button which sends data to the back end when clicked.

  The link that will be used to redirection is custom to each row.
  """

  def __init__(self, button_id, caption, bounds, url, keys, refresh="current",
               redirect=False):
    """Initializes a PostButton object.

    Args:
      url: A string indicating the url to which the button should post data.
      keys: A list of col_ids of the Columns in the list this button belongs to.
        Those columns' content will be send to the server when the button is
        clicked.
      refresh: Indicates which list to refresh, is the current list by default.
        The keyword 'all' can be used to refresh all lists on the page or an
        integer index referring to the index of the list to refresh can be
        given.
      redirect: A bool indicating whether the user will be redirected to a URL
        returned by the server.
    """
    super(PostButton, self).__init__(
        button_id, caption, bounds, 'post')
    self.url = url
    self.keys = keys
    self.refresh = refresh
    self.redirect = redirect

  def _getParameters(self):
    """See Button._getParameters for specification"""
    return {
      'url': self.url,
      'keys': self.keys,
      'refresh': self.refresh,
      'redirect': self.redirect
    }


def toListItemDict(entity, column_def):
  """Create a list item from a datastore entity.

  Args:
    entity: The datastore entity regarding a list item.
    column_def: A list of tuples. Each has a column name of the list, and the
      lambda functions that create the value for that column for a list item.
      These functions should take one parameter, the entity relevant to one list
      item.

  Returns:
    A dictionary describing a list item.
  """
  output = {}
  for col, func in column_def:
    output[col] = func(entity)
  return output


def getList(list_id):
  """Get the list instance relevant to a list id.

  Args:
    list_id: Unique id of the list.

  Returns:
    A List object with the given id.
  """
  return LISTS[list_id]


# A list of list ids
GSOC_PROJECTS_LIST_ID = 'gsoc_projects'

ORGANIZATION_LIST_ID = 'organizations'


# Organization list
from summerofcode.models import organization as org_model

# GSoCProjects list
from soc.modules.gsoc.models import project


class SimpleColumn(Column):
  """Column object to display a simple attribute.

  When simply a value of an attribute of the entity is needed to be displayed
  in a column this class is used. The column id must be the same as the
  relevant attribute name.
  """
  def getValue(self, entity):
    return getattr(entity, self.col_id)


class KeyColumn(Column):
  """Column object to represent the unique key of the project."""
  def getValue(self, entity):
    """See Column.getValue for specification"""
    return '%s/%s' % (entity.parent_key().name(), entity.key().id())


class EncodedKeyColumn(Column):
  """Column object to represent the unique key as encoded key of the entity."""
  def getValue(self, entity):
    """See Column.getValue for specification."""
    return str(entity.key())


class StudentColumn(Column):
  """Column object to represent the student"""
  def getValue(self, entity):
    """See Column.getValue for specification"""
    return entity.parent_key().name()


class OrganizationColumn(Column):
  """Column object to represent the organization"""
  def getValue(self, entity):
    """See Column.getValue for specification"""
    # TODO(daniel): this hack will not be needed, when project model is
    # converted to NDB
    org_key = project_model.GSoCProject.org.get_value_for_datastore(entity)
    return ndb.Key.from_old_key(org_key).get().name


class TagsColumn(Column):
  """Column class to represent tags for organization."""

  def getValue(self, entity):
    """See Column.getValue for specification."""
    return ', '.join(entity.tags)


class IdeasColumn(Column):
  """Column class to represent URL to list of ideas for organization."""

  def getValue(self, entity):
    """See Column.getValue for specification."""
    return url_helper.urlize(entity.ideas_page, name='Ideas page')


key = EncodedKeyColumn(key_column_id_const.KEY_COLUMN_ID, 'Key', hidden=True)
student = StudentColumn('student', 'Student')
title = SimpleColumn('title', 'Title')
org = OrganizationColumn('org', 'Organization')
status = SimpleColumn('status', 'Status')

cache_reader = CacheReader()
datastore_reader = DatastoreReaderForDB()
# CachedList should be updated once a day
valid_period = datetime.timedelta(0, 60)

GSOC_PROJECTS_LIST = List(GSOC_PROJECTS_LIST_ID, 0, project.GSoCProject,
                          [key, student, title, org, status], datastore_reader,
                          cache_reader=cache_reader, valid_period=valid_period)

# TODO(daniel): move this part to a separate module
# TODO(daniel): replace this column with one that is more versatile
class NdbKeyColumn(Column):
  """Column object to represent the unique key of the entity."""

  def getValue(self, entity):
    """See Column.getValue for specification"""
    return entity.key.id()

key = NdbKeyColumn(key_column_id_const.KEY_COLUMN_ID, 'Key', hidden=True)
name = SimpleColumn('name', 'Name')
tags = TagsColumn('tags', 'Tags')
ideas = IdeasColumn('ideas', 'Ideas')

ORGANIZATION_LIST = List(
    ORGANIZATION_LIST_ID, 0, org_model.SOCOrganization,
    [key, name, tags, ideas], datastore_reader)

LISTS = {
    GSOC_PROJECTS_LIST_ID: GSOC_PROJECTS_LIST,
    ORGANIZATION_LIST_ID: ORGANIZATION_LIST,
    }
