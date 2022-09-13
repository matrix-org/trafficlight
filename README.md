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

`/client/<uuid>/error`

```
{
  "error": { 
     "type": "unknown_error",
     "path": "/path_to_file/file.name",
     "details": "arbitrary long message for humans to read about the error"
  }
}
```

Error is used by clients to indicate an issue with the test client - for instance a timeout waiting for action or in some other way that the client has stopped functioning.

`/client/<uuid>/upload`

Mime-multipart upload of an arbitrary set of files related to the client.

Used for uploading videos, audio files, log files.

Additionally:

`/status`

Provides html for human-readable information about which clients are registered and what state they're in. Useful for debugging why a certain test has not yet run.

`/status/junit.xml`

Provides compatible junit.xml test output for use in other services / formatting / etc.

 * Tests that have not started (not found enough clients to run) are `skipped`
 * Tests that have started and completed are successes
 * Tests that have started and explicitly fail are `failures`
 * Tests that have started but are in any other state are `errors`

## Writing tests

Tests should be written in the `trafficlight.tests` package.

To be picked up by the autodiscovery system, they should be named `**/*_testsuite.py` and should contain one or more classes that extend `trafficlight.tests.TestSuite`.

These suites will then be expanded on startup into a number of test cases, using the list of clients and servers known to trafficlight at present.

The testSuites should implement the two methods, `generate_model` and `validate_model`. THe generator should return a trafficlight.object.Model which represents the state machine the test should go through.

The validator should post-process the model and ensure that all conditions have been successfully applied. `trafficlight.tests.assertions` contains useful `unittest`-style assertXXX() methods that can mark the test as `failed`. Other exceptions will mark the test as `error`.

Current status of all tests is on the status dashboard.

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
(venv) > QUART_APP=trafficlight quart run --host 0.0.0.0
... server starts
```

## Docker

There is a docker image that runs using hypercorn in production mode. It is available at ghcr.io/matrix-org/trafficlight, and all PRs and the main branch are published there.

`docker run -p 5000:5000 ghcr.io/matrix-org/trafficlight`

Passing in envvars below will forward them to the application as expected.

## Configuring

Various options can be used to configure the tests:

| Name          | Default                      | Function |
| ----          | -------                      | -------- |
| TEST\_PATTERN | `**/*_testsuite.py`          | Pattern to find tests. `**` for any recursive directory, `*` as normal wildcard |
| SERVER\_TYPES | `Synapse`                    | Comma-seperated list of server types to generate tests with. Current option is only `Synapse` |
| CLIENT\_TYPES | `ElementWeb,ElementAndroid`  | Comma-seperated list of client types to generate tests with. Current options are `ElementWeb` and `ElementAndroid` |

Set options via environment variables by prefixing with `TRAFFICLIGHT_`, eg: `TRAFFICLIGHT_TEST_PATTERN=only_one_test.py`.

## Releasing

???
