# Client writing guidelines

The clients should default to using `TRAFFICLIGHT_URL` to represent the server the trafficlight client should connect to for information. This should contain the base URL of the trafficlight server (without `/client`).

## Client behaviour

Clients should register then immediately start polling for actions to perform.

Clients that have not been allocated a test case will be dropped if they do not poll at least every 60s. 

Clients that have been allocated a test case will cause a timeout and fail the test, if they do not poll or respond at least every 180s.

If your action is long-running, ideally split it into smaller components internally and trigger extra polls of the server between them. You should take appropriate steps if the action changes (eg an action of "exit" should stop the test).

Do not have a background task that polls the server for an action reguardless of progress - we want the timeout to occur if no progress occurs in a fixed period of time.

## Action naming

Action should be named in `snake_case` - no capitals, spaces replaced by underscores.

We chose this because the tests are written in python and that's the native practice for naming methods. This means the actions in the test case code will be named the same as the actions on the wire.

We Should name actions with a verb at the start and what is being acted on later. The test should aim to not require comments to understand what is going on at each step.
 * `create_new_room("test_room_name")`
 * `invite_user("bob:server2")`

We should reserve `get` for passive actions that obtain information about what the client sees. 
 * `get_timeline`
 * `get_all_devices`

We Should Not name actions passively, or indirectly
 * `invite_user` instead of `do_the_user_invite`
 * `crosssign_user` instead of `invoke_crosssign`

We Should name actions after what they do, not what test they're related to
 * `create_poll` not `pr_52_action` or `msc_1235_action`

We Should avoid actions that have implied previous steps
 * `enable_video_calling` not `go_to_configuration` then `toggle_config_option("video_calling")`

We try to avoid naming actions in a client specific way unless required for the platform.
 * `clear_idb_cache` is not great because it doesn't apply to iOS / Android

Actions should ideally be generic across clients; avoid client-specific behaviour where possible. This allows our test cases to be as generic as possible and avoids requirements for duplication for different clients. But if a test does only apply to one platform; be clear in what the action does.

The canonical definition of actions that exist is in the Client code on the main branch of the trafficlight server. This includes the correct naming, potential contents of the `data: {}` block, and any values that may be returned from the action.

Not all clients support all actions. A client that is unable to support an action for any reason (unknown action, missing required data) should indicate this via an *Adapter Error*.

Branches that introduce test cases with a new or changed action should be matched by branches named identically, on all affected adapters. This will allow branches of adapters to be matched to the branch of trafficlight. In future, automated testing will be able to start branched adapters matching the change.

## Error endpoint usage

The error endpoint is somewhat lenient in what it accepts, however good practice for adapter generated errors is below:

### Adapter errors

For example, the adapter fails to start the client, the adapter has a runtime coding/data error, the adapter fails to find a required parameter in an action.

These errors should mark the test as errored, not failed, as they are not (directly) caused by the test. 


```
{
  "error": {
    "type": "adapter",
    "details": "Unable to start client due to InvalidClientException",
    "path": "/home/michaelk/work/trafficlight-adapter-element-web/src/trafficlight.js"
  }
}
```

Any error that is not of type 'action' will be interpreted as an error of type adapter. 

### Action failures

For example, the adapter correctly attempts to register a user on a homserver, but the password is an incorrect length; or the adapter correctly attempts to verify the last message was encrypted, but the last message was not encrypted.

```
{
  "error": {
     "type": "action",
     "details": "unable to cy.get('.mx_Tile .encrypted_shield_icon') within 30,000ms"
     "path": "/home/michaelk/work/trafficlight-adapter-element-web/cypress/e2e/trafficlight/actions/rooms.ts#679"
  }
}
```

Only errors of type 'action' will be treated as test failures rather than test errors.
