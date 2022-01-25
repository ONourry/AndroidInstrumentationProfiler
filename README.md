# Android Instrumentation Profiler
AIP is a tool used to profile mobile applications using existing instrumentation tests

# Setup
- AIP only runs on android devices (Make sure usb debugging is enabled and that adb detects your device)
- The following folders containing Android tools required to build the app and trace the execution must be accessible directly through the PATH
  - build-tools folder (from android sdk folder)
  - platform-tools (from android sdk folder
- The JAVA_HOME must point to a valid JDK of version 11 or above (otherwise the AST tool jar file may not run)
  - The bin directory of the JAVA_HOME must also be reachable through path (to call java)
- The ANDROID_HOME/ANDROID_SDK_ROOT must point to a valid android sdk
- The repository must be manually cloned by the user. Make sure the project can be built and that the tests are working.

# How to run
- Connect the device to your computer/server and make sure adb detects the device
- Make sure the correct package name for the analyzed app is shown at the top of the custom runner file (MyRunner.java)
- Setup the correct path to your sdk in the local.properties file
- Setup the correct paths in the config.properties file
  - buildApplication: tells AIP to build the app or not
  - updateGradleBuildFile: tells AIP to update the gradle build files to customize the test runner. 
  - gradleJDK: optional property that can be filled if a different jdk is required to build gradle without having to change the $JAVA_HOME variable

*If you intend to run the tool again on the same revision set the updateGradleBuildFile properties to False in config.properties. Otherwise, AIP will parse the already modified gradle build file and try to generate apks from it. The builds might fail and the apks will not be usable to run the instrumentation. You can also leave updateGradleBuildFile=True if you reset the build.gradle file to its default state*


**execute launcher.py** 

# Possible issues
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
- The tests or the gradle build may fail if the jdk version specified in the JAVA_HOME environment variable is not compatible with the current revision
- If using pycharm, the IDE must be fully closed and restarted for env variable changes to be reflected in the IDE
