#!/usr/bin/env python2.5
#
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

"""The survey conversion updates are defined in this module.
"""

__authors__ = [
    '"Lennard de Rijk" <ljvderijk@gmail.com>',
  ]


import logging

from django import http
from django.conf.urls.defaults import url

from google.appengine.api import taskqueue
from google.appengine.ext import db

from soc.tasks.helper import error_handler

from soc.modules.gsoc.models.grading_project_survey_record import \
    GSoCGradingProjectSurveyRecord
from soc.modules.gsoc.models.grading_project_survey_record import \
    GradingProjectSurveyRecord
from soc.modules.gsoc.models.grading_record import GSoCGradingRecord
from soc.modules.gsoc.models.grading_record import GradingRecord
from soc.modules.gsoc.models.grading_survey_group import GradingSurveyGroup
from soc.modules.gsoc.models.grading_survey_group import GSoCGradingSurveyGroup
from soc.modules.gsoc.models.project import GSoCProject
from soc.modules.gsoc.models.project_survey_record import \
    GSoCProjectSurveyRecord
from soc.modules.gsoc.models.project_survey_record import ProjectSurveyRecord


class ProjectSurveyRecordConversion(object):
  """Tasks for converting (Grading)ProjectSurveyRecords into their GSoC
  counterparts. Must be run BEFORE the other conversions in this module.
  """

  # number of records to convert in one go
  BATCH_SIZE = 25

  def djangoURLPatterns(self):
    """Returns the URL patterns for the tasks in this module
    """
    patterns = [
        url(r'tasks/gsoc/convert_surveys/project_survey_record',
            self.convertProjectSurveyRecords),
        url(r'tasks/gsoc/convert_surveys/grading_project_survey_record',
            self.convertGradingProjectSurveyRecords),
        ]
    return patterns

  def convertProjectSurveyRecords(self, request, *args, **kwargs):
    """Converts ProjectSurveyRecords into GSoCProjectSurveyRecords.
    """
    return self._convertProjectSurveyRecord(request, ProjectSurveyRecord,
                                            GSoCProjectSurveyRecord)

  def convertGradingProjectSurveyRecords(self, request, *args, **kwargs):
    """Converts GradingProjectSurveyRecords into
    GSoCGradingProjectSurveyRecords.
    """
    return self._convertProjectSurveyRecord(
        request, GradingProjectSurveyRecord, GSoCGradingProjectSurveyRecord)

  def _convertProjectSurveyRecord(self, request, from_model, to_model):
    """Converts a set of SurveyRecords that is tied to a Project.

    Args:
      request: The HTTPRequest object for this task
      from_model: Model class of the record to convert from.
      to_model: Model class of the record to conver to.
    """
    post_dict = request.POST

    q = from_model.all()

    cursor = post_dict.get('cursor')
    if cursor:
      cursor = str(cursor)
      q.with_cursor(cursor)

    records = q.fetch(ProjectSurveyRecordConversion.BATCH_SIZE)

    if not records:
      # we are done, return OK
      return http.HttpResponse()

    new_records = []

    for record in records:
      values = toValueDict(record)

      # update the project value to a GSoCProject
      values['project'] = getGSoCProjectFor(record.project)

      new_records.append(to_model(**values))

    def txn():
      task_params = {'cursor': unicode(q.cursor())}
      new_task = taskqueue.Task(params=task_params, url=request.path)
      new_task.add(transactional=True)
      db.put(new_records)

    db.RunInTransaction(txn)

    # return OK
    return http.HttpResponse()


class GradingSurveyGroupConversion(object):
  """Task for converting GradingSurveyGroup to GSoCGradingSurveyGroup.
  """

  def djangoURLPatterns(self):
    """Returns the URL patterns for the tasks in this module
    """
    patterns = [
        url(r'tasks/gsoc/convert_surveys/grading_survey_group',
            self.convertGradingSurveyGroups),
        ]
    return patterns

  def convertGradingSurveyGroups(self, request, *args, **kwargs):
    """Converts a set of GradingSurveyGroups.

    Args:
      request: The HTTPRequest object for this task
    """
    post_dict = request.POST

    q = GradingSurveyGroup.all()

    cursor = post_dict.get('cursor')
    if cursor:
      cursor = str(cursor)
      q.with_cursor(cursor)

    group = q.get()

    if not group:
      # we are done, return OK
      return http.HttpResponse()

    # The new group should have a program property instead of scope since it
    # is no longer a Linkable.
    values = toValueDict(group)
    values['program'] = group.scope

    # Values like scope will be ignored as keyword arguments for GSoCGSG
    # automatically.
    new_group = GSoCGradingSurveyGroup(**values)

    def txn():
      new_group.put()
      task_params = {'cursor': unicode(q.cursor())}
      new_task = taskqueue.Task(params=task_params, url=request.path)
      new_task.add(transactional=True)

      # Start a GradingRecord conversion task for the new group
      task_params = {'old_group': group.key().id_or_name(),
                     'new_group': new_group.key().id_or_name()}
      new_task = taskqueue.Task(
          params=task_params, url='/tasks/gsoc/convert_surveys/grading_record')
      new_task.add(transactional=True)

    db.RunInTransaction(txn)

    # return OK
    return http.HttpResponse()

