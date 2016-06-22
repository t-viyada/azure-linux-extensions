import json
import subprocess
import time

"""
	config.json --------structure---------
	{
		"pluginName" : "oracleLinux",
		"timeout" : (in minutes),
		"continueBackupOnFailure" : true/false,

		... other config params ...

		"preScriptLocation" : "/abc/xyz.sh"
		"postScriptLocation" : "/abc/def.sh"
		"preScriptNoOfRetries" : 3,
		"postScriptNoOfRetries" : 2,
		"preScriptParams" : [
			... all params to be passed to prescript ...
		],
		"postScriptParams" : [
			... all params to be passed to postscript ...
		]
	}


	errorcode policy
	errorcode = 0, means success, script runs without error, warnings maybe possible
	errorcode = 5, means timeout
	errorcode = 10, config file not found
	errorcode = process return code, means bash script encountered some other error, like 127 for script not found


"""

class ScriptPluginResult(object):
	def __init__(self):
		self.errorCode = None
		self.continueBackup = True
		self.noOfRetries = 0
		self.requiredNoOfRetries = 0
		self.fileCode = []
		self.filePath = []

	def __str__(self):
		return 'ErrorCode: ' + str(self.errorCode)


class ScriptPlugin(object):
	""" description of class """
	def __init__(self, logger, name, configPath):
		self.logger = logger
		self.timeout = 10
		self.configLocation = configPath
		self.pluginName = name
		self.continueBackupOnFailure = True
		self.preScriptParams = []
		self.postScriptParams = []
		self.preScriptLocation = None
		self.postScriptLocation = None
		self.preScriptNoOfRetries = 0
		self.postScriptNoOfRetries = 0
		self.configLoaded = False
		self.get_config()

	def get_config(self):
		"""
			Get configuration information from config.json

		"""
		try:
			with open(self.configLocation, 'r') as configFile:
				configData = json.load(configFile)
		except IOError:
			self.logger.log('Error in opening '+self.pluginName+' config file.',True,'Error')
			return
		except ValueError as err:
			self.logger.log('Error in decoding '+self.pluginName+' config file. '+str(err),True,'Error')
			return
		self.timeout = configData['timeout']
		self.pluginName = configData['pluginName']
		self.preScriptLocation = configData['preScriptLocation']
		self.postScriptLocation = configData['postScriptLocation']
		self.preScriptParams = configData['preScriptParams']
		self.postScriptParams = configData['postScriptParams']
		self.continueBackupOnFailure = configData['continueBackupOnFailure']
		self.preScriptNoOfRetries = configData['preScriptNoOfRetries']
		self.postScriptNoOfRetries = configData['postScriptNoOfRetries']
		self.configLoaded = True

	def pre_script(self, pluginIndex, preScriptCompleted, preScriptResult):
		"""
			Generates a system call to run the prescript
			-- pluginIndex is the index for the current plugin assigned by controller
			-- preScriptCompleted is a bool array, upon completion of script, true will be assigned at pluginIndex
			-- preScriptResult is an array and it stores the result at pluginIndex

		"""
		result = ScriptPluginResult()
		result.requiredNoOfRetries = self.preScriptNoOfRetries
		if not self.configLoaded:
			result.errorCode = 10
			preScriptCompleted[pluginIndex] = True
			preScriptResult[pluginIndex] = result
			self.logger.log('Cant run prescript for '+self.pluginName+' . Config File error.',True,'Error')
			return

		paramsStr = ['sh',str(self.preScriptLocation)]
		for param in self.preScriptParams:
			paramsStr.append(str(param))

		self.logger.log('Running prescript for '+self.pluginName+' module...',True,'Info')
		process = subprocess.Popen(paramsStr, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		flag = True
		curr = 0
		cnt = 0
		while True:
			while process.poll() is None:
				if curr >= (2*self.timeout):
					self.logger.log('Prescript for '+self.pluginName+' timed out.',True,'Error')
					flag = False
					break
				curr = curr + 1
				time.sleep(30)
			if process.returncode is 0:
				break
			if not flag:
				break
			if cnt >= self.preScriptNoOfRetries:
				break
			self.logger.log('Prescript for '+self.pluginName+' failed. Retrying...',True,'Info')
			cnt = cnt + 1


		result.noOfRetries = cnt
		if flag:
			result.errorCode = process.returncode
			if result.errorCode!=0:
				self.logger.log('Prescript for '+self.pluginName+' failed with error code: '+str(result.errorCode)+' .',True,'Error')
			else:
				self.logger.log('Prescript for '+self.pluginName+' successfully executed.',True,'Info')
		else:
			result.errorCode = 5
			result.continueBackup = self.continueBackupOnFailure
		preScriptCompleted[pluginIndex] = True
		preScriptResult[pluginIndex] = result

	def post_script(self, pluginIndex, postScriptCompleted, postScriptResult):
		"""
			Generates a system call to run the postscript
			-- pluginIndex is the index for the current plugin assigned by controller
			-- postScriptCompleted is a bool array, upon completion of script, true will be assigned at pluginIndex
			-- postScriptResult is an array and it stores the result at pluginIndex

		"""
		result = ScriptPluginResult()
		result.requiredNoOfRetries = self.preScriptNoOfRetries
		if not self.configLoaded:
			result.errorCode = 10
			postScriptCompleted[pluginIndex] = True
			postScriptResult[pluginIndex] = result
			self.logger.log('Cant run postscript for '+self.pluginName+' . Config File error.',True,'Error')
			return

		paramsStr = ['sh',str(self.postScriptLocation)]
		for param in self.postScriptParams:
			paramsStr.append(str(param))

		self.logger.log('Running postscript for '+self.pluginName+' module...',True,'Info')
		process = subprocess.Popen(paramsStr, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		flag = True
		curr = 0
		cnt = 0
		while True:
			while process.poll() is None:
				if curr >= (2*self.timeout):
					self.logger.log('Postscript for '+self.pluginName+' timed out.',True,'Error')
					flag = False
					break
				curr = curr + 1
				time.sleep(30)
			if process.returncode is 0:
				break
			if not flag:
				break
			if cnt >= self.postScriptNoOfRetries:
				break
			self.logger.log('Postscript for '+self.pluginName+' failed. Retrying...',True,'Info')
			cnt = cnt + 1

		result = ScriptPluginResult()
		result.noOfRetries = cnt
		result.requiredNoOfRetries = self.postScriptNoOfRetries
		if flag:
			result.errorCode = process.returncode
			if result.errorCode!=0:
				self.logger.log('Postscript for '+self.pluginName+' failed with error code: '+str(result.errorCode)+' .',True,'Error')
			else:
				self.logger.log('Postscript for '+self.pluginName+' successfully executed.',True,'Info')
		else:
			result.errorCode = 5
		postScriptCompleted[pluginIndex] = True
		postScriptResult[pluginIndex] = result