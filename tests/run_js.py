#!/usr/bin/env python2.7
import subprocess

subprocess.call("./bin/node ./node_modules/testem/testem.js ci", shell=True)
