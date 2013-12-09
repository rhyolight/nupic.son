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

"""Downloads student forms."""

import optparse
import os
import shutil

import interactive

parser = optparse.OptionParser(usage="usage: %prog [options] app_id")
parser.add_option("-o", "--output", dest="outputdir", default="forms",
                  help="write files to target DIR", metavar="DIR")
# TODO(nathaniel): Make program a required rather than optional parameter.
parser.add_option('-p', '--program', dest='program_path', default='',
                  help='full key name of the program', metavar='DIR')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


def downloadStudentForms(options):
  # TODO(nathaniel): Get these imports at top-level just like any others.
  from google.appengine.ext import db
  from soc.views.helper import lists
  from soc.modules.gsoc.models import profile
  from soc.modules.gsoc.models import program as program_model

  if not options.program_path:
    print '--program_path or -p option is required'
  program = program_model.GSoCProgram.get_by_key_name(options.program_path)

  def QueryGen():
    query = profile.GSoCStudentInfo.all()
    query.filter('number_of_projects', 1)
    query.filter('program', program)
    return query

  outputdir = os.path.abspath(options.outputdir)

  if not os.path.exists(outputdir):
    os.mkdir(outputdir)

  if not os.path.isdir(outputdir):
    print "Could not create output dir: %s" % outputdir

  print "Fetching StudentInfo..."
  students = list(i for i in interactive.deepFetch(QueryGen) if i.tax_form)

  keys = lists.collectParentKeys(students)
  keys = list(set(keys))

  prefetched = {}

  print "Fetching Profile..."

  for i in xrange(0, len(keys), 100):
    chunk = keys[i:i+100]
    entities = db.get(chunk)
    prefetched.update(dict((i.key(), i) for i in entities if i))

  lists.distributeParentKeys(students, prefetched)

  countries = ['United States']
  us_students = [i for i in students if i.parent().res_country in countries]

  for student in us_students:
    form = student.tax_form
    _, ext = os.path.splitext(form.filename)
    path = os.path.join(outputdir, student.parent().link_id + ext)
    dst = open(path, "w")
    src = form.open()
    shutil.copyfileobj(src, dst)
    print "Downloading form to '%s'..." % path

  print 'Done.'


def main():
  options, args = parser.parse_args()

  if len(args) < 1:
    parser.error("Missing app_id")

  if len(args) > 1:
    parser.error("Too many arguments")

  interactive.setup()
  interactive.setupRemote(args[0])

  downloadStudentForms(options)


if __name__ == '__main__':
  main()
