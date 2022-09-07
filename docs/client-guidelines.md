# Client writing guidelines

Unsure what else should go here, please add thoughts if you end up writing a client.

The clients should default to using `TRAFFICLIGHT_URL` to represent the server the trafficlight client
should connect to for information. This should contain the base URL of the trafficlight server (without `/client`).

Clients should aim to poll at least every 60s and should ideally respect the delay parameter in the `idle` respnose.
This might become more handwavey if the client is performing a blocking action where it's unable to poll while working.


