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

from soc.logic import site as site_logic


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

  program = db.get(program_key)
  organization = ndb.Key.from_old_key(org_key).get()

  # TODO(daniel): add email recipients, i.e. organization admins
  site = site_logic.singleton()

  admins = profile_logic.getOrgAdmins(organization.key)
  recipients = [a.contact.email for a in admins]

  @ndb.transactional
  def updateOrganizationStatus():
    """Transactionally updates organization status."""
    # only organizations defined for the specified program should be processed
    if organization.program.to_old_key() == program_key:
      if organization.status == org_model.Status.PRE_ACCEPTED:
        org_logic.setStatus(
            organization, program, site, org_model.Status.ACCEPTED)
      elif organization.status == org_model.Status.PRE_REJECTED:
        org_logic.setStatus(
            organization, program, site, org_model.Status.REJECTED)

  updateOrganizationStatus()
