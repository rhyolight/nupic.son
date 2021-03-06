# -*- coding: utf-8 -*-

"""
Example Usage
=============

The following commands can be run from the root directory of the Mercurial
repo. To run ``paver``, however, you'll need to do ``easy_install Paver``.
Most of the following commands accept other arguments; see ``command --help``
for more information, or ``paver help`` for a list of all the valid commands.

    ``paver build``
        Builds the project. This essentially just runs a bunch of other tasks,
        like ``pylint`` and ``tinymce_zip``, etc.
    ``paver pylint``
        Runs PyLint on the project.
    ``paver tinymce_zip``
        Builds the TinyMCE zip file.

If you specify ``--dry-run`` before a task, then the action of that task will
not actually be carried out, although logging output will be displayed as if
it were. For example, you could run ``paver --dry-run tinymce_zip`` to see what
files would be added to the ``tinymce.zip`` file, etc.
"""

import cStringIO
import os
import shutil
import sys
import zipfile

from google.appengine.ext import testbed

from epydoc import cli
from paver import easy
from paver import path
from paver import tasks
from pylint import lint

# Paver comes with Jason Orendorff's 'path' module; this makes path
# manipulation easy and far more readable.
PROJECT_DIR = path.path(__file__).dirname().abspath()
REPORTS_DIR = PROJECT_DIR / 'reports'
JS_DIRS = ['soc/content/js']
COPY_DIRS = JS_DIRS + ['soc/content/css']
DONT_COPY_DIRS = ['soc/content/js/thirdparty/tiny_mce']
APP_FILES = [
    'app.yaml',
    'index.yaml',
    'queue.yaml',
    'cron.yaml',
    'mapreduce.yaml',
    'main.py',
    'settings.py',
    'urls.py',
    'gae_django.py',
    'profiler.py',
    'appengine_config.py',
    ]
APP_DIRS = [
    'melange',
    'soc',
    'feedparser',
    'djangoforms',
    'ranklist',
    'shell',
    'html5lib',
    'gviz',
    'webmaster',
    'mapreduce',
    'summerofcode',
    'codein',
    'apiclient',
    'httplib2',
    'oauth2client',
    'uritemplate',
    ]
CSS_FILES = {
    'jquery-ui/jquery.ui.merged.css': [
        'jquery-ui/jquery.ui.core.css',
        'jquery-ui/jquery.ui.resizable.css',
        'jquery-ui/jquery.ui.selectable.css',
        'jquery-ui/jquery.ui.accordion.css',
        'jquery-ui/jquery.ui.autocomplete.css',
        'jquery-ui/jquery.ui.button.css',
        'jquery-ui/jquery.ui.dialog.css',
        'jquery-ui/jquery.ui.slider.css',
        'jquery-ui/jquery.ui.tabs.css',
        'jquery-ui/jquery.ui.datepicker.css',
        'jquery-ui/jquery.ui.progressbar.css',
        'jquery-ui/jquery.ui.theme.css',
        ],
    }
CSS_DIRS = ['soc/content/css/gsoc/', 'soc/content/css/gci']
ZIP_FILES = ['tiny_mce.zip']
DOCS_CONFIG = PROJECT_DIR / 'docs.config'
DOCS_OUTPUT = REPORTS_DIR / 'docs'

# TODO(nathaniel): Get rid of all the "overrides" stuff as part of
# finishing https://code.google.com/p/soc/issues/detail?id=1560.
OVERRIDES_FOLDER = PROJECT_DIR / 'overrides'
OVERRIDES_DIRS = ['soc', 'soc/models', 'soc/content']
OVERRIDES_FILES = ['soc/models/universities.py']

