#!/usr/bin/env python2.7
import subprocess
import os

_environ = dict(os.environ)
os.environ["PATH"] += os.environ["PATH"] + ':./node_modules/phantomjs/lib'
subprocess.call("./bin/node ./node_modules/testem/testem.js ci", shell=True)
os.environ.clear()
os.environ.update(_environ)
