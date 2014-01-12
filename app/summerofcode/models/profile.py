# Copyright 2014 the Melange authors.
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

"""This module contains the Summer Of Code-specific profile related models."""

from google.appengine.ext import ndb

from melange.models import profile as profile_model


class SOCStudentData(profile_model.StudentData):
  """Model that represents Summer Of Code-specific student information to be
  associated with the specified profile.
  """

  #: Number of proposals which have been submitted by the student.
  number_of_proposals = ndb.IntegerProperty(required=True, default=0)

  #: Number of projects which have been assigned to the student.
  #: Note that right now at most one project per student is supported.
  number_of_projects = ndb.IntegerProperty(required=True, default=0)

  #: Total number of project evaluations that have been passed by the student
  #: for all the projects that have been assigned to him or her.
  number_of_passed_evaluations = ndb.IntegerProperty(required=True, default=0)

  #: Total number of project evaluations that have been failed by the student
  #: for all the projects that have been assigned to him or her.
  number_of_failed_evaluations = ndb.IntegerProperty(required=True, default=0)

  #: List of organizations for which the student have been assigned a project.
  project_for_orgs = ndb.KeyProperty(repeated=True)

  #: Property pointing to the Blob storing student's tax form.
  tax_form = ndb.BlobKeyProperty()

  #: Property pointing to the Blob storing student's enrollment form.
  enrollment_form = ndb.BlobKeyProperty()
