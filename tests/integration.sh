#!/bin/bash

# This bash script has been used to create and register client_types, and force them through a simple flow.

# It doesn't do anything like validate the steps make sense, etc, and will generally not work if other client_types are registered.

# It's probably a not unreasonable place to hack around with client_types to get the server into a specific condition; but fairly soon tests will need to be more complicated.

DEBUG=DEBUG
RUN=`date +%s`
FOO=foo_$RUN
BAR=bar_$RUN
echo -n "$FOO # " && curl -X POST -H 'Content-Type: application/json' http://localhost:5000/client/$FOO/register -d '{"type": "element-web", "version": "0.15.0"}'

echo "Check UI" && read

echo -n "$BAR # " && curl -X POST -H 'Content-Type: application/json' http://localhost:5000/client/$BAR/register -d '{"type": "element-android", "version": "0.15.0"}'

echo "Started test..." && read

if [[ "DEBUG" == "$DEBUG" ]]; then echo "DEBUG?" && read ; fi;

# walk through the steps...


(echo -n "$FOO < " && curl -s http://localhost:5000/client/$FOO/poll | grep 'register' ) && echo "FOO is RED" && RED=$FOO && GREEN=$BAR

(echo -n "$BAR < " && curl -s http://localhost:5000/client/$BAR/poll | grep 'register' ) && echo "BAR is RED" && RED=$BAR && GREEN=$FOO

echo -n "$RED < " && curl http://localhost:5000/client/$RED/poll
echo -n "$GREEN < " && curl http://localhost:5000/client/$GREEN/poll

echo -n "$RED > " && curl -XPOST -H 'Content-Type: application/json' -d '{"response": "registered"}' http://localhost:5000/client/$RED/respond
if [[ "DEBUG" == "$DEBUG" ]]; then echo "DEBUG?" && read ; fi;

echo -n "$GREEN < " && curl http://localhost:5000/client/$GREEN/poll
# login

echo -n "$GREEN > " && curl -XPOST -H 'Content-Type: application/json' -d '{"response": "loggedin"}' http://localhost:5000/client/$GREEN/respond
if [[ "DEBUG" == "$DEBUG" ]]; then echo "DEBUG?" && read ; fi;

echo -n "$RED < " && curl http://localhost:5000/client/$RED/poll
# $RED should idle
echo -n "$GREEN < " && curl http://localhost:5000/client/$GREEN/poll
# $GREEN should request cross signing

echo -n "$GREEN > " && curl -XPOST -H 'Content-Type: application/json' -d '{"response": "started_crosssign"}' http://localhost:5000/client/$GREEN/respond
if [[ "DEBUG" == "$DEBUG" ]]; then echo "DEBUG?" && read ; fi;
echo -n "$RED < " && curl http://localhost:5000/client/$RED/poll
echo -n "$GREEN < " && curl http://localhost:5000/client/$GREEN/poll


# Foo accepts the cross signing request
echo -n "$RED > " && curl -XPOST -H 'Content-Type: application/json' -d '{"response": "accepted_crosssign"}' http://localhost:5000/client/$RED/respond
if [[ "DEBUG" == "$DEBUG" ]]; then echo "DEBUG?" && read ; fi;

echo -n "$RED < " && curl http://localhost:5000/client/$RED/poll
echo -n "$GREEN < " && curl http://localhost:5000/client/$GREEN/poll

# Both verify emoji
echo -n "$GREEN > " && curl -XPOST -H 'Content-Type: application/json' -d '{"response": "verified_crosssign", "data": {"emoji": "abcdefg"}}' http://localhost:5000/client/$GREEN/respond
if [[ "DEBUG" == "$DEBUG" ]]; then echo "DEBUG?" && read ; fi;

echo -n "$RED < " && curl http://localhost:5000/client/$RED/poll
echo -n "$GREEN < " && curl http://localhost:5000/client/$GREEN/poll


echo -n "$RED > " && curl -XPOST -H 'Content-Type: application/json' -d '{"response": "verified_crosssign", "data": {"emoji": "abcdefg"}}' http://localhost:5000/client/$RED/respond
if [[ "DEBUG" == "$DEBUG" ]]; then echo "DEBUG?" && read ; fi;


echo -n "$RED < " && curl http://localhost:5000/client/$RED/poll
echo -n "$GREEN < " && curl http://localhost:5000/client/$GREEN/poll

if [[ "DEBUG" == "$DEBUG" ]]; then echo "DEBUG?" && read ; fi;

echo -n "$RED > " && curl -XPOST -F 'logfile=@logfile-red.txt;type=text/plain' http://localhost:5000/client/$RED/upload
echo -n "$GREEN > " && curl -XPOST -F 'logfile=@logfile-green.txt;type=text/plain' http://localhost:5000/client/$GREEN/upload
