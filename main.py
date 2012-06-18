from flask import Flask, request
from pprint import pprint
import json
import ConfigParser
import urllib2

app = Flask(__name__)
lastCommit = {}

@app.route("/")
def hello():
  return "IntegralGit: continuous integration via GitHub"

@app.route("/<repo>")
def latest(repo):
  return lastCommit.get(repo, "I don't recognize that repo name. Try committing something to it?")

@app.route("/update", methods=["POST"])
def update():
  payload = json.dumps(request.form['payload'])
  repo = payload['repository']['name']
  owner = payload['repository']['owner']['name']
  lastCommit[repo] = payload['commits'][-1]['message']

  url = "https://raw.github.com/" + owner + "/" + repo + "/master/bot.py"
  page = urllib2.urlopen(url)
  script_data = page.read()
  page.close()

  with open("deploy.sh", "wb") as background:
    background.write(script_data)

  return ""

def parseConfig(filename):
  config = ConfigParser.SafeConfigParser()
  config.read(filename)

  for section in config.sections():
    lastCommit[section] = "No recorded commits!"

if __name__=="__main__":
  app.run(host="0.0.0.0", debug=True)
