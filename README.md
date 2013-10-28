IntegralGit
===========
Simple continuous integration/deployment server for Github/Bitbucket hosted repositories

Uses Flask and uWSGI

Setup:
-----
http://flask.pocoo.org/docs/deploying/uwsgi/#starting-your-app-with-uwsgi

Configuration:
--------------
Add a POST service hook on your repositories of choice for http://your-integralgit-server/update

Set up your repository:
* Make a new empty branch named integralgit

```
git checkout --orphan integralgit
git rm -rf .
```

* Make a json file named config formatted like so:

```JSON
{
	"hostgroups" : {
		"group-name" : [
			"host1",
		  "host2",
			"host3"
		],
		"another-group-name" : [
			"host"
		]
	},
	"configs" : {
		"base" : {
			"location" : "/absolute/path/to/repo/location",
			"script" : "./script-in-repo.sh",
			"branch" : "branch-you-want-checked-out",
			"remote" : "usually-origin-but-if-you're-a-special-snowflake-you-can-change-this"
		},
		"group-name" : {
			"location" : "/special/repo/location/for/hosts/in/this/group"
		},
		"another-group-name" : {
			"branch" : "if-this-group-was-your-test-fleet-you'd-want-it-to-use-your-dev-branch-instead-of-master"
		},
		"host3" : {
      "script" : "/host/3/is/also/a/special/snowflake.sh"
    }
  }
}
```

* Push this config up to your repo:

```
git commit -a -m "Config"
git push -u origin integralgit
```

* That's it! IntegralGit should pull your config changes automatically and use them for future push events.

Configuration Information:
--------------------------
* `location`: You MUST specify this, otherwise IntegralGit will be confused.
* `script`: If you do not specify a script, IntegralGit will just pull your updated changes.
* `branch`: Defaults to 'master'
* `remote`: Defaults to 'origin'
* The final host configuration is the union of base, all hostgroups containing the host (applied alphabetically), and the host-specific config. Values can be set in one config and overridden in a config applied later.

Using IntegralGit:
-----------------
* For the most part, IntegralGit should silently do whatever you want it to.
* Visiting http://your-integralgit-server/repo-name will provide information on commits to the repository since IntegralGit was last restarted.

Notes/WIP:
---------
* IntegralGit is confused by merge conflicts on pull. If you are working on your IntegralGit box, please ensure that any upstream changes will apply without conflict, or manually pull and resolve the conflicts.
* Log information is written to integralgit.log
* Host groups are 200% untested. If they don't seem to work, it is probably my fault.
* Currently your repo information is a json blob.

