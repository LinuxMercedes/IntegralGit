from flask import Flask, request
from pprint import pprint
import re
import json
import ConfigParser
import urllib2
import network
import os
import subprocess
import socket


def bitbucket(json):
  ret = {}
  ret['url'] = json['canon_url'] + json['repository']['absolute_url']
  ret['raw'] = ret['url'] + 'raw/'
  ret['config'] = ret['raw'] + 'integralgit/config'
  ret['name'] = json['repository']['name']
  ret['commits'] = [{'message' : j['message'], 'branch': j['branch'], 'time': j['timestamp']} for j in json['commits']]

  return ret

def github(json):
  ret = {}
  ret['url'] = json['repository']['url']
  ret['raw'] = re.sub('github', 'raw.github', ret['url'], 1) + '/'
  ret['config'] =  ret['raw'] + 'integralgit/config'
  ret['name'] = json['repository']['name']
  ret['commits'] = []
  for j in json['commits']:
    d = {'message' : j['message'], 'time' : j['timestamp']}
    d['branch'] = re.sub(r'([^\/])$', r'\1', json['ref'])
    ret['commits'].append(d)

  return ret

def shellescape(s):
  return s.replace("\\", "\\\\").replace("'", "'\\''")

def log(s, level = 0):
  logfile.write(str(s))
  logfile.write("\n")
  logfile.flush()
  print s

sources = {
    ('131.103.20.165', 1) : bitbucket,
    ('131.103.20.166', 1) : bitbucket,
    ('204.232.175.64', 27) : github,
    ('192.30.252.0', 22) : github,
  }

app = Flask(__name__)
state = {}

logfile = open('integralgit.log', 'a')

log('Starting up...')

@app.route("/")
def hello():
  return "IntegralGit: continuous integration via GitHub"

@app.route("/<repo>")
def latest(repo):
  log('wtf')
  return str(state.get(repo, "I don't recognize that repo name. Try committing something to it?"))

@app.route("/update", methods=["POST"])
def update():
  # Prevent requests from hosts we don't recognize
  source = request.remote_addr
  log('source: ' + str(source))
  decoder = None
  for n, d in sources.iteritems():
    if network.isAddressInNetwork(source, *n):
      decoder = d
      break
  else:
    return "Unrecognized source IP"

  jd = json.JSONDecoder()
  payload = jd.decode(request.form['payload'])
  info = decoder(payload)
  log(info)
  repo = info['name']
  url = info['url']
  state[repo] = info

  try:
    getConfigs(info)
    gitPull(info)
  except Exception as e:
    # Skip running host script...lessens chance of RCE
    return str(e)

  runHostScript(repo, owner)

  return "Good job"

# Get host configuration file from the integralgit branch
def getConfigs(info):
  config_data = None
  log('Host config location: ' + str(info['config']))
  try:
    page = urllib2.urlopen(info['config'])
    config_data = page.read()
    page.close()
  except:
    log("Host Config not found, quitting.")
    raise Exception("Could not load host config")

  jd = json.JSONDecoder()
  info['config'] = jd.decode(config_data)
  info['hostconfig'] = getHostConfig(info)

# Get specific host configuration
# by applying a base config (if it exists),
# applying configs for hostgroups in alphabetical order,
# then applying host-specific configs.
def getHostConfig(info):
  hostname = socket.gethostname()

  # get base config
  config = info['config'].get('configs',{}).get('base',{})

  # get hostgroup configs
  for group, hosts in iter(sorted(info['config'].get('groups', {}).iteritems())):
    if hostname in hosts:
      config.update(info['config'].get('configs', {}).get(group, {}))

  # get host specific config
  config.update(info['config'].get('configs', {}).get(hostname, {}))

  log('Host config:')
  log(config)

  return config

def gitPull(info):
# Build repo folder
  repoFolder = info['hostconfig']['location']
  if repoFolder is None:
    log("No location found for repository!")
    raise Exception("No location found!")

  log("Checking if " + repoFolder + " is a git repository...")

  # Check for folder
  if(os.path.isdir(repoFolder)):
    # Check for git repo
    result = subprocess.call(['git', 'rev-parse'], cwd=repoFolder)
    if(result != 0):
      log("Folder exists but is not a git repository. Fix your shit.")
      raise Exception("Not a git repository")

    branch = info['hostconfig'].get('branch', 'master')
    remote = info['hostconfig'].get('remote', 'origin')

    # If local branch exists, checkout and pull
    result = subprocess.call(['git', 'show-branch', branch], cwd=repoFolder)
    if result == 0:
      log("Checking out branch...")
      result = subprocess.call(['git', 'checkout', branch], cwd=repoFolder)
      log("Checkout result: " + str(result))
      log("Doing git pull...")
      result = subprocess.call(['git', 'pull'], cwd=repoFolder)
      log("Pull result: " + str(result))

    # Local branch does not exist, fetch and track remote branch
    else:
      log("Local branch does not exist...")
      log("Doing git fetch...")
      result = subprocess.call(['git', 'fetch'], cwd=repoFolder)
      log("Fetch result: " + str(result))
      log("Checking out branch...")
      result = suprocess.call(['git', 'checkout', '--track', remote + '/' + branch], cwd=repoFolder)
      log("Checkout result: " + str(result))

  # Repo does not exist at all, clone and checkout
  else:
    log("Folder does not exist; doing git clone...")
    cloneURL = "git@github.com:" + repoOwner + "/" + repoName + ".git"
    result = subprocess.call(['git', 'clone', info['url']], cwd=os.path.basename(repoFolder))
    log("Clone result: " + str(result))
    log("Checking out local branch...")
    result = subprocess.call(['git', 'checkout', '-b', branch, remote + '/' + branch], cwd=repoFolder)
    log("Checkout result: " + str(result))

def runHostScript(info):
  script_name = info['hostconfig']['script']
  repo_folder = info['hostconfig']['location']

  if(script_name is not None):
    script_path = os.path.join(repo_folder, script_name)
    log("Got script file for host: " + str(script_path))

    log("Running script...")
    subprocess.call(['chmod', '+x', script_path])
    result = subprocess.call([script_path], cwd = repo_folder)
    log("Script result: " + str(result))

def parseConfig(filename):
  config = ConfigParser.SafeConfigParser()
  config.read(filename)

  for section in config.sections():
    lastCommit[section] = "No recorded commits!"

if __name__=="__main__":
  app.run(host="0.0.0.0", debug=True)

