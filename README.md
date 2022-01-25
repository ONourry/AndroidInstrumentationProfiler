# Android Instrumentation Profiler
AIP is a tool used to profile mobile applications using existing instrumentation tests

#Setup
- AIP only runs on android devices (Make sure usb debugging is enabled and that adb detects your device)
- The following folders containing Android tools required to build the app and trace the execution must be accessible directly through the PATH
  - build-tools folder (from android sdk folder)
  - platform-tools (from android sdk folder
- The JAVA_HOME must point to a valid JDK of version 11 or above (otherwise the AST tool jar file may not run)
  - The bin directory of the JAVA_HOME must also be reachable through path (to call java)
- The ANDROID_HOME/ANDROID_SDK_ROOT must point to a valid android sdk


#How to run
- Connect the device to your computer/server and make sure adb detects the device
- Setup the correct paths in the config.properties file
  - The gradleJDK is an optional property that can be filled if a different jdk is required to build gradle without having to change the $JAVA_HOME variable
- Setup the correct path to your sdk in the local.properties file
- Make sure the correct package name is shown at the top of the custom runner file (MyRunner.java)
- Make sure the project you want to analyze can be built via gradle

execute the launcher.py file

If you intend to run the tool again on the same revision set the buildApplication and updateGradleBuildFile properties to False in config.properties. Failing to do so will result in AIP parsing the already modified gradle build file and trying to generate apks from it --> The build and/or the instrumentation will fail. The build.gradle must be reset to default if you leave buildApplication=True and updateGradleBuildFile=True

#Possible issues
- Each project and revision use their own gradle version. Some older or newer revisions might use different gradle versions which cause the build to pass/fail
- Older and newer revisions of an app may not be compatible with the same jdks (for gradle builds, a different jdk can be specified in the config.properties file via the gradleJDK property)
- If gradle stalls, try deleting existing locks using the following command
```
find ~/.gradle -type f -name "*.lock" -delete
```
- If the wrong gradle version is used to build an app, try deleting the currently cached gradle distributions. This will force re-download and usage of the correct one
```
rm -r ~/.gradle/caches/
```
- The tests or the gradle build may fail if the jdk version specified in the $JAVA_HOME environment variable is not compatible with the current revision
- If using pycharm, the IDE must be fully closed and restart for env variable changes to be reflected in the IDE
