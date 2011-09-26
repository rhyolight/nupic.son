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

"""Module containing the boiler plate required to construct templates
"""

__authors__ = [
  '"Daniel Hans" <daniel.m.hans@gmail.com>',
  ]


from soc.views import forms


class GSoCModelForm(forms.ModelForm):
  """Django ModelForm class which uses our implementation of BoundField.
  """
  
  def __init__(self, *args, **kwargs):
    super(forms.ModelForm, self).__init__(GSoCBoundField, *args, **kwargs)


class GSoCBoundField(forms.BoundField):
  """GSoC specific BoundField representation.
  """
  pass
