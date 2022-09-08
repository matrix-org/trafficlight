# Network proxy

This acts as a client (polls for updates and actions to perform)
and provides network changes as required.

The current set of actions supported by this are:

## disableEndpoint 

Disable all (GET/POST/HEAD/PUT etc) http requests to this exact endpoint.

Disabling an endpoint that has already been disabled is not an error (as the action could be sent multiple times before the flow continues.

```
{
   "action": "disableEndpoint",
   "data": {
       "endpoint": "/_matrix/client/v1/createRoom",
   }
}
```

When complete, a "endpointDisabled" response should be sent.

## enableEndpoint

Enable all (GET/POST/HEAD/PUT etc) http requests to this exact endpoint.

Enabling an endpoint that has not been disabled is not an error (as the action could be sent multiple times before the flow continues.

```
{ 
  "action": "enableEndpoint",
  "data": {
      "endpoint": "/_matrix/client/v1/createRoom",
  } 
}
```

When complete, a "endpointDisabled" response should be sent.

## Other considerations

The proxy should (ideally) log all denied requests and upload them as a file after the test completes via the `/client/<xxx>/upload`, to make it easy to check what was disabled.


# alternate thought:

```
{
   "action": "setRules",
   "data": {
      "disabledRegexes": [
            "/_matrix/client/v1/.*"
      ],
      "enabledRegexes": [
            "/_matrix/client/v1/sendMessage
      ]
   }

}
```

This should send a `rulesSet` response once the rules have been set.

This would express that all endpoints under client/v1 except for client/v1/sendMessage are disabled.

Sending another 'setRules' message should replace the rules with the new ones. Sending an entirely blank "data" section should remove all rules. 

