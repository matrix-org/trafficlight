#!/bin/bash

# This bash script has been used to create and register client_types, and force them through a simple flow.

# It doesn't do anything like validate the steps make sense, etc, and will generally not work if other client_types are registered.

# It's probably a not unreasonable place to hack around with client_types to get the server into a specific condition; but fairly soon tests will need to be more complicated.

DEBUG=DEBUG
RUN=`date +%s`
FOO=foo_$RUN
BAR=bar_$RUN
echo -n "$FOO # " && curl -X POST -H 'Content-Type: application/json' http://localhost:5000/client/$FOO/register -d '{"type": "element-web", "version": "0.15.0"}'

echo -n "$FOO > " && curl -XPOST -H 'Content-Type: application/json' http://localhost:5000/client/$FOO/error -d '{"error": {"type": "unknown_error", "path": "/var/logs/errors.log.1", "details": "Failed to read attachment" } }'
