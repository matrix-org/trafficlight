# Traffic Light

Trafficlight controller for multiple clients (client-server-server-client) under test.

Shape of server still under development.

## Concept

The trafficlight server controls various matrix clients in an effort to coordinate them testing in a live system.

Each client identifies itself externally via a UUID; which is mapped to a internal client (normally a colour) when they first connect and are allocated to a test.

Clients should sit and poll constantly until they receive an action - and then continue to poll until they're told to 'exit'

There's a bunch of client management not yet provided by the server; for example handling tidy up of clients with explicit 'exit's if a test fails.

There are three APIs provided for interaction by the server:

`/client/<uuid>/register`

Register a new client with the server. Provide data about the client so the server can allocate to tests efficiently.

NB: at present this may block for an extended period as servers and the test model are created. This should be moved to a background/worker task, but has not yet been done.

`/client/<uuid>/poll`

Poll is used by clients to retrieve the next action. It's just some JSON.

TODO: A dictionary of all actions that clients should support and how they should respond.

`/client/<uuid>/report`

Report is used by clients to advance the state machine when they've finished their current action.

Inside the server is a state machine that handles actions by different clients; typically they're referred to by colour. When a real client 


Additionally:

`/status`

Provides html for human-readable information about which clients are registered and what state they're in. Useful for debugging why a certain test has not yet run.

`/status/junit.xml`

Provides compatible junit.xml test output for use in other services / formatting / etc.

 * Tests that have not started (not found enough clients to run) are `skipped`
 * Tests that have started and completed are successes
 * Tests that have started and explicitly fail are `failures`
 * Tests that have started but are in any other state are `errors`

## Client controller loop

The client controllers should basically poll the server and have a switch block for each action being returned: For each action they should perform it and only respond when complete.

This loop should be simple enough to include in any language.

## State machine

The state machine should aim to have states that are the equivalent of steps in a business use case, and at the highest level, eg: "Send message X in already joined room Y" not "Switch UI to room Y" then "Send message X in current room". This may need some creative thought and bending of the rules for things that are modal in clients.

## See Also

Polyjuice has a very similar poll method for getting data to clients but uses matrix as a transport rather than HTTP; we should ensure that the two could be compatible; it would be nice to be able to use the same automatable clients to power other testing tools. Polyjuice is all about testing weird situations with a custom server rather than testing the common cases across as many clients as possible; but it does have similar flows.

## Installation

As well as python dependencies installed via `pip`, libgraphviz-dev (debian) or graphviz-devel (fedora) is required for the status page graph rendering.

## Development

Create a virtual environment with pip ≥ 21.1 and install
```shell
> pwd
/home/michaelk/work/trafficlight/
> python -m venv venv/
> venv/bin/pip install --upgrade pip
> venv/bin/pip install -e .[dev]
```


To run the linters and `mypy` type checker, use `./scripts-dev/lint.sh`.

## Starting

This requires a homerunner instance running (ideally on localhost:54321 which is the default) to start and stop server instances as required.

You may need to create the complement-synapse image by checking out synapse and running:

`scripts-dev/complement.sh --build-only`

Use this to start the test server:
```shell
> . venv/bin/activate
(venv) > FLASK_APP=trafficlight flask run --host 0.0.0.0
... server starts
```

## Releasing

???
