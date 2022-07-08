# Element Android

First, start synapse and the trafficlight server

Testing element android can be done by:
 - Ensure you have an emulator or physical device connected to your machine
 - Run the Trafficlight UI test in a continual loop `while true; do ./gradlew  -Pandroid.testInstrumentationRunnerArguments.class=im.vector.app.ui.TrafficLightLoop vector:connectedAndroidTest; done;`
  - TODO: make this more efficient somehow; perhaps generate an APK and upload to firebase for ongoing, parallel test cases.
  - Multiple emulators can be run in parallel in android studio, by selecting run on multiple devices. Do not attempt to run parallel builds on the console from a single checkout (eg launch two separate processes against two emulators) - the two builds will either break each other or one will wait until the second completes, depending on gradle parallelisation.
