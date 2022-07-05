# Ask for info for two clients

# These get the command to 'ready'
echo -n "foo: " && curl http://localhost:5000/client/foo/poll
echo -n "bar: " && curl http://localhost:5000/client/bar/poll
# This one gets 'be idle'
echo -n "baz: " && curl http://localhost:5000/client/baz/poll

# Ready up

curl -XPOST -H 'Content-Type: application/json' -d '{"response": "ready"}' http://localhost:5000/client/foo/respond
curl -XPOST -H 'Content-Type: application/json' -d '{"response": "ready"}' http://localhost:5000/client/bar/respond

echo -n "foo: " && curl http://localhost:5000/client/foo/poll
echo -n "bar: " && curl http://localhost:5000/client/bar/poll


curl -XPOST -H 'Content-Type: application/json' -d '{"response": "started_crosssign"}' http://localhost:5000/client/foo/respond

echo -n "foo: " && curl http://localhost:5000/client/foo/poll
echo -n "bar: " && curl http://localhost:5000/client/bar/poll


curl -XPOST -H 'Content-Type: application/json' -d '{"response": "accepted_crosssign"}' http://localhost:5000/client/bar/respond

echo -n "foo: " && curl http://localhost:5000/client/foo/poll
echo -n "bar: " && curl http://localhost:5000/client/bar/poll

curl -XPOST -H 'Content-Type: application/json' -d '{"response": "verified_crosssign"}' http://localhost:5000/client/bar/respond

echo -n "foo: " && curl http://localhost:5000/client/foo/poll
echo -n "bar: " && curl http://localhost:5000/client/bar/poll


curl -XPOST -H 'Content-Type: application/json' -d '{"response": "verified_crosssign"}' http://localhost:5000/client/foo/respond


echo -n "foo: " && curl http://localhost:5000/client/foo/poll
echo -n "bar: " && curl http://localhost:5000/client/bar/poll
