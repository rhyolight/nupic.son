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

import contextlib
import logging
import os
import pickle
import socket
import subprocess
import sys
import time

import easyprocess
from mox import stubout
import nose
from nose import failure
from nose import plugins
import pyvirtualdisplay

# Disable the messy logging information
logging.disable(logging.INFO)
log = logging.getLogger('nose.plugins.cover')

HERE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     '..'))
appengine_location = os.path.join(HERE, 'thirdparty', 'google_appengine')
extra_paths = [HERE,
               os.path.join(appengine_location, 'lib', 'yaml', 'lib'),
               os.path.join(appengine_location, 'lib', 'antlr3'),
               appengine_location,
               os.path.join(HERE, 'app'),
               os.path.join(HERE, 'tests')
              ]


def setup_gae_services():
  """Setups all google app engine services required for testing."""
  from google.appengine.api import apiproxy_stub_map
  from google.appengine.api import mail_stub
  from google.appengine.api import user_service_stub
  from google.appengine.api import urlfetch_stub
  from google.appengine.api.capabilities import capability_stub
  from google.appengine.api.memcache import memcache_stub
  from google.appengine.api.taskqueue import taskqueue_stub
  from google.appengine.api import datastore_file_stub

  apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
  apiproxy_stub_map.apiproxy.RegisterStub(
      'urlfetch', urlfetch_stub.URLFetchServiceStub())
  apiproxy_stub_map.apiproxy.RegisterStub(
      'user', user_service_stub.UserServiceStub())
  apiproxy_stub_map.apiproxy.RegisterStub(
      'memcache', memcache_stub.MemcacheServiceStub())
  apiproxy_stub_map.apiproxy.RegisterStub('datastore',
      datastore_file_stub.DatastoreFileStub('test-app-run', None, None))
  apiproxy_stub_map.apiproxy.RegisterStub('mail', mail_stub.MailServiceStub())
  yaml_location = os.path.join(HERE, 'app')
  apiproxy_stub_map.apiproxy.RegisterStub(
      'taskqueue', taskqueue_stub.TaskQueueServiceStub(root_path=yaml_location))
  apiproxy_stub_map.apiproxy.RegisterStub(
      'capability_service', capability_stub.CapabilityServiceStub())


def clean_datastore():
  from google.appengine.api import apiproxy_stub_map
  from google.appengine.ext import ndb
  datastore = apiproxy_stub_map.apiproxy.GetStub('datastore_v3')
  if datastore is not None:
    datastore.Clear()

  ndb.get_context().clear_cache()


def clear_memcache():
  """Clears all entries that exist in memcache."""
  from google.appengine.api import memcache
  memcache.flush_all()