BUILD_BUNCH = easy.Bunch(
    project_dir=PROJECT_DIR,
    app_files=APP_FILES,
    app_dirs=APP_DIRS,
    app_build=PROJECT_DIR / 'build',
    app_folder=PROJECT_DIR / 'app',
    css_dirs=CSS_DIRS,
    css_files=CSS_FILES,
    zip_files=ZIP_FILES,
    docs_config=DOCS_CONFIG,
    docs_output=DOCS_OUTPUT,
    copy_dirs=COPY_DIRS,
    dont_copy_dirs=DONT_COPY_DIRS,
    overrides_folder=OVERRIDES_FOLDER,
    overrides_dirs=OVERRIDES_DIRS,
    overrides_files=OVERRIDES_FILES,
    skip_closure=False,
    skip_docs=False,
    skip_pylint=False)

PYLINT_APP_FOLDER_MODULES = [
    'codein',
    'melange',
    'soc',
    'summerofcode',
    'settings.py',
    'urls.py',
    'main.py',
    ]
PYLINT_TESTS_FOLDER = PROJECT_DIR / 'tests'
PYLINT_PROJECT_FOLDER_MODULES = ['pavement.py', 'setup.py']
PYLINT_VERBOSE_ARGS = [
    # In the rcfile(pylintrc) errors-only option is set. This is to enable
    # other messages as well.
    # R and C modules are just too chatty, we can however turn a few of the
    # more useful ones on explicitly.
    '--enable=W,F',
    '--reports=yes',
    # We may want to enable these in the future
    '--disable=protected-access,attribute-defined-outside-init',
    # TODO(nathaniel): fix all occurences and enable this
    '--disable=abstract-method',
    # These are just plain useless, we don't ever want to these
    '--disable=fixme,unused-argument,star-args,bad-builtin,locally-disabled',
    # These are somewhat debatable, but not realistic for Melange
    '--disable=no-init,super-init-not-called',
    # TODO(nathaniel): fix all occurences and move this to pylintrc file.
    '--enable=line-too-long',
    ]
PYLINT_BUNCH = easy.Bunch(
    app_folder_modules=PYLINT_APP_FOLDER_MODULES,
    project_folder_modules=PYLINT_PROJECT_FOLDER_MODULES,
    tests_folder=PYLINT_TESTS_FOLDER,
    verbose=False,
    verbose_args=PYLINT_VERBOSE_ARGS,
    pylint_args=[],
    with_module=None,
    ignore=False,
    **BUILD_BUNCH)

CLOSURE_BIN = PROJECT_DIR / 'thirdparty/closure/compiler.jar'
CLOSURE_NO_OPTIMIZE = ['jquery-jqgrid.base.js', 'jLinq-2.2.1.js']
CLOSURE_BUNCH = easy.Bunch(
    js_filter=None,
    js_dir=None,
    output_to_build=False,
    js_dirs=JS_DIRS,
    closure_bin=CLOSURE_BIN,
    no_optimize=CLOSURE_NO_OPTIMIZE,
    **BUILD_BUNCH)

# Install the option bunches.
easy.options(
    build=BUILD_BUNCH,
    clean_build=BUILD_BUNCH,
    tinymce_zip=BUILD_BUNCH,
    pylint=PYLINT_BUNCH,
    closure=CLOSURE_BUNCH)


# Utility functions

def tinymce_zip_files(tiny_mce_dir):
  """Yields each filename which should go into ``tiny_mce.zip``."""
  for filename in tiny_mce_dir.walkfiles():
    if '.svn' in filename.splitall():
      continue

    tasks.environment.info('%-4stiny_mce.zip <- %s', '', filename)
    arcname = tiny_mce_dir.relpathto(filename)
    yield filename, arcname


def write_zip_file(zip_file_handle, files):
  if tasks.environment.dry_run:
    for args in files:
      pass
    return
  zip_file = zipfile.ZipFile(zip_file_handle, mode='w')
  for args in files:
    zip_file.write(*args)
  zip_file.close()


def symlink(target, link_name):
  if hasattr(target, 'symlink'):
    target.symlink(link_name)
  else:
    # If we are on a platform where symlinks are not supported (such as
    # Windows), simply copy the files across.
    target.copy(link_name)

# Tasks


