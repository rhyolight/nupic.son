# Copyright 2008 the Melange authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module containing Melange Django settings.
"""


import os

# Debug flag True only on App Engine development environment (dev_appserver.py)
# dev_appserver sets SERVER_SOFTWARE to 'Development/1.0'
DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Dev')
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

# A dictionary containing the settings for all databases to be
# used with Django.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy',
        'NAME': 'dummy'
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# Create a random SECRET_KEY, this key will be different for each instance of
# Melange that AppEngine creates, guaranteeing that we cannot accidentally rely
# on any Django feature that uses it. That is, if we would accidentally rely on
# such a feature, it would fail safely (by, for example, rejecting a user
# request).
# We would prefer if there was a way to make any such request fail with a 50x
# error, but Django does not provide such an option.
SECRET_KEY_LENGTH = 50
SECRET_KEY = os.urandom(SECRET_KEY_LENGTH).encode("hex")

MIDDLEWARE_CLASSES = (
    'google.appengine.ext.appstats.recording.AppStatsDjangoMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'soc.middleware.blobstore.BlobStoreMiddleware',
    'soc.middleware.xsrf.XsrfMiddleware',
)

ROOT_URLCONF = 'urls'

ROOT_PATH = os.path.dirname(__file__)
TEMPLATE_DIRS = (
    # TODO(proto): customize the template search directories
    os.path.join(ROOT_PATH, 'soc', 'templates'),
    os.path.join(ROOT_PATH, 'shell', 'templates'),
    os.path.join(ROOT_PATH, 'melange', 'content', 'html'),
    os.path.join(ROOT_PATH, 'summerofcode', 'content', 'html'),
    os.path.join(ROOT_PATH, 'codein', 'content', 'html'),
)

INSTALLED_APPS = (
    'soc.views.helper',
#    'soc.modules.gsoc.views.helper',
#    'soc.modules.gci.views.helper',
#    'django.contrib.auth',
#    'django.contrib.contenttypes',
#    'django.contrib.sessions',
#    'django.contrib.sites',
)

GCI_TASK_QUOTA_LIMIT_ENABLED = False

CALLBACK_MODULE_NAMES = [
    'codein.callback',
    'melange.callback',
    'soc.modules.soc_core.callback',
    'soc.modules.gsoc.callback',
    'soc.modules.gci.callback',
    'summerofcode.callback'
    ]

#GData APIs Source:
GDATA_SOURCE = 'Google-Melange-v1'

#In order to use same access token with different services, we demand
#a generic token that has access to all scopes that Melange uses. This
#provides single authentication instead of seperate for each service.
#So all scopes are defined together in a list:
GDATA_SCOPES = [
    # Used for: Syncing student proposals, ...
    'https://docs.google.com/feeds',

    # Used for: Exporting Melange lists, ...
    'https://spreadsheets.google.com/feeds/',
]
