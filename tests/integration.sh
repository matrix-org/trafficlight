#!/bin/bash

# Ask for info for two clients

echo -n "foo # " && curl -X POST -H 'Content-Type: application/json' http://localhost:5000/client/foo/register -d '{"type": "element-web", "version": "0.15.0"}'

echo "Check UI" && read

echo -n "bar # " && curl -X POST -H 'Content-Type: application/json' http://localhost:5000/client/bar/register -d '{"type": "element-android", "version": "0.15.0"}'

echo "Started test..." && read

echo -n "baz # " && curl -X POST -H 'Content-Type: application/json' http://localhost:5000/client/baz/register -d '{"type": "element-android", "version": "0.15.0"}'

echo -n "baz < " && curl http://localhost:5000/client/baz/poll

# walk through the steps...

echo -n "foo < " && curl http://localhost:5000/client/foo/poll
# register


echo -n "foo > " && curl -XPOST -H 'Content-Type: application/json' -d '{"response": "registered"}' http://localhost:5000/client/foo/respond

echo -n "bar < " && curl http://localhost:5000/client/bar/poll
# login

echo -n "bar > " && curl -XPOST -H 'Content-Type: application/json' -d '{"response": "loggedin"}' http://localhost:5000/client/bar/respond

echo -n "foo < " && curl http://localhost:5000/client/foo/poll
# foo should idle
echo -n "bar < " && curl http://localhost:5000/client/bar/poll
# bar should request cross signing

echo -n "bar > " && curl -XPOST -H 'Content-Type: application/json' -d '{"response": "started_crosssign"}' http://localhost:5000/client/bar/respond

echo -n "foo < " && curl http://localhost:5000/client/foo/poll
echo -n "bar < " && curl http://localhost:5000/client/bar/poll


# Foo accepts the cross signing request
echo -n "foo > " && curl -XPOST -H 'Content-Type: application/json' -d '{"response": "accepted_crosssign"}' http://localhost:5000/client/foo/respond

echo -n "foo < " && curl http://localhost:5000/client/foo/poll
echo -n "bar < " && curl http://localhost:5000/client/bar/poll

# Both verify emoji
echo -n "bar > " && curl -XPOST -H 'Content-Type: application/json' -d '{"response": "verified_crosssign"}' http://localhost:5000/client/bar/respond

echo -n "foo < " && curl http://localhost:5000/client/foo/poll
echo -n "bar < " && curl http://localhost:5000/client/bar/poll


echo -n "foo > " && curl -XPOST -H 'Content-Type: application/json' -d '{"response": "verified_crosssign"}' http://localhost:5000/client/foo/respond


echo -n "foo < " && curl http://localhost:5000/client/foo/poll
echo -n "bar < " && curl http://localhost:5000/client/bar/poll
