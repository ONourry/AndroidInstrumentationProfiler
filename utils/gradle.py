import re
import json
import subprocess
import os
import shutil


class GradleParser:
    def __init__(self, app_repo):
        self.app_repo = app_repo
        self.defaultConfigInfo = self.getDefaultConfigInfo('applicationId', 'testInstrumentationRunner',
                                                           'testApplicationId')

    def get_app_process(self):
        app_process = self.defaultConfigInfo['applicationId'].replace('\"', '')
        app_process = app_process.replace("\'", "")

        if "$" in app_process:  # they're using variables. Can't use the parsed text
            app_process = self.extractAppProcess()
        return app_process


    def get_runner(self):
        runner = self.defaultConfigInfo['testInstrumentationRunner'].replace('\"', '')
        runner = runner.replace("\'", "")
        return runner


    def get_test_application_id(self):
        if self.defaultConfigInfo.get("testApplicationId"):
            testApplicationId = self.defaultConfigInfo['testApplicationId'].replace('\"', '')
            print("Found custom test process name:", testApplicationId)
        else:
            print("Default .test process name")
            testApplicationId = None  # Sometimes they put custom test apk process name
        return testApplicationId

        # Some apps use variables to define the process. Cannot extract the text. Gotta extract the process name somewhere else
        # i.e:  #"${project.APP_GROUP}.${project.APP_ID.toLowerCase(Locale.CANADA)}"

    def extractAppProcess(self):
        apk_metadata = None
        # Find apk metadata after build command is ran
        for dirPath, dirs, files in os.walk(self.app_repo):
            if 'build/outputs/apk/debug' in dirPath:
                json_files = [f for f in files if f.endswith('.json')]
                for file in json_files:
                    if file == "output-metadata.json":
                        apk_metadata = os.path.join(dirPath, file)
                        print(apk_metadata)

        with open(apk_metadata, 'r') as f:
            contents = json.loads(f.read())
            return contents['applicationId']


    def findGradleFile(self):
        for dirpath, dirnames, filenames in os.walk(self.app_repo):
            if "app" in dirnames and "gradlew.bat" in filenames:
                if os.path.isfile(os.path.join(dirpath, 'app/build.gradle')):
                    return os.path.join(dirpath, 'app/build.gradle')
                elif os.path.isfile(os.path.join(dirpath, 'app/build.gradle.kts')):
                    return os.path.join(dirpath, 'app/build.gradle.kts')

    # Find and return the content for a specific section. i.e: everything in 'android {' section for build.gradle
    def getSectionData(self, text, section_pattern):
        brackets = ['{']  # add one initially from the 'android {' pattern that starts the android settings section
        subtext = []
        for i, char in enumerate(text):
            subtext.append(char)
            if char == "{":
                brackets.append(char)
            elif char == "}":
                brackets.pop(0)

            if len(brackets) == 0:  # we matched all the brackets, section is done
                section_data = section_pattern + ''.join(subtext)  # re-add the section header that was removed by split
                after_section_data = text[i + 1:]
                return (section_data, after_section_data)

    # Only works for java, not kotlin
    def makeIntoDictFormat(self, text):
        # dict_start = re.compile(" {") #find section title + {  like 'android {'
        # dict_format = (re.sub(dict_start, '":\g<0>', text)) #add ": between section title and { for dict format
        dict_format = text
        dict_format = re.sub("([a-zA-Z|\d|.]+)", '"\g<0>"', dict_format)  # add quotation to every word
        dict_format = re.sub("([a-zA-Z|\d|.]+\" )", '\g<0>:', dict_format)  # add : between space
        dict_format = re.sub("\"(\s*\")", r'",\1', dict_format)  # add comma after each value
        dict_format = re.sub(r"(})[\s]* \"", r'\1,"', dict_format)  # add comma after each dict value

        dict_format = '{' + dict_format + '}'  # required for dict format

        # make into python dict
        dict_object = json.loads(dict_format)
        return dict_object

    """
    Rebuild androidSection with the modified values
    Before-----
    buildTypes {
            debug {
            }
            release {
                signingConfig signingConfigs.release
                zipAlignEnabled true
                minifyEnabled false
            }
        }
    After----------
    buildTypes {
            debug {
                debuggable true
            }
            release {
                signingConfig signingConfigs.release
                zipAlignEnabled true
                minifyEnabled false
            }
        }
    """
    def reconstructAndroidSection(self, android_dict):
        androidSection = list(android_dict.keys())[0] + " {\n"  # there should only be 1 key --> buildTypes
        for sectionName, buildTypes in android_dict.items():
            for builds, parameters in buildTypes.items():
                androidSection += builds + " {\n"
                for param, value in parameters.items():
                    androidSection += param + " " + value + "\n"
                androidSection += '}\n'
            androidSection += '}\n'
        return androidSection


    def makeDebuggable(self):
        buildGradleFile = self.findGradleFile()
        section_pattern = "buildTypes {"  # section to make apk debuggable starts with this pattern
        with open(buildGradleFile) as f:
            data = f.read()
            if section_pattern in data:
                print("Found android section")
                fileSections = data.split(section_pattern)

                android_section_start = fileSections[1]
                build_types_text, after_buildTypes_text = self.getSectionData(android_section_start, section_pattern)

                android_dict = self.makeIntoDictFormat(build_types_text)
                if not android_dict['buildTypes']['debug'].get('debuggable'):
                    android_dict['buildTypes']['debug']['debuggable'] = 'true'
                else:
                    print("App is already debuggable")

                # Reconstruct file
                android_section = self.reconstructAndroidSection(android_dict)
                gradleFile = fileSections[0] + android_section + after_buildTypes_text
                with open(buildGradleFile, 'w') as f:
                    f.write(gradleFile)


    def removeAppProcessSufix(self):
        buildGradleFile = self.findGradleFile()
        section_pattern = "buildTypes {"
        with open(buildGradleFile) as f:
            data = f.read()
            if section_pattern in data:
                print("Found android section")
                fileSections = data.split(section_pattern, 1)

                android_section_start = fileSections[1]
                # remove everything after buildTypes section
                build_types_text, after_buildTypes_text = self.getSectionData(android_section_start, section_pattern)
                build_types_lines = build_types_text.split("\n")

                for line in build_types_lines:
                    if 'applicationIdSuffix' in line:
                        build_types_lines.remove(line)

                build_types_text = '\n'.join(build_types_lines)
                gradle_file = fileSections[0] + build_types_text + after_buildTypes_text.rstrip()
                with open(buildGradleFile, 'w') as f:
                    f.write(gradle_file)


    def getDefaultConfigInfo(self, *args):
        buildGradleFile = self.findGradleFile()
        print(buildGradleFile)
        if not buildGradleFile:
            print("COULDN'T FIND GRADLE FILE")
            return {}
        section_pattern = "defaultConfig {"
        return_data = {}
        with open(buildGradleFile) as f:
            data = f.read()
            # print(data)
            if section_pattern in data:
                print("Found android section")
                fileSections = data.split(section_pattern)
                android_section_start = fileSections[1]

                try:
                    defaultConfig_text, after_defaultConfig_text = self.getSectionData(android_section_start,
                                                                                       section_pattern)
                except TypeError:
                    # section doesn't exist
                    return {}

                defaultConfig_lines = defaultConfig_text.split("\n")

                if 'applicationId' in args:
                    for line in defaultConfig_lines:
                        if 'applicationId' in line:
                            app_process = line.strip().split()[1]
                            return_data['applicationId'] = app_process

                if 'testInstrumentationRunner' in args:
                    for line in defaultConfig_lines:
                        if 'testInstrumentationRunner' in line:
                            runner = line.strip().split()[1]
                            return_data['testInstrumentationRunner'] = runner

                if 'testApplicationId' in args:
                    for line in defaultConfig_lines:
                        if 'testApplicationId' in line:
                            instrumentationProcess = line.strip().split()[1]
                            return_data['testApplicationId'] = instrumentationProcess

        return return_data


    def updateGradleRunner(self, newRunner, runnerFile):
        buildGradleFile = self.findGradleFile()
        section_pattern = "defaultConfig {"
        dep = ['android.support.test.runner.AndroidJUnitRunner', 'androidx.test.runner.AndroidJUnitRunner']
        with open(buildGradleFile) as f:
            data = f.read()
            if section_pattern in data:
                fileSections = data.split(section_pattern)

                android_section_start = fileSections[1]
                section_text, after_section_text = self.getSectionData(android_section_start, section_pattern)

                updatedSectionText, dep_used = self.updateRunnerText(section_text, newRunner)
                gradle_file = fileSections[0] + updatedSectionText + after_section_text.rstrip()

                # Make the runner use the old instrumentation dependency (android) or the more recent one (androidx)
                if dep_used == 'androidx':
                    self.updateRunnerDependency(dep[1], runnerFile)
                elif dep_used == 'android':
                    self.updateRunnerDependency(dep[0], runnerFile)

                with open(buildGradleFile, 'w') as f:
                    f.write(gradle_file)


    def updateRunnerText(self, text, newRunner):
        updatedText = ""
        dependency = None

        for i, line in enumerate(text.split("\n")):
            print(i, line)
            if not 'testInstrumentationRunner' in line:
                updatedText += line + "\n"
            else:
                if 'androidx' in line:
                    dependency = 'androidx'
                else:
                    dependency = 'android'
                line = line.split(" ")
                line = [l for l in line if l]  # remove empty strings
                print(line)
                newLine = line[0] + " \"" + newRunner + "\""
                updatedText += newLine + "\n"

        return (updatedText, dependency)


    #Uncomment androidx or android import for AndroidJUnitRunner in custom runner
    def updateRunnerDependency(self, dep, runnerFile):
        newFile = ""
        with open(runnerFile, 'r') as f:
            content = f.readlines()
            for line in content:
                if dep in line:
                    newLine = line.replace("//", "")
                    newFile += newLine
                else:
                    newFile += line

        with open(runnerFile, 'w') as f:
            f.write(newFile)


