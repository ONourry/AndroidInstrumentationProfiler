# Android Instrumentation Profiler
AIP is a tool used to profile mobile applications using existing instrumentation tests

# Tool Showcase Link

[![IMAGE ALT TEXT](https://i3.ytimg.com/vi/XMV-nxWjOQA/maxresdefault.jpg)]((https://www.youtube.com/watch?v=XMV-nxWjOQA) "Android Instrumentation Profiler")



# Requirements / Initial Setup
- AIP only runs on android devices (Make sure usb debugging is enabled and that adb detects your device)
- Make sure the that both androidx and android JUnitRunner imports are commented out in the initial MyRunner.java file before running AIP
- The repository must be manually cloned by the user. Make sure the project can be built and that the tests are working.

## Environment Variables
- The JAVA_HOME must point to a valid JDK of version 11 or above (otherwise the AST tool jar file will not run)
  - The bin directory of the JAVA_HOME must also be reachable through path (to call java)

- The ANDROID_HOME/ANDROID_SDK_ROOT must point to a valid android sdk
- The following folders containing Android tools required to build the app and generate the traces. They must be accessible directly through the PATH
  - build-tools (from android sdk folder)
  - platform-tools (from android sdk folder

## Configuration files
- Setup the correct path to your sdk in the local.properties file

- Setup the correct paths in the config.properties file
  - buildApplication (True/False): tells AIP to build the app or not
  - updateGradleBuildFile (True/False): tells AIP to update the gradle build files, customize the test runner and copy the runner into the androidTestFolder. 
  - gradleJDK: optional property to use a different jdk if the gradle build requires older/newer jdk versions from the one defined in $JAVA_HOME. Older revisions or project are often compatible only with jdk 1.8 (the $JAVA_HOME variable must remain jdk 11 or above to run the jar)

# How to run
- Connect the device to your computer/server and make sure adb detects the device

**execute launcher.py** 

*If you intend to run the tool again on the same revision set the updateGradleBuildFile properties to False in config.properties. Otherwise, AIP will parse the already modified gradle build file and try to generate apks from it. The builds might fail and the apks will not be usable to run the instrumentation. You can leave updateGradleBuildFile=True if you reset the repository to its default state (build file reset and MyRunner removed from androidTest folder)*

# Testing the tool
The toy project IntentsAdvancedSample from the https://github.com/android/testing-samples repository requires no permissions to run the tests. The tools should easily run on it.

The https://github.com/Neamar/KISS project should run without any issue using JDK 11 and contains more tests than the IntentsAdvancedSample toy project. (Use revision 228ccb1b4893bdf12c7b3b59b2ec7b493e477837. The later revisions require permissions to run the instrumented tests) 

# Possible issues
## Gradle
- Each project and revision use their own gradle version. Some older or newer revisions might use different gradle versions which cause the build to pass/fail

- If gradle stalls, try deleting existing locks using the following command
```
find ~/.gradle -type f -name "*.lock" -delete
```
- If the wrong gradle version is used to build an app, try deleting the currently cached gradle distributions. This will force re-download and usage of the correct one
```
rm -r ~/.gradle/caches/
```
## Versioning
- Older and newer revisions of an app may not be compatible with the same jdks (If jdk 11 doesn't work, try jdk 17 or vice-versa)
  - If versioning issues happen during the gradle build, try using the gradleJDK property in the configuration file  

## Other
- Some projects need the permissions to be set in order to run the instrumented tests
- For large experiments, if an error message appears saying adb cannot install the apks due to memory issues, restarting the phone can solve this problem
- If using pycharm, the IDE must be fully closed and restarted for env variable changes updated in the bash_profile to be reflected in the IDE
