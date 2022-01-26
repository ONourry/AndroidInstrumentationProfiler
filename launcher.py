from toolSetup import setup
from profiler import profile
from utils.gradle import GradleParser
from utils.util import exec
import subprocess
import configparser
import os


"""
java -jar TestMethodExtractor.jar path/to/repo revision path/to/folderWhereGenerateOutputFile
"""
def getTestSignatures(jarExecutable, appRepo, astOutputDir):
    #command = "git rev-parse HEAD"
    #print(command.split())
    #revisionHash = subprocess.check_output(command.split(), cwd=appRepo).decode().strip()
    #subprocess.call(["java", "-jar", "TestMethodExtractor.jar", appRepo, revisionHash, astOutputDir])
    subprocess.call(["java", "-jar", jarExecutable, appRepo, astOutputDir])


def uninstallApp(app_process, app_repo):
    print("UNINSTALLING NOW")
    uninstall_app = "adb uninstall " + app_process
    uninstall_instrumentation = "adb shell pm uninstall " + app_process + ".test"

    print(uninstall_app)
    print(uninstall_instrumentation)
    exec(uninstall_app, app_repo)
    exec(uninstall_instrumentation, app_repo)


def main():
    jarExecutable = os.path.join(os.getcwd(),"TestMethodExtractor.jar")
    configFile = os.path.join(os.getcwd(),'config.properties')
    configIni = configparser.ConfigParser()
    configIni.read(configFile, encoding='utf-8')
    print({section: dict(configIni[section]) for section in configIni.sections()})

    appRepo = configIni["CONFIG"]["appDirectory"]
    propertyFile = configIni["CONFIG"]["localPropertyFile"]
    build = configIni["CONFIG"]["buildApplication"]
    updateGradle = configIni["CONFIG"]["updateGradleBuildFile"]
    customTestRunner = configIni["CONFIG"]["testRunner"]
    profilerOutputDirectory = configIni["CONFIG"]["profilerOutputDirectory"]
    astOutputDir = configIni["CONFIG"]["astOutputDir"]
    gradleJDK = configIni["CONFIG"]["gradleJDK"] #jar file needs jdk 11+ to run but some projects need older ver to build

    getTestSignatures(jarExecutable, appRepo, astOutputDir)
    testSignatureFile = os.path.join(astOutputDir, 'test_cases.txt')

    print("start setup")
    setupOut = setup(appRepo=appRepo, propertyFile=propertyFile, build=build, updateGradleBuildFile=updateGradle, myRunnerFile=customTestRunner, gradleJDK=gradleJDK)

    testSignatures = None
    with open(testSignatureFile,"r") as f:
        testSignatures = f.read().strip().split("\n")

    for testCase in testSignatures:
        testCaseOutput = os.path.join(profilerOutputDirectory,testCase)
        if not os.path.isdir(testCaseOutput):
            os.makedirs(testCaseOutput)

        profile(appRepo, testCaseOutput, testCase)

    gradleParser = GradleParser(appRepo)
    uninstallApp(gradleParser.get_app_process(), appRepo)

if __name__ == "__main__":
    main()