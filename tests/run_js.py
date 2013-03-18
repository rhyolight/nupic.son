#!/usr/bin/env python2.7
import subprocess
import os

_environ = os.environ.copy()
_environ["PATH"] += ':./node_modules/phantomjs/lib/phantom/bin'

subprocess.call("./bin/node ./node_modules/testem/testem.js ci", env=_environ, shell=True)
