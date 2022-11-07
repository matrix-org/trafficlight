#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# This script assumes to be run from the root of the following directory layout:
#  - complement: a checkout of the complement repo, with homeserver built
#  - trafficlight: a checkout of this repo
#  - trafficlight-adapter-element-web: a checkout of https://github.com/matrix-org/trafficlight-adapter-element-web
#  - trafficlight-proxy: a checkout of https://github.com/vector-im/trafficlight-proxy/


# Additionally, an environmental variable `CYPRESS_BASE_URL` should be set
# with url of the element-web instance that should be tested.

echo "Docker Version: "
docker info -f '{{.ServerVersion}}'
IS_DOCKER_RUNNING=$?
if [ $IS_DOCKER_RUNNING -ne "0" ]; then
	echo 'start docker first';
	exit
fi

echo "Using CYPRESS_BASE_URL $CYPRESS_BASE_URL"
session="trafficlight"

tmux new-session -d -s $session -c ./complement
tmux send-keys -t $session 'HOMERUNNER_SPAWN_HS_TIMEOUT_SECS=30 ./homerunner' Enter

tmux split-pane -h -c ./trafficlight
tmux send-keys -t $session '. venv/bin/activate' Enter
tmux send-keys -t $session 'QUART_APP=trafficlight quart run --host 0.0.0.0' Enter

CLIENT_COUNT=${CLIENT_COUNT:-2}
for i in $(seq 1 $CLIENT_COUNT)
do
	if [ "$i" -eq "1" ]; then
		tmux new-window -n adapters -c ./trafficlight-adapter-element-web
	else
		tmux split-pane -c ./trafficlight-adapter-element-web
	fi
	# docker cuts the network when starting the whole setup
	# so give it 5 seconds cut and then wait until the network has come back by polling the cypress url
	# so the tests don't fail because of this
	tmux send-keys -t $session "sleep 5" Enter
	tmux send-keys -t $session 'while [[ "$(curl --connect-timeout 2 -s -o /dev/null -w ''%{http_code}'' $CYPRESS_BASE_URL)" != "200" ]]; do sleep 1; done' Enter
	tmux send-keys -t $session "XDG_CONFIG_HOME=\"/tmp/cypress-home-$i\" yarn test:trafficlight" Enter
	tmux select-layout tiled
done

REQUIRES_PROXY=${REQUIRES_PROXY:-false}
if [[ $REQUIRES_PROXY == "true" ]]; then
	tmux split-pane -v -c ./trafficlight-proxy
	tmux send-keys -t $session 'yarn start' Enter
fi


REQUIRES_HYDROGEN=${REQUIRES_HYDROGEN:-false}
if [[ $REQUIRES_HYDROGEN == "true" ]]; then
	tmux split-pane -v -c ./trafficlight-adapter-hydrogen-web
	tmux send-keys -t $session 'while [[ "$(curl --connect-timeout 2 -s -o /dev/null -w ''%{http_code}'' $HYDROGEN_APP_URL)" != "200" ]]; do sleep 1; done' Enter
	tmux send-keys -t $session 'yarn test:trafficlight' Enter
fi
tmux attach-session -t $session