class GradingRecordConversion(object):
  """Task for converting GradingRecord to GSoCGradingRecord.
  """

  def djangoURLPatterns(self):
    """Returns the URL patterns for the tasks in this module
    """
    # Note that if this pattern is changed it should be changed in
    # the GSGConversion above as well.
    patterns = [
        url(r'tasks/gsoc/convert_surveys/grading_record',
            self.convertGradingRecord),
        ]
    return patterns

  def convertGradingRecord(self, request, *args, **kwargs):
    """Converts a GradingRecord into a GSoCGradingRecord.

    Args:
      request: The HTTPRequest object for this task
    """
    post_dict = request.POST

    if not(post_dict.get('old_group') and post_dict.get('new_group')):
      return error_handler.logErrorAndReturnOK(
          'To convert a GradingRecord the key to the old and new '
          'GradingSurveyGroup need to be present, current POST contains %s' %
          post_dict)

    old_group = GradingSurveyGroup.get_by_key_name(post_dict.get('old_group'))
    if not old_group:
      return error_handler.logErrorAndReturnOK(
          '%s is not a valid GradingSurveyGroup key' %
          post_dict.get('old_group'))

    new_group = GSoCGradingSurveyGroup.get_by_id(
        int(post_dict.get('new_group')))

    if not new_group:
      return error_handler.logErrorAndReturnOK(
          '%s is not a valid GSoCGradingSurveyGroup id' %
          post_dict.get('new_group'))

    q = GradingRecord.all()
    q.filter('grading_survey_group', old_group)

    cursor = post_dict.get('cursor')
    if cursor:
      cursor = str(cursor)
      q.with_cursor(cursor)

    old_record = q.get()

    if not old_record:
      # we are done
      return http.HttpResponse()

    values = toValueDict(old_record)
    values['grading_survey_group'] = new_group

    if old_record.mentor_record:
      old_mentor_record = old_record.mentor_record
      mentor_record_q = GSoCGradingProjectSurveyRecord.all()
      mentor_record_q.filter('survey', old_mentor_record.survey)
      mentor_record_q.filter('project', old_mentor_record.project)
      values['mentor_record'] = mentor_record_q.get()

    if old_record.student_record:
      old_student_record = old_record.student_record
      student_record_q = GSoCProjectSurveyRecord.all()
      student_record_q.filter('survey', old_student_record.survey)
      student_record_q.filter('project', old_student_record.project)
      values['student_record'] = student_record_q.get()

    # Create a new record where the parent is now the project for transactional
    # reasons.
    project = getGSoCProjectFor(old_record.project)
    new_record = GSoCGradingRecord(parent=project, **values)

    def txn():
      new_record.put()

      # done inside transaction to make sure new_record has a key
      if old_record.key() in project.passed_evaluations:
        project.passed_evaluations.remove(old_record.key())
        project.passed_evaluations.append(new_record.key())
      elif old_record.key() in project.failed_evaluations:
        project.failed_evaluations.remove(old_record.key())
        project.failed_evaluations.append(new_record.key())

      project.put()

      task_params = {
          'cursor': unicode(q.cursor()),
          'old_group': post_dict.get('old_group'),
          'new_group': post_dict.get('new_group')}
      new_task = taskqueue.Task(params=task_params, url=request.path)
      new_task.add(transactional=True)

    db.RunInTransaction(txn)

    # return OK
    return http.HttpResponse()

def toValueDict(entity):
  """Takes an entity and puts its properties into a dictionary.
  """
  values = {}
  for prop in entity.properties().keys() + entity.dynamic_properties():
    values[prop] = getattr(entity, prop)
  return values


def getGSoCProjectFor(project):
  """Given a StudentProject returns the GSoCProject entity that represents the
  project in the new system.

  Args:
    project: StudentProject entity.

  Returns:
    The GSoCProject entity that was created from the given Project.
  """
  student = project.student
  q = GSoCProject.all()
  q.ancestor(student)
  return q.get()
