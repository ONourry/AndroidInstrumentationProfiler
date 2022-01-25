import os
import subprocess
import time
import multiprocessing

from utils.util import exec
from utils.gradle import GradleParser,GradleBuilder

"""
Need # symbol, not . to run test by test
"""
def changeSignature(methodSignature):
	lastDot = methodSignature.rfind(".")
	testSignature = methodSignature[:lastDot] + "#" + methodSignature[lastDot + 1:]
	return testSignature

def startInstrument(signature, testProcess, runner):
	coverage_line = ""
	newSignature = changeSignature(signature)
	command = f"adb shell am instrument -w -e class {newSignature} {coverage_line} -e debug false  {testProcess}{runner}"
	print(command)
	output = exec(command, app_repo=".", return_output=True)
	if "OK" not in output:
		print(output)
		print("NO OK") #something wrong with the test
		#raise
	else:
		print(output)


def startProfiling(app_process,app_repo, device_output_file):
	started = False
	wait_for_process = f"adb shell 'ps | grep {app_process}' "
	while not started:
		try:
			output = subprocess.check_output(wait_for_process,shell=True)
			started = True
		except subprocess.CalledProcessError as e:
			time.sleep(0.0001)
	command = "adb shell am profile start " + app_process + " " + device_output_file
	process = subprocess.Popen(command.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=app_repo)
	print("Process started. Starting profiling...")
	print(command)


def stopProfiling(app_process):
	command = "adb shell am profile stop " + app_process
	print(command)
	exec(command)
	print("Stopped profiling")


def cleanUp(app_process):
	clear_package_data = "adb shell pm clear " + app_process
	exec(clear_package_data)
	exec("adb shell dumpsys batterystats --reset")


def stopMonitorProfiling(app_process):
	stop_keyword2 = "STOP_PROFILING_NOW"
	command = "adb logcat"
	logcat_process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
	                                universal_newlines=True, bufsize=-1)
	while True:
		nextline = logcat_process.stdout.readline()
		logcat_process.stdout.flush()
		if stop_keyword2 in nextline:
			stopProfiling(app_process)
			break
	logcat_process.terminate()
	print("FOUND STOP KEYWORD")


def startMonitorProfiling(app_process, app_repo, device_output_file):
	stop_keyword = "START_PROFILING_NOW"
	subprocess.call(["adb", "logcat", "-c"])
	command = "adb logcat"
	logcat_process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
	                                universal_newlines=True, bufsize=-1)
	while True:
		nextline = logcat_process.stdout.readline()
		logcat_process.stdout.flush()
		if stop_keyword in nextline:
			startProfiling(app_process,app_repo, device_output_file)
			break
	logcat_process.terminate()
	print("FOUND START KEYWORD")


def startSystrace(android_home, systracefile):
	print("start systrace")
	command = "python2 " + android_home + "/platform-tools/systrace/systrace.py freq idle -o " + systracefile
	systrace_process = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
	                                universal_newlines=True)
	time.sleep(3)
	return systrace_process


def stopSystrace(systrace_process):
	print("Stop Systrace")
	#stop systrace process by sending 'Enter' key input
	print(systrace_process.communicate(input="\n")[0])


def launchProcessWithMonitor(app_process, runner, systracefile, device_output_file, app_repo, android_home, signature,
							 testProcess=None):
	print("In Launch process")
	if not testProcess:
		testProcess = app_process + ".test/"
	else:
		testProcess = testProcess + "/"

	profiling_process = multiprocessing.Process(target=startMonitorProfiling,
	                                            args=(app_process,app_repo,device_output_file))
	profiling_process.start()
	stop_monitor_process = multiprocessing.Process(target=stopMonitorProfiling, args=(app_process, app_repo, False))
	stop_monitor_process.start()
	systrace_process = startSystrace(android_home, systracefile) #systrace started
	time.sleep(3)
	startInstrument(signature, testProcess, runner)
	stopSystrace(systrace_process)
	time.sleep(3)
	profiling_process.terminate()
	stop_monitor_process.terminate()
	print("Finish monitoring")


def pullTraceAndDump(device_output_file, trace_dump_file, output_dir, batteryStatsFile):
	print("pull start")
	command = "adb pull " + device_output_file
	print(f" {command}")
	process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=output_dir)
	output = process.communicate()[0].decode()

	pulled_file = os.path.join(output_dir, device_output_file.split("/")[-1])

	dump_trace = "dmtracedump -o " + pulled_file + " > " + trace_dump_file
	print(dump_trace)
	dump_batterystats = "adb shell dumpsys batterystats > " + batteryStatsFile

	i = 0
	while not os.path.isfile(pulled_file):
		time.sleep(3)
		i += 3
		if i > 10:
			return

	subprocess.Popen(dump_trace, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
	                                   universal_newlines=True,cwd=output_dir)

	subprocess.Popen(dump_batterystats, shell=True, stdout=subprocess.PIPE,
	                                     stderr=subprocess.STDOUT, universal_newlines=True, cwd=output_dir)


def cleanUpLogsInDevice(device_output_file):
	subprocess.call(["adb", "shell", "rm", "-f", device_output_file])


def profile(appRepo, outputDirectory, testSignature):
	androidHome = os.getenv('ANDROID_HOME')
	deviceOutputDir = "/data/local/tmp/"
	tracedumpFile = os.path.join(outputDirectory, "tracedump")
	systraceFile = os.path.join(outputDirectory, 'systrace')
	batteryStatsFile = os.path.join(outputDirectory, 'batterystats')

	gradleParser = GradleParser(appRepo)

	appProcess = gradleParser.get_app_process()
	testApplicationId = gradleParser.get_test_application_id()
	runner = gradleParser.get_runner()

	device_output_file = appProcess.replace(".", "_") + '.log'
	device_output_file = deviceOutputDir + device_output_file

	#clean up the logs that previous runs created
	cleanUpLogsInDevice(device_output_file)
	cleanUp(appProcess)

	print(device_output_file)
	launchProcessWithMonitor(appProcess, runner, systraceFile, device_output_file, appRepo, androidHome, testSignature,
							 testApplicationId)
	pullTraceAndDump(device_output_file, tracedumpFile, outputDirectory, batteryStatsFile)