@easy.task
@easy.cmdopts([
    ('app-folder=', 'a', 'App folder directory (default /app)'),
    ('pylint-command=', 'c', 'Specify a custom pylint executable'),
    ('with-module=', 'w', 'Include a specific module'),
    ('verbose', 'v', 'Enables a lot of the noisy pylint output'),
    ('ignore', 'i', 'Ignore PyLint errors')
])
def pylint(options):
  """Check the source code using PyLint."""
  # Initial command.
  arguments = []

  if options.verbose:
    arguments.extend(options.verbose_args)

  if 'pylint_args' in options:
    arguments.extend(list(options.pylint_args))

  # Add the list of paths containing the modules to check using PyLint.
  if options.with_module:
    arguments.append(options.with_module)
  else:
    arguments.extend(str(options.app_folder / module)
                     for module in options.app_folder_modules)
    arguments.extend(str(options.project_dir / module)
                     for module in options.project_folder_modules)
    # We should lint everything in the tests folder.
    arguments.append(str(options.tests_folder))

  # By placing run_pylint into its own function, it allows us to do dry runs
  # without actually running PyLint.
  def run_pylint():
    # Add app folder to path.
    sys.path.insert(0, options.app_folder.abspath())
    # Add google_appengine directory to path.
    path = options.project_dir.abspath() / 'thirdparty' / 'google_appengine'
    sys.path.insert(0, path)

    # Specify PyLint RC file.
    path = options.project_dir.abspath() / 'pylintrc'
    arguments.append('--rcfile=' + path)

    # `lint.Run.__init__` runs the PyLint command.
    try:
      lint.Run(arguments)
    # PyLint will `sys.exit()` when it has finished, so we need to catch
    # the exception and process it accordingly.
    except SystemExit, exc:
      return_code = exc.args[0]
      if return_code != 0 and (not options.pylint.ignore):
        raise tasks.BuildFailure(
            'PyLint finished with a non-zero exit code: %d' % return_code)

  return easy.dry('pylint ' + ' '.join(arguments), run_pylint)


@easy.task
@easy.cmdopts([
    ('app-build=', 'b', 'App build directory (default /build)'),
    ('app-folder=', 'a', 'App folder directory (default /app)'),
    ('skip-pylint', 's', 'Skip PyLint checker'),
    ('skip-docs', '', 'Skip documentation creation'),
    ('ignore-pylint', 'i', 'Ignore results of PyLint (but run it anyway)'),
    ('verbose-pylint', 'v', 'Make PyLint run verbosely'),
])
def build(options):
  """Build the project."""
  # If `--skip-pylint` is not provided, run PyLint.
  if not options.skip_pylint:
    # If `--ignore-pylint` is provided, act as if `paver pylint --ignore`
    # was run. Likewise for `--verbose-pylint`.
    if options.get('ignore_pylint', False):
      options.pylint.ignore = True
    if options.get('verbose_pylint', False):
      options.pylint.verbose = True
    pylint(options)

  # Compile the css files into one
  build_css(options)

  # Clean old generated zip files from the app folder.
  clean_zip(options)

  # Clean the App build directory by removing and re-creating it.
  clean_build(options)

  # Build the tiny_mce.zip file.
  tinymce_zip(options)

  # Make the necessary symlinks between the app and build directories.
  build_symlinks(options)

  # Handle overrides
  overrides(options)

  # Handle deep overrides (copy)
  deep_overrides(options)

  # Run closure over JS files
  options.closure.build = True
  closure(options)

  # Run grunt for production
  run_grunt(options)

  # Builds documentation for the project
  if not options.skip_docs:
    build_docs(options)


@easy.task
def run_grunt(options):
  """Run Grunt for build"""
  easy.sh('bin/grunt build')


@easy.task
@easy.cmdopts([
    ('app-build=', 'b', 'App build directory (default /build)'),
    ('app-folder=', 'a', 'App folder directory (default /app)'),
])
def build_symlinks(options):
  """Build symlinks between the app and build folders."""
  # Create the symbolic links from the app folder to the build folder.
  for filename in options.app_files + options.app_dirs + options.zip_files:
    # The `symlink()` function handles discrepancies between platforms.
    target = path.path(options.app_folder) / filename
    link = path.path(options.app_build) / filename
    easy.dry('%-4s%-20s <- %s' % ('', target, link),
        lambda: symlink(target, link.abspath()))


