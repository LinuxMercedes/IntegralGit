from flask import Flask, request
from pprint import pprint
import re
import json
import ConfigParser
import urllib2

import os
import subprocess
import socket

app = Flask(__name__)
lastCommit = {}

def bitbucket(json):
  ret = {}
  ret['url'] = json['canon_url'] + json['repository']['absolute_url']
  ret['name'] = json['repository']['name']
  ret['commits'] = [{'message' : j['message'], 'branch': j['branch'], 'time': j['timestamp']} for j in json['commits']]

  return ret

def github(json):
  ret = {}
  ret['url'] = json['repository']['url']
  ret['name'] = json['repository']['name']
  ret['commits'] = []
  for j in json['commits']:
    d = {'message' : j['message'], 'time' : j['timestamp']}
    d['branch'] = re.sub(r'([^\/])$', r'\1', json['ref'])
    ret['commits'].append(d)

  return ret

sources = {
    ('131.103.20.165', 1) : bitbucket,
    ('131.103.20.166', 1) : bitbucket,
    ('204.232.175.64', 27) : github,
    ('192.30.252.0', 22) : github,
  }


repoLocation = "/home/ubuntu/src"

def shellescape(s):
  return s.replace("\\", "\\\\").replace("'", "'\\''")

def log(s, level = 0):
  print s

def repofolder(repo):
  return repoLocation + "/" + shellescape(repo) + "/"

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
#  owner = payload['repository']['owner']['name']
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
  repoFolder = repofolder(repoName)
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

def runHostScript(repo, owner):
  base_url = "https://raw.github.com/" + owner + "/" + repo
  config_url = base_url + "/master/hostconfig"

  log("Host Config url:" + config_url)

  config_data = ''

  try:
    page = urllib2.urlopen(config_url)
    config_data = page.read()
    page.close()
  except:
    log("Host Config not found, quitting.")
    return

  log("Got host config, parsing...")
  jd = json.JSONDecoder()
  config = jd.decode(config_data)

  script_name = config[socket.gethostname()]['script']

  if(script_name is not None):
    log("Got script file for host: " + str(script_name))
    script_url = base_url + "/master/" + script_name

    try:
      page = urllib2.urlopen(script_url)
      script_data = page.read()
      page.close()
    except:
      log("Host Script not found, quitting.")
      return

    script_file = '/tmp/' + shellescape(repo) + '-' + str(os.getpid())

    log("Gost Host Script, writing to:" + script_file)

    with open(script_file, "wb") as script_fh:
      script_fh.write(script_data)

    log("Running script...")
    subprocess.call(['chmod', '+x', script_file])
    result = subprocess.call([script_file], cwd = repofolder(repo))
    log("Script result: " + str(result))

def parseConfig(filename):
  config = ConfigParser.SafeConfigParser()
  config.read(filename)

  for section in config.sections():
    lastCommit[section] = "No recorded commits!"

if __name__=="__main__":
  app.run(host="0.0.0.0", debug=True)