class GradleBuilder:
    def __init__(self):
        pass

    def copy_local_prop(self, property_file, gradle_dir):
        name = property_file.split("/")[-1]
        path = os.path.join(gradle_dir, name)
        shutil.copyfile(property_file, path)

    def execAsSudo(self, command, app_repo):
        command = command.split()
        build = subprocess.Popen(command, stdout=subprocess.PIPE, cwd=app_repo)
        build_output = build.stdout.read().decode()
        print(build_output)

    def execSudoAndReturn(self, command, app_repo, previous_app_repo=None):
        command = command.split()
        build = subprocess.Popen(command, stdout=subprocess.PIPE, cwd=app_repo)
        build_output = build.stdout.read().decode()
        return build_output

    # find the gradlew folder to build the app
    def findGradleFolder(self, app_repo):
        for dirpath, dirnames, filenames in os.walk(app_repo):
            if "app" in dirnames and "gradlew.bat" in filenames:
                return dirpath

    def removeGradleLock(self, previous_app_repo, lock_holding_pid):
        print("Trying to remove gradle lock")
        subprocess.call("rm -rf ~/.gradle/caches/*", shell=True)
        print("removed caches")
        stop_build = subprocess.Popen(['gradle', "--stop"], stdout=subprocess.PIPE, cwd=previous_app_repo)
        cmd_out = stop_build.stdout.read().decode()
        print("cmd3")

        kill_cmd = "sudo kill -9 %s" % (lock_holding_pid)
        self.execAsSudo(kill_cmd, previous_app_repo)
        print("Killed lock holding process")

    def AssembleGradle(self, app_repo, previous_app, property_file, gradleJDK=None):
        try:
            gradle_dir = self.findGradleFolder(app_repo)
            self.copy_local_prop(property_file, gradle_dir)
            print("Gradle folder found: " + gradle_dir)
            print("Setting permissions to execute gradlew.")
            self.execAsSudo("chmod +x gradlew", gradle_dir)

            # Can stall without sudo.
            print("Starting gradle build.")
            if gradleJDK:
                build_command = "./gradlew clean assemble assembleAndroidTest -Dorg.gradle.java.home=" + gradleJDK + " -x lint"
            else:
                build_command = "./gradlew clean assemble assembleAndroidTest -x lint "
            print(build_command)
            build_output = self.execSudoAndReturn(build_command, gradle_dir)
            print(build_output)

            if "BUILD SUCCESSFUL in " in build_output:
                success = True
            elif "Timeout waiting to lock " in build_output:
                lock_holding_pid = re.search("Owner PID: \d*", build_output)
                digit_list = filter(str.isdigit, lock_holding_pid)
                lock_holding_pid = "".join(lock_holding_pid)
                if previous_app:
                    self.removeGradleLock(previous_app, lock_holding_pid)
                    # try building again
                    build_output = self.execSudoAndReturn(build_command, gradle_dir)
                    print(build_output)
                    if "BUILD SUCCESSFUL in " in build_output:
                        success = True
                    else:
                        success = False
            else:
                success = False

        except Exception as e:
            success = False

        return (success, gradle_dir, build_output)
