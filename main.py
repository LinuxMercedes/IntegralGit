from flask import Flask, request
from pprint import pprint
import json
import ConfigParser

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
  lastCommit[repo] = payload['commits'][0]['message']
  return ""

def parseConfig(filename):
  config = ConfigParser.SafeConfigParser()
  config.read(filename)

  for section in config.sections():
    lastCommit[section] = "No recorded commits!"

if __name__=="__main__":
  app.run(host="0.0.0.0", debug=True)
