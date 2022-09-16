#!/bin/bash

# This script assumes to be run from the root of the following directory layout:
#  - complement: a checkout of the complement repo, with homeserver built
#  - trafficlight: a checkout of this repo
#  - matrix-react-sdk: a checkout of matrix-react-sdk, where the trafficlight adapter can be found.

# Additionally, an environmental variable `ELEMENT_WEB_LOCATION` should be set
# with the location of the `element-web` repository where the dev server can be run from.

systemctl list-units --type=service | grep -q docker
IS_DOCKER_RUNNING=$?
if [ $IS_DOCKER_RUNNING -ne "0" ]; then
	echo 'start docker first';
	exit
fi

session="trafficlight"

tmux new-session -d -s $session -c ./complement
tmux send-keys -t $session 'HOMERUNNER_SPAWN_HS_TIMEOUT_SECS=30 ./homerunner' Enter

tmux split-pane -h -c ./trafficlight
tmux send-keys -t $session '. venv/bin/activate' Enter
tmux send-keys -t $session 'QUART_APP=trafficlight quart run --host 0.0.0.0' Enter

CLIENT_COUNT=2
for i in $(seq 1 $CLIENT_COUNT)
do
	if [ "$i" -eq "1" ]; then
		tmux new-window -n adapters -c ./matrix-react-sdk
	else
		tmux split-pane -c ./matrix-react-sdk
	fi
	tmux send-keys -t $session "XDG_CONFIG_HOME=\"/tmp/cypress-home-$i\" yarn test:trafficlight" Enter
	tmux select-layout tiled
done

tmux attach-session -t $session
