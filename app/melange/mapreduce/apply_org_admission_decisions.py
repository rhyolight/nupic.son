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

"""MapReduce to finalize and apply program administrators' decisions on
what organizations are accepted into program."""

from google.appengine.ext import db
from google.appengine.ext import ndb

from mapreduce import context as mapreduce_context

from melange.logic import organization as org_logic
from melange.logic import profile as profile_logic
from melange.models import organization as org_model
from melange.request import links

from codein.views.helper import urls as ci_urls

from soc.logic import site as site_logic

# pylint: disable=unused-import
from soc.modules.gci.models.program import GCIProgram
from soc.modules.gsoc.models.program import GSoCProgram
from summerofcode.models.organization import SOCOrganization
# pylint: enable=unused-import

from summerofcode.views.helper import urls as soc_urls


def process(org_key):
  """Processes a single organization.

  Organization status is updated to ACCEPTED or REJECTED if the current
  status has been set to PRE_ACCEPTED or PRE_REJECTED, respectively,
  by program administrators.

  Args:
    org_key: Organization key.
  """
  context = mapreduce_context.get()
  program_key = db.Key(context.mapreduce_spec.mapper.params['program_key'])

  if program_key.kind() == 'GSoCProgram':
    url_names = soc_urls.UrlNames
  elif program_key.kind() == 'GCIProgram':
    url_names = ci_urls.UrlNames
  else:
    raise ValueError('Invalid program type %s' % program_key.kind())

  program = db.get(program_key)

  site = site_logic.singleton()

  org_key = ndb.Key.from_old_key(org_key)
  org_admins = profile_logic.getOrgAdmins(org_key)

  # We are "prefetching" the ProgramMessages entity here instead of fetching
  # it where it is required i.e. when the message templates are required
  # to build the email message body. We do this because we perform the
  # operation of fetching the ProgramMessages entity if it exists or create
  # it if it doesn't in a Appengine regular "db" transation whereas rest
  # of the updating of organization entities happen within an ndb transaction
  # because Organization model is an ndb model and such cross API nested
  # transactions are incompatible in Appengine.
  program_messages = program.getProgramMessages()

  @ndb.transactional
  def updateOrganizationStatus():
    """Transactionally updates organization status."""
    # only organizations defined for the specified program should be processed
    organization = org_key.get()
    if organization.program.to_old_key() == program_key:
      if organization.status == org_model.Status.PRE_ACCEPTED:
        org_logic.setStatus(
            organization, program, site, program_messages,
            org_model.Status.ACCEPTED, links.ABSOLUTE_LINKER, url_names,
            org_admins=org_admins)
      elif organization.status == org_model.Status.PRE_REJECTED:
        org_logic.setStatus(
            organization, program, site, program_messages,
            org_model.Status.REJECTED, links.ABSOLUTE_LINKER, url_names,
            org_admins=org_admins)

  updateOrganizationStatus()