@easy.task
def build_css(options):
  """Compiles the css files into one."""
  for css_dir in options.css_dirs:
    for target, components in options.css_files.iteritems():
      target = options.app_folder / css_dir / target
      with target.open('w') as target_file:
        for component in components:
          source = options.app_folder / css_dir / component
          easy.dry(
              "cat %s >> %s" % (source, target),
              lambda: shutil.copyfileobj(source.open('r'), target_file))


@easy.task
@easy.cmdopts([
    ('app-build=', 'b', 'App build directory (default /build)'),
])
def clean_build(options):
  """Clean the build folder."""
  # Not checking this could cause an error when trying to remove a
  # non-existent file.
  if path.path(options.app_build).exists():
    path.path(options.app_build).rmtree()
  path.path(options.app_build).makedirs_p()


@easy.task
@easy.cmdopts([
    ('app-folder=', 'a', 'App folder directory (default /app)'),
])
def clean_zip(options):
  """Remove all the generated zip files from the app folder."""
  for zip_file in options.zip_files:
    zip_path = path.path(options.app_folder) / zip_file
    if zip_path.exists():
      zip_path.remove()


@easy.task
@easy.cmdopts([
    ('app-folder=', 'a', 'App folder directory (default /app)'),
])
def tinymce_zip(options):
  """Create the zip file containing TinyMCE."""
  tinymce_dir = path.path(
      options.app_folder) / 'soc/content/js/thirdparty/tiny_mce'
  tinymce_zip_filename = path.path(options.app_folder) / 'tiny_mce.zip'
  if tasks.environment.dry_run:
    tinymce_zip_fp = cStringIO.StringIO()
  else:
    # Ensure the parent directories exist.
    tinymce_zip_filename.dirname().makedirs_p()
    tinymce_zip_fp = open(tinymce_zip_filename, mode='w')

  try:
    write_zip_file(tinymce_zip_fp, tinymce_zip_files(tinymce_dir))
  except Exception, exc:
    tinymce_zip_fp.close()
    tinymce_zip_filename.remove()
    raise tasks.BuildFailure(
        'Error occurred creating tinymce.zip: %r' % (exc,))
  finally:
    if not tinymce_zip_fp.closed:
      tinymce_zip_fp.close()

def run_closure(f):
  """Runs the closure compiler over one JS file"""
  tmp = f + ".tmp.js"
  f.move(tmp)

  try:
    easy.sh("java -jar '%s' --js='%s' > '%s'" % (
        easy.options.closure_bin, tmp, f))
  except easy.BuildFailure:
    tasks.environment.error(
        '%s minimization failed, copying plain file', f)
    tmp.copy(f)

  tmp.remove()

@easy.task
@easy.cmdopts([
    ('app-folder=', 'a', 'App folder directory (default /app)'),
    ('js-dir=', 'j', 'JS directory to minimize, relative to /app'),
    ('js-filter=', 'f', 'Minimize files matching this regex, default "*.js"'),
])
def closure(options):
  """Runs the closure compiler over the JS files."""
  if options.js_dir:
    dirs = [options.app_folder / options.js_dir]
  else:
    if options.closure.build:
      dirs = [options.app_build / i for i in options.js_dirs]
    else:
      dirs = [options.app_folder / i for i in options.js_dirs]
  old_size = 0
  new_size = 0

  js_filter = options.js_filter if options.js_filter else "*.js"

  for js_dir in dirs:
    if options.closure.build:
      min_dir = js_dir
    else:
      min_dir = js_dir + ".min"
      if not options.js_filter:
        min_dir.rmtree()
        js_dir.copytree(min_dir)

    for f in min_dir.walkfiles(js_filter):
      if f.name in options.no_optimize:
        tasks.environment.info(
            '%-4sCLOSURE: Skipping %s', '', f)
        continue

      tasks.environment.info(
          '%-4sCLOSURE: Processing %s', '', f)

      old_size += f.size

      run_closure(f)

      new_size += f.size

  rate = new_size*100 / old_size
  tasks.environment.info(
      '%-4sCLOSURE: Source file sizes: %s, Dest file sizes: %s, Rate: %s',
      '', old_size, new_size, rate)


