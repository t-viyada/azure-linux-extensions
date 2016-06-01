import json
import sys
import threading

"""
	config.json --------structure---------
	{
		"timeout" : (in minutes),

		.... other params ...

		"plugins" : [
			{
				"pluginName" : "oracle_plugin",
				"baseFolder" : "/abc/xyz/"
			},
		]
	}

"""

class ControllerError(object):
	def __init__(self):
		self.errorCode = None

	def __str__(self):
		return 'ErrorCode: ' + str(self.errorCode)

class ControllerResult(object):
	def __init__(self):
		self.errors = []
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
		self.pluginModules = []
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
		self.timeout = configData["timeout"]
		for pluginData in configData["plugins"]:
			sys.path.append(pluginData["baseFolder"])
			self.pluginModules.append(__import__(pluginData["pluginName"]))
			self.noOfPlugins = self.noOfPlugins + 1
			self.preScriptCompleted.append(False)
			self.preScriptResult.append(None)
			self.postScriptCompleted.append(False)
			self.postScriptResult.append(None)

	def add_plugin(self, values):
		"""
			Adds a new plugin module by updating config.json file
			values is a dictionary with the structure as shown in config.json file description

		"""
		configData = None
		with open('config.json', 'r') as configFile:
			configData = json.load(configFile)
		configData["plugins"].append(values)
		with open('config.json', 'w+') as configFile:
			configFile.write(json.dumps(configData))
		self.noOfPlugins = self.noOfPlugins + 1

	def pre_script(self):
		"""
			Runs pre_script() for all plugins and maintains a timer

		"""
		self.load_modules()
		curr = 0
		preScriptResult = ControllerResult()
		for param in params:
			currPlugin = self.pluginModules[curr].ScriptPlugin()
			# t1 = threading.Thread(target=currPlugin.pre_script,agrs=(curr,self.preScriptCompleted,self.preScriptResult,param,))
			t1.start()
			curr = curr + 1



	def post_script(self, params):
