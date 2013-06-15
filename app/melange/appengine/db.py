# Copyright 2008 the Melange authors.
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

"""App Engine datastore related functions."""

from django.core import validators


def email_validator(property, value):
  """Validates whether the input value for the specified property
  is a valid email address.

  The function signature is required by NBD API. Property parameter is not
  actually used in this function.

  Args:
    property: validated model property
    value: value to validate

  Raises:
    ValueError: if the specified value is not a valid email address.
  """
  try:
    # use internal django's validator
    validators.validate_email(value)
  except Exception:
    raise ValueError('%s is not a valid email address.' % value)


_LINK_VALIDATOR = validators.URLValidator()
def link_validator(property, value):
  """Validates whether the input value for the specified property
  is a valid URL.

  The function signature is required by NBD API. Property parameter is not
  actually used in this function.

  Args:
    property: validated model property
    value: value to validate

  Raises:
    ValueError: if the specified value is not a valid URL.
  """
  try:
    # use internal django's validator
    _LINK_VALIDATOR(value)
  except Exception:
    raise ValueError('%s is not a valid URL.' % value)
