#!/usr/bin/env python
#
# Copyright 2009 the Melange authors.
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

"""This module supplies an interactive shell with remote api configured.

Usage is simple:

App Engine interactive console
>>> from soc.models.user import User
>>> gen = lambda: User.all()
>>> it = deepFetch(gen)
>>> result = [i for i in it]
"""


import code
import getpass
import os
import sys

def auth_func():
  """Returns a tuple with username and password.
  """

  if os.path.exists('.appengine_auth'):
    try:
      f = open('.appengine_auth')
      name = f.readline()
      pwd = f.readline()
      # nip off the newlines
      return name[:-1], pwd[:-1]
    finally:
      f.close()
    print "Could not read auth from .appengine_auth"

  return raw_input('Username:'), getpass.getpass('Password:')


def deepFetch(queryGen, key=None, filters=None, batchSize = 100):
  """Iterator that yields an entity in batches.

  Args:
    queryGen: should return a Query object
    key: used to .filter() for __key__
    filters: dict with additional filters
    batchSize: how many entities to retrieve in one datastore call

  Retrieved from http://tinyurl.com/d887ll (AppEngine cookbook).
  """

  from google.appengine.ext import db

   # AppEngine will not fetch more than 1000 results
  batchSize = min(batchSize, 1000)

  query = None
  done = False
  count = 0

  if key:
    key = db.Key(key)

  while not done:
    print count
    query = queryGen()

    if filters:
      for filter_key, value in filters.items():
        query.filter(filter_key, value)

    if key:
      query.filter("__key__ > ", key)

    results = query.fetch(batchSize)
    for result in results:
      count += 1
      yield result
    if batchSize > len(results):
      done = True
    else:
      key = results[-1].key()


def setupRemote(app_id, host=None):
  """Sets up execution for the specified remote.
  """
  from google.appengine.api import apiproxy_stub_map
  from google.appengine.ext import db
  from google.appengine.ext.remote_api import remote_api_stub

  if not host:
    host = '%s.appspot.com' % app_id.split("~")[-1]

  remote_api_stub.ConfigureRemoteDatastore(app_id, '/_ah/remote_api', auth_func, host)
  remote_api_stub.MaybeInvokeAuthentication()


def remote(args, context=None):
  """Starts a shell with the datastore as remote_api_stub.

  Args:
    args: arguments from the user
    context: locals that should be added to the shell
  """

  if not context:
    context = {}

  app_id = args[0]

  host = args[1] if len(args) > 1 else None

  setupRemote(app_id, host)

  context['deepFetch'] = deepFetch

  try:
    from IPython.frontend.terminal.embed import TerminalInteractiveShell
    shell = TerminalInteractiveShell(user_ns=context)
    shell.mainloop()
  except ImportError:
    # IPython < 0.11
    # Explicitly pass an empty list as arguments, because otherwise
    # IPython would use sys.argv from this script.
    try:
      from IPython.Shell import IPShell
      shell = IPShell(argv=[], user_ns=context)
      shell.mainloop()
    except ImportError:
      # IPython not found, use the vanilla interpreter shell
      code.interact('App Engine interactive console for %s' % (app_id,), None, context)

def setup():
  """Sets up the sys.path and environment for development."""

  here = os.path.abspath(__file__)
  here = os.path.join(os.path.dirname(here), '..')
  here = os.path.normpath(here)

  appengine_location = os.path.join(here, 'thirdparty', 'google_appengine')

  extra_paths = [here,
                 os.path.join(appengine_location, 'lib', 'django'),
                 os.path.join(appengine_location, 'lib', 'webob_0_9'),
                 os.path.join(appengine_location, 'lib', 'yaml', 'lib'),
                 os.path.join(appengine_location, 'lib', 'fancy_urllib'),
                 os.path.join(appengine_location, 'lib', 'simplejson'),
                 os.path.join(appengine_location, 'lib', 'protorpc-1.0'),
                 appengine_location,
                 os.path.join(here, 'app'),
                ]

  sys.path = extra_paths + sys.path

  os.environ['SERVER_SOFTWARE'] = 'Development Interactive Shell'


def setDjango():
  """Sets Django version used by the application."""

  # TODO(daniel): this should be removed at some point as Interactive Shell
  # does not use Django. This is currently required, because when main module
  # is loaded, it always imports gae_django module which requires Django
  # version to be set. This should be changed so that it is loaded only
  # for Prod/Dev server.
  os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

  from google.appengine import dist
  dist.use_library('django', '1.2')

def main(args):
  """Convenience wrapper that calls setup and remote."""
  setup()
  setDjango()
  remote(args)

  import main as app_main

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "Usage: %s app_id [host]" % (sys.argv[0],)
    sys.exit(1)

  main(sys.argv[1:])
