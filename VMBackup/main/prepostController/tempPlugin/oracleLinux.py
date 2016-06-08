import json
import subprocess
import datetime
import os
import time
import signal

"""
	config.json --------structure---------
	{
		"pluginName" : "oracleLinux",
		"timeout" : (in minutes),
		"continueBackupOnFailure" : true/false,

		... other config params ...

		"preScriptLocation" : "/abc/xyz.sh"
		"postScriptLocation" : "/abc/def.sh"
		"preScriptParams" : [
			... all params to be passed to prescript ...
		],
		"postScriptParams" : [
			... all params to be passed to postscript ...
		]
	}


	errorcode policy
	errorcode = 0, means success, script runs without error, warnings maybe possible
	errorcode = 1, means script timed out
	errorcode = 2, means script encountered some error

"""

class ScriptPluginResult(object):
	def __init__(self):
		self.errorCode = None
		self.continueBackup = True
		self.fileCode = []
		self.filePath = []

	def __str__(self):
		return 'ErrorCode: ' + str(self.errorCode)


class ScriptPlugin(object):
	""" description of class """
	def __init__(self, logger):
		self.logger = logger
		self.timeout = 10
		self.pluginName = None
		self.continueBackupOnFailure = True
		self.preScriptParams = []
		self.postScriptParams = []
		self.preScriptLocation = None
		self.postScriptLocation = None
		self.preScriptTimeoutHandlerLocation = None
		self.postScriptTimeoutHandlerLocation = None
		self.get_config()

	def get_config(self):
		"""
			Get configuration information from config.json

		"""
		with open('config.json', 'r') as configFile:
			configData = json.load(configFile)
		self.timeout = configData['timeout']
		self.pluginName = configData['pluginName']
		self.preScriptParams = configData['preScriptParams']
		self.postScriptParams = configData['postScriptParams']
		self.continueBackupOnFailure = configData['continueBackupOnFailure']

	def pre_script(self, pluginIndex, preScriptCompleted, preScriptResult):
		"""
			Generates a system call to run the prescript
			-- pluginIndex is the index for the current plugin assigned by controller
			-- preScriptCompleted is a bool array, upon completion of script, true will be assigned at pluginIndex
			-- preScriptResult is an array and it stores the result at pluginIndex

		"""
		result = ScriptPluginResult()
		preScriptResult[pluginIndex] = result
		paramsStr = [str(self.preScriptLocation)]
		for param in self.preScriptParams:
			paramsStr.append(str(param))

		process = subprocess.Popen(paramsStr, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		flag = True
		curr = 0
		while process.poll() is None:
			if curr >= self.timeout:
				flag = False
				break
			curr = curr + 1
			time.sleep(60)

		preScriptCompleted[pluginIndex] = flag
		if flag:
			preScriptResult[pluginIndex] = result

	def post_script(self, pluginIndex, postScriptCompleted, postScriptResult):
		"""
			Generates a system call to run the postscript
			-- pluginIndex is the index for the current plugin assigned by controller
			-- postScriptCompleted is a bool array, upon completion of script, true will be assigned at pluginIndex
			-- postScriptResult is an array and it stores the result at pluginIndex

		"""
		result = ScriptPluginResult()
		postScriptResult[pluginIndex] = result
		paramsStr = [str(self.postScriptLocation)]
		for param in self.postScriptParams:
			paramsStr.append(str(param))

		process = subprocess.Popen(paramsStr, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		flag = True
		curr = 0
		while process.poll() is None:
			if curr >= self.timeout:
				flag = False
				break
			curr = curr + 1
			time.sleep(60)

		postScriptCompleted[pluginIndex] = flag
		if flag:
			postScriptResult[pluginIndex] = result