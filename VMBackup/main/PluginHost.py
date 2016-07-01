import time
import sys
import threading
import ConfigParser


    # [pre_post]
    # "timeout" : (in minutes),
    #
    # .... other params ...
    #
    # "pluginName0" : "oracle_plugin",      the python plugin file will have same name
    # "pluginPath0" : "/abc/xyz/"
    # "pluginConfigPath0" : "sdf/sdf/abcd.json"
    #
    #
    # errorcode policy
    # errorcode = 0, means success, script runs without error, warnings maybe possible
    # errorcode = 5, means timeout
    # errorcode = 10, config file not found
    # errorcode = process return code, means bash script encountered some other error, like 127 for script not found


class PluginHostError(object):
    def __init__(self, errorCode, pluginName):
        self.errorCode = errorCode
        self.pluginName = pluginName

    def __str__(self):
        return 'Plugin :- ', self.pluginName , ' ErrorCode :- ' + str(self.errorCode)


class PluginHostResult(object):
    def __init__(self):
        self.errors = []
        self.anyScriptFailed = False
        self.continueBackup = True
        self.errorCode = 0
        self.fileCode = []
        self.filePath = []

    def __str__(self):
        errorStr = ''
        for error in self.errors:
            errorStr += (str(error)) + '\n'
        errorStr += 'Final Error Code :- ' + str(self.errorCode) + '\n'
        errorStr += 'Any script Failed :- ' + str(self.anyScriptFailed) + '\n'
        errorStr += 'Continue Backup :- ' + str(self.continueBackup) + '\n'
        return errorStr


class PluginHost(object):
    """ description of class """
    def __init__(self, logger):
        self.logger = logger
        self.modulesLoaded = False
        self.configLocation = ''
        self.timeout = 10
        self.plugins = []
        self.pluginName = []
        self.noOfPlugins = 0
        self.preScriptCompleted = []
        self.preScriptResult = []
        self.postScriptCompleted = []
        self.postScriptResult = []

    def load_modules(self):

            # Imports all plugin modules using the information in config.json
            # and initializes basic class variables associated with each plugin


        try:
            config = ConfigParser.ConfigParser()
            config.read(self.configLocation)
        except Exception as err:
            self.logger.log('Error in PluginHost config file. '+str(err),True,'Error')
            return
        self.timeout = int(config.get('pre_post','timeout'))
        len = int(config.get('pre_post','numberOfPlugins'))
        while self.noOfPlugins < len:
            pname = config.get('pre_post','pluginName'+str(self.noOfPlugins))
            ppath = config.get('pre_post','pluginPath'+str(self.noOfPlugins))
            pcpath = config.get('pre_post','pluginConfigPath'+str(self.noOfPlugins))
            sys.path.append(ppath)
            plugin = __import__(pname)
            self.plugins.append(plugin.ScriptRunner(logger=self.logger,name=pname,configPath=pcpath))
            self.noOfPlugins = self.noOfPlugins + 1
            self.pluginName.append(pname)
            self.preScriptCompleted.append(False)
            self.preScriptResult.append(None)
            self.postScriptCompleted.append(False)
            self.postScriptResult.append(None)
        self.modulesLoaded = True

    def pre_script(self):

            # Runs pre_script() for all plugins and maintains a timer


        self.logger.log('Loading script modules now...',True,'Info')
        self.load_modules()
        result = PluginHostResult()
        if not self.modulesLoaded:
            result.errorCode = 10
            return result

        self.logger.log('Modules loaded successfully...',True,'Info')
        self.logger.log('Starting prescript for all modules.',True,'Info')
        curr = 0
        for plugin in self.plugins:
            t1 = threading.Thread(target=plugin.pre_script,args=(curr,self.preScriptCompleted,self.preScriptResult,))
            t1.start()
            curr = curr + 1

        flag = True
        for i in range(0,6*(self.timeout)):
            time.sleep(10)
            flag = True
            for j in range(0,self.noOfPlugins):
                flag = flag&self.preScriptCompleted[j]
            if flag:
                break


        continueBackup = True
        for j in range(0,self.noOfPlugins):
            ecode = 5
            continueBackup = continueBackup&self.preScriptResult[j].continueBackup
            if self.preScriptCompleted[j]:
                ecode = self.preScriptResult[j].errorCode
            if ecode != 0:
                result.anyScriptFailed = True
            presult = PluginHostError(errorCode=ecode,pluginName=self.pluginName[j])
            result.errors.append(presult)
        result.continueBackup = continueBackup
        self.logger.log('Finished prescript execution from PluginHost side. Continue Backup: '+str(continueBackup),True,'Info')
        return result

    def post_script(self):

            # Runs post_script() for all plugins and maintains a timer


        result = PluginHostResult()
        if not self.modulesLoaded:
            self.logger.log('PluginHost config file error.', True, 'Info')
            result.errorCode = 10
            return result

        self.logger.log('Starting postscript for all modules.',True,'Info')
        curr = 0
        for plugin in self.plugins:
            t1 = threading.Thread(target=plugin.post_script,args=(curr,self.postScriptCompleted,self.postScriptResult,))
            t1.start()
            curr = curr + 1

        flag = True
        for i in range(0,6*(self.timeout)):
            time.sleep(10)
            flag = True
            for j in range(0,self.noOfPlugins):
                flag = flag&self.postScriptCompleted[j]
            if flag:
                break

        for j in range(0,self.noOfPlugins):
            ecode = 5
            if self.postScriptCompleted[j]:
                ecode = self.postScriptCompleted[j].errorCode
            presult = PluginHostError(errorCode=ecode,pluginName=self.pluginName[j])
            result.errors.append(presult)
        self.logger.log('Finished prescript execution from PluginHost side.',True,'Info')
        return result


