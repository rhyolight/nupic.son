#!/usr/bin/env python2.5
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


__authors__ = [
  '"Augie Fackler" <durin42@gmail.com>',
  '"Leo (Chong Liu)" <HiddenPython@gmail.com>',
  ]

import sys
import os

HERE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     '..'))
appengine_location = os.path.join(HERE, 'thirdparty', 'google_appengine')
extra_paths = [HERE,
               os.path.join(appengine_location, 'lib', 'django'),
               os.path.join(appengine_location, 'lib', 'webob'),
               os.path.join(appengine_location, 'lib', 'yaml', 'lib'),
               os.path.join(appengine_location, 'lib', 'antlr3'),
               appengine_location,
               os.path.join(HERE, 'app'),
               os.path.join(HERE, 'thirdparty', 'coverage'),
              ]

import nose
from nose import plugins

import logging
log =  logging.getLogger('nose.plugins.cover')


def begin(self):
  """Used to stub out nose.plugins.cover.Coverage.begin. The difference is that
  it loads Melange after coverage starts so the loading of models, logic and
  views can be tracked by coverage.
  """
  log.debug("Coverage begin")
  import coverage
  self.skipModules = sys.modules.keys()[:]
  if self.coverErase:
    log.debug("Clearing previously collected coverage statistics")
    coverage.erase()
  coverage.exclude('#pragma[: ]+[nN][oO] [cC][oO][vV][eE][rR]')
  coverage.start()
  load_melange()


def load_melange():
  """
  Registers a core, and SoC, GSoC and GHOP modules callbacks, sitemap, sidebar
  and rights.
  """
  # Register a core for the test modules to use
  from soc.modules import callback
  from soc.modules.core import Core
  callback.registerCore(Core())
  current_core = callback.getCore()
  # Register SoC and GSoC modules callbacks
  current_core.registerModuleCallbacks()
  # Register GHOP modules callbacks
  from soc.modules.ghop.callback import Callback
  ghop_callback = Callback(current_core)
  ghop_callback.registerWithSitemap()
  ghop_callback.registerWithSidebar()
  ghop_callback.registerRights()
  from soc.modules.soc_core.callback import Callback as soc_core_Callback
  soc_core_callback = soc_core_Callback(current_core)
  soc_core_callback.registerWithSitemap()
  soc_core_callback.registerWithSidebar()
  soc_core_callback.registerRights()
  from soc.modules.gsoc.callback import Callback as gsoc_Callback
  gsoc_callback = gsoc_Callback(current_core)
  gsoc_callback.registerWithSitemap()
  gsoc_callback.registerWithSidebar()
  gsoc_callback.registerRights()


class AppEngineDatastoreClearPlugin(plugins.Plugin):
  """Nose plugin to clear the AppEngine datastore between tests.
  """
  name = 'AppEngineDatastoreClearPlugin'
  enabled = True
  def options(self, parser, env):
    return plugins.Plugin.options(self, parser, env)

  def configure(self, parser, env):
    plugins.Plugin.configure(self, parser, env)
    self.enabled = True

  def afterTest(self, test):
    from google.appengine.api import apiproxy_stub_map
    datastore = apiproxy_stub_map.apiproxy.GetStub('datastore')
    # clear datastore iff one is available
    if datastore is not None:
      datastore.Clear()


def main():
  sys.path = extra_paths + sys.path
  os.environ['SERVER_SOFTWARE'] = 'Development via nose'
  os.environ['SERVER_NAME'] = 'Foo'
  os.environ['SERVER_PORT'] = '8080'
  os.environ['APPLICATION_ID'] = 'test-app-run'
  os.environ['USER_EMAIL'] = 'test@example.com'
  os.environ['CURRENT_VERSION_ID'] = 'testing-version'
  os.environ['HTTP_HOST'] = 'some.testing.host.tld'
  import main as app_main
  from google.appengine.api import apiproxy_stub_map
  from google.appengine.api import datastore_file_stub
  from google.appengine.api import mail_stub
  from google.appengine.api import user_service_stub
  from google.appengine.api import urlfetch_stub
  from google.appengine.api.memcache import memcache_stub
  from google.appengine.api.labs.taskqueue import taskqueue_stub
  apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
  apiproxy_stub_map.apiproxy.RegisterStub('urlfetch',
                                          urlfetch_stub.URLFetchServiceStub())
  apiproxy_stub_map.apiproxy.RegisterStub('user',
                                          user_service_stub.UserServiceStub())
  apiproxy_stub_map.apiproxy.RegisterStub('datastore',
    datastore_file_stub.DatastoreFileStub('test-app-run', None, None))
  apiproxy_stub_map.apiproxy.RegisterStub('memcache',
    memcache_stub.MemcacheServiceStub())
  apiproxy_stub_map.apiproxy.RegisterStub('mail', mail_stub.MailServiceStub())
  yaml_location = os.path.join(HERE, 'app')
  apiproxy_stub_map.apiproxy.RegisterStub('taskqueue',
                 taskqueue_stub.TaskQueueServiceStub(root_path=yaml_location))
  import django.test.utils
  django.test.utils.setup_test_environment()

  plugins = [AppEngineDatastoreClearPlugin()]

  if '--coverage' in sys.argv:
    from nose.plugins import cover
    plugin = cover.Coverage()
    from mox import stubout
    stubout_obj = stubout.StubOutForTesting()
    stubout_obj.SmartSet(plugin, 'begin', begin)
    plugins.append(plugin)

    args = ['--with-coverage',
            '--cover-package=soc.',
            '--cover-erase',
            '--cover-html',
            '--cover-html-dir=coverageResults']

    sys.argv.remove('--coverage')
    sys.argv += args
  else:
    load_melange()

  nose.main(addplugins=plugins)


if __name__ == '__main__':
  main()
