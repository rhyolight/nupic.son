# Copyright 2011 the Melange authors.
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

"""Utils for manipulating program data."""

from codein import types as ci_types

from google.appengine.ext import db

from melange import types

from soc.models import document as document_model
from soc.models.org_app_survey import OrgAppSurvey
from soc.models import program as program_model
from soc.models.site import Site
from soc.models.sponsor import Sponsor

from soc.modules.gci.models.organization import GCIOrganization
from soc.modules.seeder.logic.providers import string as string_provider
from soc.modules.seeder.logic.seeder import logic as seeder_logic

from summerofcode import types as soc_types

from tests import org_utils
from tests import profile_utils
from tests import timeline_utils


# TODO(daniel): move this function to a separate module
def seedSite(**kwargs):
  """Seeds a new site entity.

  Returns:
    Newly seeded Site entity.
  """
  properties = {
    'key_name': 'site',
    'active_program': None,
  }
  properties.update(kwargs)

  site = Site(**properties)
  site.put()
  return site


TEST_SPONSOR_EMIAL = 'test.sponsor@example.com'
TEST_SPONSOR_HOME_PAGE = 'http://test.sponsor.home.page.com'
TEST_SPONSOR_NAME = 'Test Sponsor'
TEST_SPONSOR_DESCRIPTION = 'Test Sponsor Description'
TEST_SPONSOR_SHORT_NAME = 'Sponsor'

# TODO(daniel): move this function to a separate module
def seedSponsor(sponsor_id=None, **kwargs):
  """Seeds a new sponsor entity.

  Args:
    sponsor_id: Identifier of the new sponsor.

  Returns:
    Newly seeded Sponsor entity.
  """
  sponsor_id = sponsor_id or string_provider.UniqueIDProvider().getValue()

  properties = {
      'description': TEST_SPONSOR_DESCRIPTION,
      'email': TEST_SPONSOR_EMIAL,
      'home_page': TEST_SPONSOR_HOME_PAGE,
      'key_name': sponsor_id,
      'link_id': sponsor_id,
      'org_id': sponsor_id,
      'name': TEST_SPONSOR_NAME,
      'short_name': TEST_SPONSOR_SHORT_NAME,
      'sponsor_id': sponsor_id,
      }
  properties.update(kwargs)
  sponsor = Sponsor(**properties)
  sponsor.put()

  return sponsor


def seedTimeline(models=types.MELANGE_MODELS,
    timeline_id=None, sponsor_key=None, **kwargs):
  """Seeds a new timeline.

  Args:
    models: Instance of types.Models that represent appropriate models.
    timeline_id: Identifier of the new timeline.
    sponsor_key: Sponsor key to be used as scope for the timeline.

  Returns:
    Newly seeded timeline entity.
  """
  timeline_id = timeline_id or string_provider.UniqueIDProvider().getValue()

  sponsor_key = sponsor_key or seedSponsor()

  properties = {
      'key_name': '%s/%s' % (sponsor_key.name(), timeline_id),
      'link_id': timeline_id,
      'program_start': timeline_utils.past(),
      'program_end': timeline_utils.future(),
      'scope': sponsor_key,
      }
  properties.update(kwargs)
  timeline = models.timeline_model(**properties)
  timeline.put()

  return timeline


TEST_PROGRAM_DESCRIPTION = 'Test Program Description'
TEST_PROGRAM_NAME = 'Test Program'
TEST_PROGRAM_SHORT_NAME = 'Program'

TEST_DOCUMENT_PREFIX = 'program'
TEST_DOCUMENT_TITLE = 'Test Document'

def seedProgram(models=types.MELANGE_MODELS, program_id=None,
    sponsor_key=None, timeline_key=None, **kwargs):
  """Seeds a new program.

  Args:
    models: instance of types.Models that represent appropriate models.
    program_id: Identifier of the new program.
    sponsor_key: Sponsor key for the new program.
    timeline_key: Timeline key for the new program.

  Returns:
    Newly seeded program entity.
  """
  program_id = program_id or string_provider.UniqueIDProvider().getValue()

  sponsor_key = sponsor_key or seedSponsor().key()
  timeline_key = timeline_key or seedTimeline(
      models=models, timeline_id=program_id, sponsor_key=sponsor_key).key()

  properties = {
      'scope': sponsor_key,
      'sponsor': sponsor_key,
      'link_id': program_id,
      'program_id': program_id,
      'key_name': '%s/%s' % (sponsor_key.name(), program_id),
      'name': TEST_PROGRAM_NAME,
      'short_name': TEST_PROGRAM_SHORT_NAME,
      'description': TEST_PROGRAM_DESCRIPTION,
      'timeline': timeline_key,
      'status': program_model.STATUS_VISIBLE,
      }
  properties.update(kwargs)
  program = models.program_model(**properties)

  host = profile_utils.seedUser(host_for=[sponsor_key])
  document_id = string_provider.UniqueIDProvider().getValue()
  prefix = kwargs.get('prefix', TEST_DOCUMENT_PREFIX)
  properties = {
      'scope': program,
      'read_access': 'public',
      'key_name': '%s/%s/%s' % (prefix, program.key().name(), document_id),
      'link_id': document_id,
      'modified_by': host,
      'author': host,
      'home_for': None,
      'title': TEST_DOCUMENT_TITLE,
      'prefix': prefix,
    }
  document = document_model.Document(**properties)
  document.put()

  program.about_page = document
  program.events_page = document
  program.help_page = document
  program.connect_with_us_page = document
  program.privacy_policy = document
  program.put()

  seedProgramMessages(models=models, program_key=program.key(), **kwargs)

  return program


