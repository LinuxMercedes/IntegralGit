from flask import Flask, request
from pprint import pprint
import json

app = Flask(__name__)
lastCommit = "No recorded commits!"

@app.route("/")
def hello():
  return "IntegralGit: continuous integration via GitHub"

@app.route("/update", methods=["POST"])
def update():
  print json.dumps(request.form['payload'])
  return

if __name__=="__main__":
  app.run(host="0.0.0.0", debug=True)
