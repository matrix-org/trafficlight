# Running traffic light locally

To write new tests, the easiest way to try them out is to run them locally.
For now, we'll use 2 element-web clients, and a synapse.

## Installation

There are 4 to 5 processes that need to run to be able to run the traffic light tests. For now, every time you want to run the tests, you need to restart the whole stack. To make this easy, there is the `run-localdev-setup.sh` script in the `scripts-dev` directory. This script assumes a directory structure as follows:

 - `complement`: your complement checkout
 - `synapse`: your synapse checkout
 - `trafficlight`: your trafficlight checkout
 - `matrix-react-sdk`: your matrix-react-sdk checkout that supports the `test:trafficlight` yarn command to run the element-web trafficlight adapter.

So make sure to install the instructions below in these directories.

### Docker

Make sure you have docker installed

### Build synapse complement image

Check out https://github.com/matrix-org/synapse and run the `scripts-dev/complement.sh --build-only`. 

### Setup homerunner

Check out https://github.com/matrix-org/complement and run the `go build` instructions in the README file. 

### Setup traffic light

Check out https://github.com/matrix-org/trafficlight/ and install as described in the README: https://github.com/matrix-org/trafficlight/#installation

### Setup matrix-react-sdk

Check out the matrix-react-sdk from https://github.com/matrix-org/matrix-react-sdk/pull/9117 (on a fork for now) and run `yarn install`.

## Running

Now you can run `ELEMENT_WEB_URL=https://app.element.io trafficlight/scripts-dev/run-localdev-setup.sh && tmux kill-server` from the root directory where you checked out all the projects. This will start all the processes needed to run the trafficlight tests in a tmux session. If the tests error out, or finish successfully, you can stop the whole stack by doing Ctrl+B and then press D.

This will also bring up the GUI for traffic light on http://localhost:5000/status/

If you want to run the tests against a local checkout of element web, you're going to have to set up [for local development there](https://github.com/vector-im/element-web#setting-up-a-dev-environment) first if you haven't done so already, run `yarn start` in the element-web repository, and pass `http://localhost:8080` in `ELEMENT_WEB_URL`.