TEST_APP_TASKS_LIMIT = 20
TEST_SLOTS = 1000

def seedGSoCProgram(program_id=None, sponsor_key=None,
    timeline_key=None, **kwargs):
  """Seeds a new Summer Of Code program.

  Args:
    program_id: Identifier of the new program.
    sponsor_key: Sponsor key for the new program.
    timeline_key: Timeline key for the new program.

  Returns:
    Newly seeded program entity.
  """
  properties = {
      'apps_tasks_limit': TEST_APP_TASKS_LIMIT,
      'slots': TEST_SLOTS,
      'prefix': 'gsoc_program',
      }
  properties.update(kwargs)
  return seedProgram(
      models=soc_types.SOC_MODELS, program_id=program_id,
      sponsor_key=sponsor_key, timeline_key=timeline_key, **properties)


def seedGCIProgram(program_id=None, sponsor_key=None,
    timeline_key=None, **kwargs):
  """Seeds a new Code In program.

  Args:
    program_id: Identifier of the new program.
    sponsor_key: Sponsor key for the new program.
    timeline_key: Timeline key for the new program.

  Returns:
    Newly seeded program entity.
  """
  properties = {'prefix': 'gci_program'}
  properties.update(kwargs)
  return seedProgram(
      models=ci_types.CI_MODELS, program_id=program_id,
      sponsor_key=sponsor_key, timeline_key=timeline_key, **properties)


def seedProgramMessages(
    models=types.MELANGE_MODELS, program_key=None, **kwargs):
  """Seeds a new program messages.

  Args:
    models: instance of types.Models that represent appropriate models.
    program_key: Program key for messages.

  Returns:
    Newly seeded program messages entity.
  """
  properties = {'parent': program_key}
  properties.update(kwargs)
  program_messages = models.program_messages_model(**properties)
  program_messages.put()

  return program_messages


def seedGSoCProgramMessages(program_key=None, **kwargs):
  """Seeds a new program messages for Summer Of Code.

  Args:
    program_key: Program key for messages.

  Returns:
    Newly seeded program messages entity.
  """
  return seedProgramMessages(
      models=soc_types.SOC_MODELS, program_key=program_key)


def seedGCIProgramMessages(program_key=None, **kwargs):
  """Seeds a new program messages for Code In.

  Args:
    program_key: Program key for messages.

  Returns:
    Newly seeded program messages entity.
  """
  return seedProgramMessages(
      models=ci_types.CI_MODELS, program_key=program_key)


def seedApplicationSurvey(program_key, **kwargs):
  """Seeds a new organization application survey for the specified program.

  Args:
    program_key: Program key to create a survey for.
    kwargs: Optional values for other properties of the seeded entity.

  Returns:
    Newly seeded survey entity.
  """
  user = profile_utils.seedNDBUser()
  program = db.get(program_key)

  properties = {
      'scope': program_key,
      'program': program_key,
      'modified_by': user.key.to_old_key(),
      'created_by': user.key.to_old_key(),
      'author': user.key.to_old_key(),
      'schema': ('[["item"],{"item":{"field_type":"input_text",'
                 '"required":false, "label":"test"}}]'),
      'survey_content': None,
      'key_name': '%s/%s/orgapp' % (program.prefix, program_key.name())
      }
  properties.update(kwargs)
  return seeder_logic.seed(OrgAppSurvey, properties)


