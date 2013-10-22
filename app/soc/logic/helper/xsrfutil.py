# Copyright 2010 the Melange authors.
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

"""Helper methods for creating & verifying XSRF tokens."""


import base64
import hmac
import os  # for urandom
import time

from google.appengine.api import users


# Delimiter character
DELIMITER = ':'

# 4 days in seconds
DEFAULT_TIMEOUT_SECS = 4*24*60*60

# Number of bytes in the secret key.
XSRF_SECRET_KEY_LENGTH = 16


class InvalidTokenException(Exception):
  """Indicates that the token is invalid."""

  def __init__(self, reason):
    """Constructs a new InvalidTokenException.

    Args:
      reason: A string describing why the token is invalid.
    """
    self.reason = reason


def _generateToken(key, user_id, action_id="", when=None):
  """Generates a URL-safe token for the given user, action, time tuple.

  Args:
    key: secret key to use.
    user_id: the user ID of the authenticated user (e.g. Gaia ID).
    action_id: a string identifier of the action they requested
      authorization for.
    when: the time in seconds since the epoch at which the user was
      authorized for this action. If not set the current time is used.

  Returns:
    A string XSRF protection token.
  """
  when = when or int(time.time())
  digester = hmac.new(key.encode('utf-8'))
  digester.update(str(user_id))
  digester.update(DELIMITER)
  digester.update(action_id)
  digester.update(DELIMITER)
  digester.update(str(when))
  digest = digester.digest()

  token = base64.urlsafe_b64encode('%s%s%d' % (digest,
                                               DELIMITER,
                                               when))
  return token


def _validateToken(key, token, user_id, action_id=""):
  """Validates that the given token authorizes the user for the action.

  Tokens are invalid if the time of issue is too old or if the token
  does not match what generateToken outputs (i.e. the token was forged).

  Args:
    key: secret key to use.
    token: a string of the token generated by generateToken.
    user_id: the user ID of the authenticated user (e.g. Gaia ID).
    action_id: a string identifier of the action they requested
      authorization for.

  Raises:
    InvalidTokenException: If the token is invalid.
  """
  if not token:
    raise InvalidTokenException("Missing token")

  try:
    decoded = base64.urlsafe_b64decode(str(token))
  except (TypeError, ValueError):
    raise InvalidTokenException("Could not base64 decode token")

  try:
    token_time = long(decoded.split(DELIMITER)[-1])
  except (TypeError, ValueError):
    raise InvalidTokenException("Could not split token")

  current_time = time.time()

  # If the token is too old it's not valid.
  if current_time - token_time > DEFAULT_TIMEOUT_SECS:
    raise InvalidTokenException("Token too old")

  # The given token should match the generated one with the same time.
  expected_token = _generateToken(key, user_id, action_id, when=token_time)
  if token != expected_token:
    raise InvalidTokenException("Token mismatch for user_id '%s'" % user_id)


def _getCurrentUserId():
  """Returns a unique id string for the current user, or -1 if not logged in.

  We don't use the Melange user data because this doesn't exist until the
  user creates a profile, and that itself is a form that should be protected
  with an XSRF token.
  """
  appengine_user = users.get_current_user()
  if appengine_user:
    user_id = appengine_user.user_id()
  else:
    user_id = -1
  return user_id


def getGeneratedTokenForCurrentUser(secret_key):
  """Returns a generated token."""
  user_id = _getCurrentUserId()
  expected_token = _generateToken(secret_key, user_id)
  return expected_token


def isTokenValid(secret_key, token_from_browser):
  """Determines of the given token is valid."""
  user_id = _getCurrentUserId()
  return _validateToken(secret_key, token_from_browser, user_id)


def newXsrfSecretKey():
  """Returns a random XSRF secret key.  This should only be called once per
  instance of Melange.
  """
  return os.urandom(XSRF_SECRET_KEY_LENGTH).encode("hex")
