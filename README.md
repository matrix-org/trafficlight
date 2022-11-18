# Trafficlight

Trafficlight controller for multiple clients (client-server-server-client) under test.

## Concept

The trafficlight server controls various matrix clients in an effort to coordinate testing in a live system.

Tests can specify sets of clients and servers under tests, that are created by the system and passed into their `run()` method.

TestSuites are setup around each Test, and provide a matrix of TestCases based on the ranges of Clients and Servers that are required for each test.

For example, one Test which asks servers for synapse or dendrite, and two clients that can be element android or element web, will end up creating and running 8 test cases - the product of two options for each server and two options for each client.

Servers are managed by complements `homerunner` tool, and are setup on demand as each TestCase starts. We will be able to start tests running against Synapse, Dendrite and other homeservers, so long as they are packaged for Complements' usecase.

Clients are managed by Adapters. Adapters are wrappers around various clients (eg, element-web / element-android / hydrogen ) that perform actions from the trafficlight tests.

Adapters are able to upload files (logs and videos) after a test run to allow us to reflect on the tests after they've completed.

Adapters are managed separately from the trafficlight server, and are managed in a similar style to CI runners - they register and poll the trafficlight server for commands to run. If no test requires the adapter at present they are left idling until they are allocated to a TestCase.

There are some APIs provided for interaction by the server:

`POST /client/<uuid>/register`

Register a new client with the server. Provide data about the client so the server can allocate to tests efficiently.

NB: at present this may block for an extended period as servers and the test model are created. This should be moved to a background/worker task, but has not yet been done.

`GET /client/<uuid>/poll`

Poll is used by clients to retrieve the next action. No data is required in It's just some JSON.

TODO: A dictionary of all actions that clients should support and how they should respond.

`POST /client/<uuid>/respond`

Report is used by clients to advance the state machine when they've finished their current action.

`POST /client/<uuid>/error`

```
{
  "error": { 
     "type": "adapter",
     "path": "/path_to_file/file.name#125",
     "details": "arbitrary long message for humans to read about the error"
  }
}
```

Error is used by clients to indicate an issue with the test client - for instance a timeout waiting for action or in some other way that the client has stopped functioning.

`POST /client/<uuid>/upload`

Mime-multipart upload of an arbitrary set of files related to the client.

Used for uploading videos, audio files, log files.

Additionally:

`GET /status`

Provides html for human-readable information about which clients are registered and what state they're in. Useful for debugging why a certain test has not yet run.

`GET /status/junit.xml`

Provides compatible junit.xml test output for use in other services / formatting / etc.

 * Tests that have not started (not found enough clients to run) are `waiting`
 * Tests that have found enough clients to run but are setting up are `preparing`
 * Tests that have finished preparing and are running are `running`
 * Tests that have started and completed are `success`
 * Tests that have started and explicitly fail are `failure`
 * Tests that have started but fail for another reason are `error`

## Writing tests

Tests should be written in the `trafficlight.tests` package.

To be picked up by the autodiscovery system, they should be named `**/*_test.py` and should contain a class that extend `trafficlight.internal.Test`.

These suites will then be expanded on startup into a number of test cases, using the list of clients and servers specified in the __init__ method of the Test.

The run method is an async method but can block the main http reactor thread so please do not perform synchronous waits in tests. Using a matrix client like matrix-nio is required for any other client behaviour.

Current status of all tests is on the status dashboard.

## Client controller loop

The client controllers should basically poll the server and have a switch block for each action being returned: For each action they should perform it and only respond when complete.

This concept of a loop should be simple enough to include in any language, and may be embedded into a client or be a separate process.

See [docs/client.md] for more details

## See Also

Polyjuice has a very similar poll method for getting data to clients but uses matrix as a transport rather than HTTP; we should ensure that the two could be compatible; it would be nice to be able to use the same automatable clients to power other testing tools. Polyjuice is all about testing weird situations with a custom server rather than testing the common cases across as many clients as possible; but it does have similar flows.

## Installation

All python dependencies installed via `pip`.

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

See [docs/local-dev.md] for information on running all components locally.

Trafficlight requires a homerunner instance running (ideally on localhost:54321 which is the default) to start and stop server instances as required.

You may need to create the complement-synapse image by checking out `matrix-org/synapse` and running:

`synapse> scripts-dev/complement.sh --build-only`

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
| TEST\_PATTERN | `**/*_test.py`          | Pattern to find tests. `**` for any recursive directory, `*` as normal wildcard |

Set these options via environment variables by prefixing with `TRAFFICLIGHT_`, eg: `TRAFFICLIGHT_TEST_PATTERN=only_one_test.py`.

## Releasing

???
