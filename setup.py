"""Minimal setup script to appease buildout for Melange."""

import os
import re

import setuptools

MATCH_VERSION = re.compile('version: ([0-9\-]+)')

MELANGE_NAME = 'melange'
MELANGE_DESCRIPTION = (
    'The goal of this project is to create a framework for ' +
    'representing Open Source contribution workflows, such as ' +
    'the existing Google Summer of Code TM (GSoC) program.')
MELANGE_AUTHORS = open('AUTHORS').read()
MELANGE_URL = 'http://code.google.com/p/soc'
MELANGE_LICENSE = 'Apache2'

PACKAGES = setuptools.find_packages(exclude=['thirdparty', 'parts'])
TESTS_REQUIRE = [
    'zope.testbrowser',
    'gaeftest',
    'gaetestbed',
    'webtest',
    'mox',
    'nose',
    'mock',
    ]
ENTRY_POINTS = {
    'console_scripts': [
        'run-tests = tests.run:main',
        'gen-app-yaml = scripts.gen_app_yaml:main',
        'stats = scripts.stats:main',
        'download-student-forms = scripts.download_student_forms:main',
        ],
    }


try:
  appyaml = open(os.path.join('app', 'app.yaml.template'))
  version = MATCH_VERSION.findall(appyaml.read())[0]
except:
  version = 'UNKNOWN'

setuptools.setup(
    name=MELANGE_NAME,
    description=MELANGE_DESCRIPTION,
    version=version,
    packages=PACKAGES,
    author=MELANGE_AUTHORS,
    url=MELANGE_URL,
    license=MELANGE_LICENSE,
    install_requires=[],
    tests_require=TESTS_REQUIRE,
    entry_points=ENTRY_POINTS,
    include_package_data=True,
    zip_safe=False,
    )
