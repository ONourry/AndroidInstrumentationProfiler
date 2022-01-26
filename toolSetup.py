import os
import shutil
import re

from utils.util import exec
from utils.gradle import GradleParser,GradleBuilder

class NoAndroidTestException(Exception):
    pass

class NoJavaAndroidTestException(Exception):
    pass


def findTestFolder(app_repo):  # find package name
    androidTestFolders = []  # some apps are using androidTest subdirectories. We need the top level one
    for dirPath, dirs, files in os.walk(app_repo):
        if 'src' in dirPath and 'androidTest' in dirs:
            androidTestFolders.append(os.path.join(dirPath, 'androidTest'))
    if len(androidTestFolders) == 0:
        raise NoAndroidTestException
    elif len(androidTestFolders) >= 1:
        for dirPath in androidTestFolders:
            # top level androidTestFolder should contain a java/ directory under it. In some cases it can be kotlin
            if os.path.isdir(os.path.join(dirPath, 'java/')):
                return dirPath
    raise NoJavaAndroidTestException


def findPackageName(app_repo):
    androidTestFolder = findTestFolder(app_repo)

    # java instrumentation code
    androidTestFolderForJava = os.path.join(androidTestFolder, 'java/')

    # Get all the source code files
    target_files = []
    for rootPath, dirs, files in os.walk(androidTestFolderForJava):
        for file in files:
            if file.endswith('.java'):
                target_files.append(os.path.join(rootPath, file))

    # Find the top level file that contains source code. This is where we will copy custom runner and use the path as the package name
    shortest_path_depth = 99
    list_index = 0
    for i, instrumentationFile in enumerate(target_files):
        path_depth = len(instrumentationFile.split("/"))
        if path_depth < shortest_path_depth:
            shortest_path_depth = path_depth
            list_index = i

    topFile = target_files[list_index]
    topFilePath = "/".join(topFile.split("/")[:-1])


    packageName = topFile.replace(androidTestFolderForJava, "")
    packageName = ".".join(packageName.split("/")[:-1])  # Remove file name, replace / by .

    return (topFilePath, packageName)


# Find package name, move myRunner into the right directory, Update package name in myRunner
def setupRunner(app_repo, myRunnerFile):
    copyPath, packageName = findPackageName(app_repo)  # copy path is where we want to copy myRunner
    runnerName = myRunnerFile.split("/")[-1]
    newRunnerFile = os.path.join(copyPath, runnerName)
    print("Runner Name:", runnerName)
    javaPackageName = 'package ' + packageName + ";"
    print("Package Name:", javaPackageName)

    shutil.copy(myRunnerFile, newRunnerFile)
    with open(newRunnerFile, 'r') as f:
        content = f.read()

    packagePattern = re.compile("package ([a-z|A-Z]+.*)+")
    content = re.sub(packagePattern, javaPackageName, content,
                     1)  # find existing package name and replace with new package name. Only 1st occurence

    with open(newRunnerFile, 'w') as f:
        f.write(content)
    return packageName, newRunnerFile


def installApks(app_repo):
    debugApk = None
    testApk = None
    for dirPath, dirs, files in os.walk(app_repo):
        if 'build/outputs/apk/androidTest' in dirPath:
            apk_files = [f for f in files if f.endswith('.apk')]
            for apk in apk_files:
                testApk = os.path.join(dirPath, apk)
                if not os.path.isfile(testApk):
                    testApk = None
        elif 'build/outputs/apk/debug' in dirPath:
            apk_files = [f for f in files if f.endswith('.apk')]
            for apk in apk_files:
                debugApk = os.path.join(dirPath, apk)
                if not os.path.isfile(debugApk):
                    debugApk = None
        elif 'build/outputs/apk' in dirPath:
            if (debugApk is None) or (testApk is None):
                if testApk is None:
                    test_apk_files = [os.path.join(dirPath, f) for f in files if f.endswith('androidTest.apk')]
                if debugApk is None:
                    debug_apk_files = [os.path.join(dirPath, f) for f in files if f.endswith('debug.apk')]
                #assert len(test_apk_files) < 2
                #assert len(debug_apk_files) < 2
                if len(debug_apk_files):
                    debugApk = debug_apk_files[0]
                if len(test_apk_files):
                    testApk = test_apk_files[0]
    assert debugApk is not None
    assert testApk is not None

    exec("adb shell dumpsys battery set ac 0", app_repo)
    exec("adb shell dumpsys battery set usb 0", app_repo)

    install_debug = "adb install -r " + debugApk
    install_test = "adb install -r " + testApk
    print(install_debug)
    print(install_test)
    print("Installing debug apk", debugApk)
    exec(install_debug, app_repo)
    print("Installing test apk", testApk)
    exec(install_test, app_repo)
    print("installed apks")


def setup(appRepo, propertyFile, build, updateGradleBuildFile, myRunnerFile, gradleJDK=None):
    gradleParser = GradleParser(appRepo)
    gradleBuilder = GradleBuilder()

    runnerName = os.path.basename(myRunnerFile)
    runnerName = os.path.splitext(runnerName)[0]

    if build.lower() == "true":
        if updateGradleBuildFile.lower() == "false":#no update for gradle
            findTestFolder(appRepo)  #to check no Android Test Exception/No Java AndroidTest
            pass
        elif updateGradleBuildFile.lower() == "true":
            gradleParser.removeAppProcessSufix()
            packageName, myNewRunnerFile = setupRunner(appRepo, myRunnerFile)
            packageRunner = packageName + "." + runnerName
            gradleParser.updateGradleRunner(packageRunner, myNewRunnerFile)

        previous_app = None
        success, gradle_dir, build_output = gradleBuilder.AssembleGradle(appRepo, previous_app, property_file=propertyFile, gradleJDK=gradleJDK)
        installApks(appRepo)
        return success, build_output
    else:
        installApks(appRepo)