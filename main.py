from flask import Flask, request
from pprint import pprint
import re
import json
import ConfigParser
import urllib2

import os
import subprocess

app = Flask(__name__)
lastCommit = {}
repoLocation = "/home/ubuntu/src"

def shellescape(s):
  return s.replace("\\", "\\\\").replace("'", "'\\''")

def log(s, level = 0):
  print s

@app.route("/")
def hello():
  return "IntegralGit: continuous integration via GitHub"

@app.route("/<repo>")
def latest(repo):
  return lastCommit.get(repo, "I don't recognize that repo name. Try committing something to it?")

@app.route("/update", methods=["POST"])
def update():
  jd = json.JSONDecoder()
  payload = jd.decode(request.form['payload'])
  repo = payload['repository']['name']
  owner = payload['repository']['owner']['name']
  lastCommit[repo] = payload['commits'][-1]['message']

  try:
    gitPull(repo, owner)
  except Exception as e:
    # Skip running host script...lessens chance of RCE
    return str(e)

  runHostScript(repo, owner)

  return "Good job"

def gitPull(repoName, repoOwner):
# Build repo folder
  repoFolder = repoLocation + "/" + shellescape(repoName) + "/"
  log("Checking if " + repoFolder + " is a git repository...")

  # Check for folder
  if(os.path.isdir(repoFolder)):
    # Check for git repo
    result = subprocess.call(['git', 'rev-parse'], cwd=repoFolder)
    if(result != 0):
      log("Folder exists but is not a git repository. Fix your shit.")
      raise Exception("Not a git repository")

    # Pull
    log("Doing git pull...")
    result = subprocess.call(['git', 'pull'], cwd=repoFolder)
    log("Pull result: " + str(result))
  
  else:
    log("Folder does not exist; doing git clone...")
    cloneURL = "git@github.com:" + repoOwner + "/" + repoName + ".git"
    result = subprocess.call(['git', 'clone', cloneURL], cwd=repoLocation)
    log("Clone result: " + str(result))

def runHostScript(repoName, repoOwner):
  url = "https://raw.github.com/" + repoOwner + "/" + "repoName" + "/master/hostScript"

  log("Host Script url:" + url)

  page = urllib2.urlopen(url)
  script_data = page.read()
  page.close()

  with open("deploy.sh", "wb") as background:
    background.write(script_data)

def parseConfig(filename):
  config = ConfigParser.SafeConfigParser()
  config.read(filename)

  for section in config.sections():
    lastCommit[section] = "No recorded commits!"

if __name__=="__main__":
  app.run(host="0.0.0.0", debug=True)
