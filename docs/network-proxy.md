# Network proxy

This acts as a client (polls for updates and actions to perform)
and provides network changes as required.

When registering, the proxy should claim to be a client of type `network-proxy`, and should provide the endpoint that it is accessible via in the `endpoint` field.

The current set of actions supported by the proxy are:

## idle

Idle for the time given in `delay` for a new command, as with other clients.

```
{ 
   "action": "idle",
   "data": {
       "delay": 5000
   }
}
```

## proxyTo

Sets the endpoint that the network proxy should forward to

```
{
   "action": "proxyTo"
   "data": {
      "url": "https://<host>:<port>/
   }
}
```

When complete a `proxyToSet` response should be sent.

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

When complete, a "endpointEnabled" response should be sent.

## exit

The proxy should stop forwarding traffic and may do so in an unclean fashion (not waiting for responses) if required - the test has been completed. (it is also valid to cleanly terminate all connections before exiting)

## Other considerations

The proxy should (ideally) log all denied requests and upload them as a file after the test completes via the `/client/<xxx>/upload`, to make it easy to check what was disabled.

If the proxy receives requests before the `setHomeserverUrl` action is performed, then the requests should be dropped and a request to `/client/<uuid>/error` with details of the request should be sent.

The proxy should forward all requests transparently where possible, but will need to be aware of well-known responses in the login response and in the .well-known/matrix/client response, where the server endpoint may need to be updated.