@easy.task
@easy.cmdopts([
    ('docs-output=', '', 'Output directory for documentation'),
    ('docs-config=', '', 'Configuration file for documentation'),
])
def build_docs(options):
  """Builds documentation for the project."""
  # Epydoc smartly makes its own output directory if the output
  # directory doesn't exist, but is not so smart that it will
  # recursively create the parents of the output directory if they
  # don't exist. Since we have the output directory path here we
  # might as well create it rather than parsing out just the parents
  # and leaving the directory itself to epydoc.
  if not os.path.exists(options.docs_output):
    os.makedirs(options.docs_output)

  # NOTE(nathaniel): Epydoc actually imports modules during analysis,
  # Melange's modules in turn import App Engine modules, and App Engine
  # modules complain if the right Django and App Engine settings aren't
  # in place at import time. Consequently, we must mutate the current
  # environment to be that of an App Engine test before we can build
  # Melange's documentation.
  os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
  os.environ['SERVER_SOFTWARE'] = 'build'
  appengine_testbed = testbed.Testbed()
  appengine_testbed.activate()
  appengine_testbed.init_datastore_v3_stub()

  # NOTE(nathaniel): Deriving the options to pass to (epydoc.)cli.main this
  # way is horsehockey, but epydoc doesn't actually expose a proper API.
  stored_actual_argv = sys.argv
  sys.argv = [
      'unused_fake_executuable',
      '--config=%s' % options.docs_config,
      '--output=%s' % options.docs_output,
      ]
  epydoc_options, epydoc_names = cli.parse_arguments()
  sys.argv = stored_actual_argv

  # NOTE(nathaniel): As of 13 January 2014 this call emits two false
  # positive "Bad argument - expected name or tuple" errors. See
  # https://sourceforge.net/p/epydoc/bugs/363/ for progress.
  cli.main(epydoc_options, epydoc_names)


@easy.task
def deep_overrides(options):
  """Copies files from the copy structure to the build directory."""
  dirs = [options.app_folder / i for i in options.copy_dirs]
  dont_copy_dirs = [options.app_folder / i for i in options.dont_copy_dirs]

  for source_dir in dirs:
    dest_dir = options.app_build / options.app_folder.relpathto(source_dir)
    dest_dir.remove()
    source_dir.copytree(dest_dir)

  for remove_dir in dont_copy_dirs:
    dest_dir = options.app_build / options.app_folder.relpathto(remove_dir)
    dest_dir.rmtree()


@easy.task
def overrides(options):
  """Copies files from the overrides structure to the build directory."""
  for path in options.overrides_dirs:
    target = options.app_build / path
    unroll_symlink(target)
  for path in options.overrides_files:
    target = options.overrides_folder / path
    if not target.exists():
      continue
    if not target.isfile():
      tasks.environment.info('target "%s" is not a file', target)
      continue
    to = options.app_build / path
    to.remove()
    target.symlink(to)


def unroll_symlink(target):
  """Unrolls a symlink.

  Does the following if target is a directory symlink:
  - removes the symlink
  - creates a directory with the same name
  - populates it with symlinks to individual files

  Otherwise does nothing.
  """
  if not target.exists():
    tasks.environment.info('target "%s" does not exist', target)
    return
  if not target.isdir():
    tasks.environment.info('target "%s" is not a directory', target)
    return
  if not target.islink():
    tasks.environment.info('target "%s" is not a symlink', target)
    return

  deref = target.readlinkabs()
  target.remove()
  target.mkdir()

  contents = deref.listdir()

  for path in contents:
    path.symlink(target / path.name)