def begin(self):
  """Used to stub out nose.plugins.cover.Coverage.begin.

  The difference is that it loads Melange after coverage starts, so
  the loading of models, logic and views can be tracked by coverage.
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
  self._orig_begin()


def load_melange():
  """Prepare Melange for usage.

  Registers a core, the GSoC and GCI modules, and calls the sitemap, sidebar
  and rights services.
  """
  from soc.modules import callback
  from soc.modules.core import Core

  # Register a core for the test modules to use
  callback.registerCore(Core())
  current_core = callback.getCore()

  callback_module_names = [
      'codein.callback',
      'melange.callback',
      'soc.modules.soc_core.callback',
      'soc.modules.gsoc.callback',
      'soc.modules.gci.callback',
      'summerofcode.callback'
      ]

  current_core.registerModuleCallbacks(callback_module_names)

  # Make sure all services are called
  current_core.callService('registerViews', True)
  current_core.callService('registerWithSitemap', True)
  current_core.callService('registerWithSidebar', True)
  current_core.callService('registerRights', True)


class AppEngineDatastoreClearPlugin(plugins.Plugin):
  """Nose plugin to clear the AppEngine datastore between tests."""
  name = 'AppEngineDatastoreClearPlugin'
  enabled = True
  def options(self, parser, env):
    return plugins.Plugin.options(self, parser, env)

  def configure(self, parser, env):
    plugins.Plugin.configure(self, parser, env)
    self.enabled = True

  def afterTest(self, test):
    clean_datastore()


class DefaultUserSignInPlugin(plugins.Plugin):
  """Nose plugin to sign in a user with the default Google Account
  between tests.
  """
  name = 'DefaultUserSignInPlugin'
  enabled = True

  def options(self, parser, env):
    return plugins.Plugin.options(self, parser, env)

  def configure(self, parser, env):
    plugins.Plugin.configure(self, parser, env)
    self.enabled = True

  def afterTest(self, test):
    os.environ['USER_EMAIL'] = 'test@example.com'
    os.environ['USER_ID'] = '42'


class AppEngineMemcacheClearPlugin(plugins.Plugin):
  """Nose plugin to clear the AppEngine memecache entries between the tests."""
  name = 'AppEngineMemcacheClearPlugin'
  enabled = True

  def configure(self, parser, env):
    """See plugins.Plugin.configure for specification."""
    super(AppEngineMemcacheClearPlugin, self).configure(parser, env)
    self.enabled = True

  def afterTest(self, test):
    """See plugins.Plugin.afterTest for specification."""
    clear_memcache()


def multiprocess_runner(ix, testQueue, resultQueue, currentaddr, currentstart,
           keyboardCaught, shouldStop, loaderClass, resultClass, config):
  """To replace the test runner of multiprocess.

  * Setup gae services at the beginning of every process
  * Clean datastore after each test
  """
  from nose.pyversion import bytes_
  try:
    from cStringIO import StringIO
  except ImportError:
    import StringIO
  from nose.plugins.multiprocess import _instantiate_plugins, \
    NoSharedFixtureContextSuite, _WritelnDecorator, TestLet
  config = pickle.loads(config)
  dummy_parser = config.parserClass()
  if _instantiate_plugins is not None:
    for pluginclass in _instantiate_plugins:
      plugin = pluginclass()
      plugin.addOptions(dummy_parser,{})
      config.plugins.addPlugin(plugin)
  config.plugins.configure(config.options,config)
  config.plugins.begin()
  log.debug("Worker %s executing, pid=%d", ix,os.getpid())
  loader = loaderClass(config=config)
  loader.suiteClass.suiteClass = NoSharedFixtureContextSuite

  def get():
    return testQueue.get(timeout=config.multiprocess_timeout)

  def makeResult():
    stream = _WritelnDecorator(StringIO())
    result = resultClass(stream, descriptions=1,
               verbosity=config.verbosity,
               config=config)
    plug_result = config.plugins.prepareTestResult(result)
    return plug_result if plug_result else result

  def batch(result):
    failures = [(TestLet(c), err) for c, err in result.failures]
    errors = [(TestLet(c), err) for c, err in result.errors]
    errorClasses = {}
    for key, (storage, label, isfail) in result.errorClasses.items():
      errorClasses[key] = ([(TestLet(c), err) for c, err in storage],
                 label, isfail)
    return (
      result.stream.getvalue(),
      result.testsRun,
      failures,
      errors,
      errorClasses)

  def setup_process_env():
    """Runs just after the process starts to setup services."""
    setup_gae_services()

  def after_each_test():
    """Runs after each test to clean datastore."""
    clean_datastore()

  # Setup gae services at the beginning of every process
  setup_process_env()
  for test_addr, arg in iter(get, 'STOP'):
    if shouldStop.is_set():
      log.exception('Worker %d STOPPED',ix)
      break
    result = makeResult()
    test = loader.loadTestsFromNames([test_addr])
    test.testQueue = testQueue
    test.tasks = []
    test.arg = arg
    log.debug("Worker %s Test is %s (%s)", ix, test_addr, test)
    try:
      if arg is not None:
        test_addr = test_addr + str(arg)
      currentaddr.value = bytes_(test_addr)
      currentstart.value = time.time()
      test(result)
      currentaddr.value = bytes_('')
      resultQueue.put((ix, test_addr, test.tasks, batch(result)))
      # Clean datastore after each test
      after_each_test()
    except KeyboardInterrupt:
      keyboardCaught.set()
      if len(currentaddr.value) > 0:
        log.exception('Worker %s keyboard interrupt, failing '
                'current test %s',ix,test_addr)
        currentaddr.value = bytes_('')
        failure.Failure(*sys.exc_info())(result)
        resultQueue.put((ix, test_addr, test.tasks, batch(result)))
      else:
        log.debug('Worker %s test %s timed out',ix,test_addr)
        resultQueue.put((ix, test_addr, test.tasks, batch(result)))
    except SystemExit:
      currentaddr.value = bytes_('')
      log.exception('Worker %s system exit',ix)
      raise
    except:
      currentaddr.value = bytes_('')
      log.exception("Worker %s error running test or returning "
                    "results",ix)
      failure.Failure(*sys.exc_info())(result)
      resultQueue.put((ix, test_addr, test.tasks, batch(result)))
    if config.multiprocess_restartworker:
      break
  log.debug("Worker %s ending", ix)


def checkCanSplit(context, fixt):
  """Override the default multiprocess test runner behaviour.

  Not checking and running each test case independently by default if
  _multiprocess_can_split_ is True or _multiprocess_shared_ is False or unset.
  This is used by the multiprocess plugin of nose. Its default behaviour is to
  run a class/suite of test cases together and run its fixtures
  (setUp/tearDown) only once.

  Args:
    - context: test context
    - fixt: data fixture

  Returns: bool, if should check tests splittable
  """
  if hasattr(context, '_multiprocess_can_split_') and \
      not getattr(context, '_multiprocess_can_split_'):
    return True
  if getattr(context, '_multiprocess_shared_', False):
    return True
  return False


def run_pyunit_tests():
  sys.path = extra_paths + sys.path
  os.environ['SERVER_SOFTWARE'] = 'Development via nose'
  os.environ['SERVER_NAME'] = 'Foo'
  os.environ['SERVER_PORT'] = '8080'
  os.environ['APPLICATION_ID'] = 'test-app-run'
  os.environ['USER_EMAIL'] = 'test@example.com'
  os.environ['USER_ID'] = '42'
  os.environ['CURRENT_VERSION_ID'] = 'testing-version'
  os.environ['HTTP_HOST'] = 'some.testing.host.tld'
  os.environ['APPENGINE_RUNTIME'] = 'python27'
  setup_gae_services()

  # settings cannot be imported at module level, as it requires all
  # environmental variables to be already set
  import settings
  settings.MIDDLEWARE_CLASSES = list(settings.MIDDLEWARE_CLASSES) + [
      'test_utils.FakeBlobstoreMiddleware']

  import main as app_main
  import django.test.utils
  django.test.utils.setup_test_environment()

  plugins = [
      AppEngineDatastoreClearPlugin(),
      AppEngineMemcacheClearPlugin(),
      DefaultUserSignInPlugin()
      ]

  # For coverage
  if '--coverage' in sys.argv:
    from nose.plugins import cover
    plugin = cover.Coverage()
    plugin._orig_begin = plugin.begin
    stubout_obj = stubout.StubOutForTesting()
    stubout_obj.SmartSet(plugin, 'begin', begin)
    plugins.append(plugin)

    args = ['--with-coverage',
            '--cover-package=soc.,melange.,summerofcode.,codein.',
            '--cover-erase',
            '--cover-html',
            '--cover-html-dir=reports/py_coverage']

    sys.argv.remove('--coverage')
    sys.argv += args
  else:
    load_melange()

  # For multiprocess
  will_multiprocess = False
  for arg in sys.argv[1:]:
    if '--processes' in arg:
      will_multiprocess = True
      break
  if will_multiprocess:
    from nose.plugins import multiprocess
    stubout_obj = stubout.StubOutForTesting()
    stubout_obj.SmartSet(multiprocess, '__runner', multiprocess_runner)
    stubout_obj.SmartSet(multiprocess.MultiProcessTestRunner,
        'checkCanSplit', staticmethod(checkCanSplit))
    # The default --process-timeout (10s) is too short
    sys.argv += ['--process-timeout=300']

  # Ignore functional and old_app tests
  args = ['--exclude=functional',
          '--exclude=^old_app$']
  sys.argv += args
  nose.run(addplugins=plugins)


def get_js_tests_environment():
  """Create appropriate environment variables for JS tests.

  Returns:
    A mapping derived from os.environ containing additional appropriate paths to
    run the JS tests successfully. Specifically, it adds paths for node and
    phantomjs.
  """
  js_tests_environment = os.environ.copy()
  js_tests_environment['PATH'] += ':./node_modules/phantomjs/bin:./bin'

  return js_tests_environment


def get_random_available_port():
  """Get an available port from the operating system.

    The port is retrieved from the operating system and the connection is closed
    right after the retrieval. Client functions should use the port as soon as
    possible, because there's no guarantee that another process would not get
    the same port in the meantime.

  Returns:
    A random available port from the operating system.
  """
  with contextlib.closing(
      socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
    sock.bind(('', 0))
    sock.listen(1)
    return str(sock.getsockname()[1])


def run_js_tests(run_browsers_gui):
  """Run JS tests suite.

    If run_browsers_gui is True, then run all JS tests in all browsers found in
    the system, showing their UI during the tests.
    If run_browsers_gui is False, then:
    a) if Xvfb is present in the system, JS tests for all browsers in the system
       are run in the virtual buffer, so no browser GUI is shown.
    b) If Xvfb is not available, then JS tests are run headlessly only in
       PhantomJS.

  Args:
    run_browsers_gui: Boolean to specify whether or not to run all JS tests in
      all browsers available in the system showing their UI.
  """
  # TODO(mario): this is necessary since testem doesn't have any facility to run
  # its server from a random port for CI. If multiple users are running tests in
  # the same machine at the same time it crashes.
  # This can be removed once https://github.com/airportyh/testem/issues/283 is
  # fixed.
  port = get_random_available_port()

  if run_browsers_gui:
    subprocess.call(
        'node ./node_modules/testem/testem.js -p %s ci' % port,
        env=get_js_tests_environment(), shell=True)
    return

  try:
    # start() assigns the DISPLAY environment variable to the virtual display.
    virtual_display = pyvirtualdisplay.Display().start()
  except easyprocess.EasyProcessCheckInstalledError:
    virtual_display = None

  if virtual_display:
    subprocess.call(
        'node ./node_modules/testem/testem.js -p %s ci' % port,
        env=get_js_tests_environment(), shell=True)
    virtual_display.stop()
  else:
    print ('WARNING: You don\'t have Xvfb installed. This is required in order'
           ' to run tests in browsers headlessly')
    print ('You can either install xvfb ("sudo apt-get install xvfb" in Ubuntu)'
           ' or run tests with --browsers-gui switch')
    subprocess.call(
        'node ./node_modules/testem/testem.js -l phantomjs -p %s ci' % port,
        env=get_js_tests_environment(), shell=True)


def run_pylint():
  """Runs PyLint."""
  subprocess.call('bin/paver pylint', shell=True)


def run_js_dev():
  subprocess.call(
    'node ./node_modules/testem/testem.js -l phantomjs -g',
    env=get_js_tests_environment(), shell=True)


# TODO(nathaniel): Deduplicate the code that is shared with js tests.
def run_functional_tests(run_browsers_gui):
  """Run Functional Tests.

  Args:
    run_browsers_gui: Boolean to specify whether or not to run all functional tests in
      the browser UI.
  """
  os.environ['SERVER_SOFTWARE'] = 'Development'
  os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
  if run_browsers_gui:
    argv = ['-W', 'tests/functional/']
    nose.run(argv=argv)
    return

  try:
    # start() assigns the DISPLAY environment variable to the virtual display.
    virtual_display = pyvirtualdisplay.Display().start()
  except easyprocess.EasyProcessCheckInstalledError:
    virtual_display = None

  if virtual_display:
    argv = ['-W', 'tests/functional/']
    nose.run(argv=argv)
    virtual_display.stop()
  else:
    logging.warning('WARNING: You don\'t have Xvfb installed. This is required in order'
           ' to run tests in browsers headlessly')
    logging.warning('You can either install xvfb ("sudo apt-get install xvfb" in Ubuntu)'
           ' or run tests with --browsers-gui switch')
    argv = ['-W', 'tests/functional/']
    nose.run(argv=argv)


def main():
  tests = set()
  if '-js-dev' in sys.argv:
    run_js_dev()
  else:
    if '-t' in sys.argv:
      i = sys.argv.index('-t')
      tests.update(sys.argv[i+1].split(','))
      del sys.argv[i:i+2]
    else:
      tests = set(['js', 'pyunit', 'pylint', 'functional'])

    if 'functional' in tests:
      run_browsers_gui = False
      if '--browsers-gui' in sys.argv:
        i = sys.argv.index('--browsers-gui')
        del sys.argv[i]
        run_browsers_gui = True
      run_functional_tests(run_browsers_gui)
    if 'pylint' in tests:
      run_pylint()
    if 'pyunit' in tests:
      run_pyunit_tests()
    if 'js' in tests:
      run_browsers_gui = False
      if '--browsers-gui' in sys.argv:
        i = sys.argv.index('--browsers-gui')
        del sys.argv[i]
        run_browsers_gui = True
      run_js_tests(run_browsers_gui)

if __name__ == '__main__':
  main()