class ProgramHelper(object):
  """Helper class to aid in manipulating program data.
  """

  def __init__(self, sponsor=None, program=None):
    """Initializes the ProgramHelper.

    Args:
      sponsor: Sponsor entity.
    """
    self.sponsor = sponsor
    self.program = program
    self.org_app = None
    self.org = None
    self.site = None
    self.createOrg = self.createOrUpdateOrg

  def seed(self, model, properties,
           auto_seed_optional_properties=True):
    return seeder_logic.seed(model, properties, recurse=False,
        auto_seed_optional_properties=auto_seed_optional_properties)

  def seedn(self, model, properties, n,
            auto_seed_optional_properties=True):
    return seeder_logic.seedn(model, n, properties, recurse=False,
        auto_seed_optional_properties=auto_seed_optional_properties)

  def createProgram(self, override={}):
    """Creates a program for the defined properties.
    """
    if self.sponsor is None:
      self.sponsor = seedSponsor()

  def createOrgApp(self, override={}):
    """Creates an organization application for the defined properties.
    """
    if self.org_app:
      return self.org_app
    if self.program is None:
      self.createProgram()

    user = profile_utils.seedUser()
    properties = {
        'scope': self.program,
        'program': self.program,
        'modified_by': user,
        'created_by': user,
        'author': user,
        'schema': ('[["item"],{"item":{"field_type":"input_text",'
                   '"required":false, "label":"test"}}]'),
        'survey_content': None,
        'key_name': '%s/%s/orgapp' % (
            self.program.prefix, self.program.key().name()),
    }
    properties.update(override)
    self.org_app = self.seed(OrgAppSurvey, properties)
    return self.org_app

  def _updateEntity(self, entity, override):
    """Updates self.<entity> with override.
    """
    properties = entity.properties()
    for name, value in override.iteritems():
      properties[name].__set__(entity, value)
    entity.put()
    return entity

  def _updateOrg(self, override):
    """Updates self.org with override.
    """
    return self._updateEntity(self.org, override)

  def createOrUpdateOrg(self, override={}):
    """Creates or updates an org (self.org) for the defined properties.
    """
    if self.org:
      if not override:
        return self.org
      else:
        return self._updateOrg(override)
    self.org = self.createNewOrg(override)
    return self.org

  def createNewOrg(self, override={}):
    """Creates a new organization for the defined properties.

    This new organization will not be stored in self.org but returned.
    """
    if self.program is None:
      self.createProgram()


class GSoCProgramHelper(ProgramHelper):
  """Helper class to aid in manipulating GSoC program data.
  """

  def __init__(self, **kwargs):
    """Initializes the GSoCProgramHelper.
    """
    super(GSoCProgramHelper, self).__init__(**kwargs)

  def createProgram(self, override={}):
    """Creates a program for the defined properties.
    """
    if self.program:
      return self.program
    super(GSoCProgramHelper, self).createProgram()

    self.program = seedGSoCProgram(sponsor_key=self.sponsor.key(), **override)

    return self.program

  def createNewOrg(self, override={}):
    """Creates a new organization for the defined properties.

    This new organization will not be stored in self.org but returned.
    """
    if not self.program:
      self.createProgram()
    return org_utils.seedSOCOrganization(self.program.key(), **override)

  def createOrgApp(self, override={}):
    """Creates an organization application for the defined properties.
    """
    override.update({
        'key_name': 'gsoc_program/%s/orgapp' % self.program.key().name(),
        'survey_start': timeline_utils.past(),
        'survey_end': timeline_utils.future(),
        })
    return super(GSoCProgramHelper, self).createOrgApp(override)


class GCIProgramHelper(ProgramHelper):
  """Helper class to aid in manipulating GCI program data.
  """

  def __init__(self, **kwargs):
    """Initializes the GCIProgramHelper.
    """
    super(GCIProgramHelper, self).__init__(**kwargs)

  def createProgram(self, override={}):
    """Creates a program for the defined properties.
    """
    if self.program:
      return self.program
    super(GCIProgramHelper, self).createProgram()

    self.program = seedGCIProgram(sponsor_key=self.sponsor.key(), **override)

    return self.program

  def createNewOrg(self, override={}):
    """Creates a new organization for the defined properties.

    This new organization will not be stored in self.org but returned.
    """
    super(GCIProgramHelper, self).createNewOrg(override)
    properties = {
        'scope': self.program,
        'status': 'active',
        'home': None,
        'task_quota_limit': 100,
        'backup_winner': None,
        'program': self.program,
        }
    properties.update(override)
    return self.seed(GCIOrganization, properties)

  def createOrgApp(self, override={}):
    """Creates an organization application for the defined properties.
    """
    override.update({
        'key_name': 'gci_program/%s/orgapp' % self.program.key().name(),
        })
    return super(GCIProgramHelper, self).createOrgApp(override)
