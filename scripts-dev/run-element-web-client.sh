#!/bin/bash
echo "waiting for $ELEMENT_WEB_URL to come online..."
sleep 2
while [[ "$(curl --connect-timeout 2 -s -o /dev/null -w ''%{http_code}'' $ELEMENT_WEB_URL)" != "200" ]]; do sleep 1; done
yarn test:trafficlight