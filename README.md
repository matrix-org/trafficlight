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

`/client/<uuid>/poll`

Poll is used by clients to retrieve the next action. It's just some JSON.

TODO: A dictionary of all actions that clients should support and how they should respond.

`/client/<uuid>/report`

Report is used by clients to advance the state machine when they've finished their current action.

Inside the server is a state machine that handles actions by different clients; typically they're referred to by colour. When a real client 


## Client controller loop

The client controllers should basically poll the server and have a switch block for each action being returned: For each action they should perform it and only respond when complete.

This loop should be simple enough to include in any language.

## State machine

The state machine should aim to have states that are the equivalent of steps in a business use case, and at the highest level, eg: "Send message X in already joined room Y" not "Switch UI to room Y" then "Send message X in current room". This may need some creative thought and bending of the rules for things that are modal in clients.

## See Also

Polyjuice has a very similar poll method for getting data to clients but uses matrix as a transport rather than HTTP; we should ensure that the two could be compatible; it would be nice to be able to use the same automatable clients to power other testing tools. Polyjuice is all about testing weird situations with a custom server rather than testing the common cases across as many clients as possible; but it does have similar flows.

## Installation


## Development

In a virtual environment with pip ≥ 21.1, run
```shell
pip install -e .[dev]
```

To run the unit tests, you can either use:
```shell
tox -e py
```
or
```shell
trial tests
```

To run the linters and `mypy` type checker, use `./scripts-dev/lint.sh`.

## Starting

Use this to start the test server:
`FLASK_APP=trafficlight flask run --host 0.0.0.0`

## Releasing

???
