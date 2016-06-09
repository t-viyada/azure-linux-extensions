import json
import time
import sys
import threading

"""
	config.json --------structure---------
	{
		"timeout" : (in minutes),

		.... other params ...

		"plugins" : [
			{
				"pluginName" : "oracle_plugin",      the python plugin file will have same name
				"baseFolder" : "/abc/xyz/"
			},
		]
	}


	errorcode policy
	errorcode = 0, means success, script runs without error, warnings maybe possible
	errorcode = 5, means timeout
	errorcode = process return code, means bash script encountered some other error, like 127 for script not found

"""

class ControllerError(object):
	def __init__(self, errorCode, pluginName):
		self.errorCode = errorCode
		self.pluginName = pluginName

	def __str__(self):
		return 'Plugin: ', self.pluginName , ' ErrorCode: ' + str(self.errorCode)


class ControllerResult(object):
	def __init__(self):
		self.errors = []
		self.continueBackup = True
		self.fileCode = []
		self.filePath = []

	def __str__(self):
		errorStr = ''
		for error in self.errors:
			errorStr += (str(error)) + '\n'
		return errorStr


class Controller(object):
	""" description of class """
	def __init__(self, logger):
		self.logger = logger
		self.timeout = 10
		self.plugins = []
		self.pluginName = []
		self.noOfPlugins = 0
		self.preScriptCompleted = []
		self.preScriptResult = []
		self.postScriptCompleted = []
		self.postScriptResult = []

	def load_modules(self):
		"""
			Imports all plugin modules using the information in config.json
			and initializes basic class variables associated with each plugin

		"""
		configData = None
		with open('config.json', 'r') as configFile:
			configData = json.load(configFile)
		curr = 0
		self.timeout = configData['timeout']
		for pluginData in configData['plugins']:
			sys.path.append(pluginData['baseFolder'])
			plugin = __import__(pluginData['pluginName'])
			self.plugins.append(plugin.ScriptPlugin(logger=self.logger))
			self.noOfPlugins = self.noOfPlugins + 1
			self.pluginName.append(pluginData['pluginName'])
			self.preScriptCompleted.append(False)
			self.preScriptResult.append(None)
			self.postScriptCompleted.append(False)
			self.postScriptResult.append(None)

	def add_plugin(self, pluginName, baseFolder):
		"""
			Adds a new plugin module by updating config.json file
			pluginName and baseFolder are information about the new plugin

		"""
		configData = None
		with open('config.json', 'r') as configFile:
			configData = json.load(configFile)
		values = {'pluginName': pluginName, 'baseFolder': baseFolder}
		configData['plugins'].append(values)
		with open('config.json', 'w+') as configFile:
			configFile.write(json.dumps(configData))
		self.noOfPlugins = self.noOfPlugins + 1

	def pre_script(self):
		"""
			Runs pre_script() for all plugins and maintains a timer

		"""
		self.load_modules()
		curr = 0
		for plugin in self.plugins:
			t1 = threading.Thread(target=plugin.pre_script,args=(curr,self.preScriptCompleted,self.preScriptResult,))
			t1.start()
			curr = curr + 1

		flag = True
		for i in range(0,self.timeout):
			time.sleep(60)
			flag = True
			for j in range(0,self.noOfPlugins):
				flag = flag&self.preScriptCompleted[j]
			if flag:
				break

		result = ControllerResult()
		continueBackup = True
		for j in range(0,self.noOfPlugins):
			ecode = 5
			continueBackup = continueBackup&self.postScriptResult[j].continueBackup
			if self.preScriptCompleted[j]:
				ecode = self.preScriptResult[j].errorCode
			presult = ControllerError(errorCode=ecode,pluginName=self.pluginName[j])
			result.errors.append(presult)
		result.continueBackup = continueBackup
		return result

	def post_script(self):
		"""
			Runs post_script() for all plugins and maintains a timer

		"""
		curr = 0
		for plugin in self.plugins:
			t1 = threading.Thread(target=plugin.post_script,args=(curr,self.postScriptCompleted,self.postScriptResult,))
			t1.start()
			curr = curr + 1

		flag = True
		for i in range(0,self.timeout):
			time.sleep(60)
			flag = True
			for j in range(0,self.noOfPlugins):
				flag = flag&self.postScriptCompleted[j]
			if flag:
				break

		result = ControllerResult()
		result.continueBackup = True
		for j in range(0,self.noOfPlugins):
			ecode = 5
			if self.postScriptCompleted[j]:
				ecode = self.postScriptCompleted[j].errorCode
			presult = ControllerError(errorCode=ecode,pluginName=self.pluginName[j])
			result.errors.append(presult)
		return result


