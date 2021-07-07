import datetime,os
from config import getInstrumentHandler,getScanner
from utils.action import Action
import h5py
import numpy as np
import shutil

def makeDir(filepath,count):
    try:
        filePath = filepath+str(count)
        os.mkdir(filePath)
    except:
        filePath = makeDir(filepath,count+1)
    return filePath


class ExperimentOutput():
    def __init__(self,experimentName):
        self._metadata = experimentName
        directory = os.path.join(os.path.dirname(os.path.realpath(__file__)),os.path.join('outputs',experimentName+'-'+str(datetime.datetime.now().date())))
        self._directory = makeDir(directory,0)
        self._mainModuleFile = os.path.join(self._directory,'MainExp.txt')
        self._actionCount = 1
        self.create_config()
        self._fileNameh = os.path.join(self._directory,'OscData.hdf5')

    def create_config(self):
    ############add files that need to be copied to new folder of experiment#########
        files_to_copy = ["replay.py","replay.bat","heatmap_plot.bat","heatmap.py"]
        for file in files_to_copy:
            shutil.copyfile(os.path.join("data_processing",file), os.path.join(self._directory,file))
    ###############copying the config file###########################################
        filename = os.path.join(self._directory,"config.py")
        file = open(filename,"a")
        configfile = open("config.py","r")
        ignore_lines = ["","from","def","scanner"]
        file.writelines("from ctypes import * \n")
        for i in configfile.readlines():
            if i.split(" ")[0] not in ignore_lines:
                file.writelines(i)
        file.close()
        configfile.close()
    
###   This is where all the output is handled and this is where we change the data logging and storing modules
    def addStepData(self,action,output):
        actionData = 'TimeStamp:'+str(datetime.datetime.now())+', Instrument:'+action._instName+', Action Type:'+action._actionType+', Action Data:'+str(action._actionData)
        if output[0]:
            actionData= actionData+': Success'
            if output[1]:   
                fileName = os.path.join(self._directory,'GetDataOsc'+str(datetime.datetime.now().date())+'_'+str(self._actionCount)+'.txt')
                actionData= actionData+'File:GetDataOsc'+str(datetime.datetime.now().date())+'_'+str(self._actionCount)
                outputData = output[1][0]
                h5data = np.array([outputData[0],outputData[1]])
                fileh = h5py.File(self._fileNameh, "a")
                fileh.create_dataset(f"step-{self._actionCount}", h5data.size, dtype='f',data = h5data)
                print(outputData)
                file = open(fileName,"a")
                for i in  range(len(outputData[0])):
                    file.writelines(str(outputData[0][i])+' , '+str(outputData[1][i])+'\n')
                file.close()
                fileh.close()
                self._actionCount +=1

                
        else:
            actionData= actionData+': Failure'
        file = open(self._mainModuleFile,"a")
        file.writelines(actionData+'\n')
        file.close()
    

        



class Experiment():
    def __init__(self,experimentName,experimentMetaData=None):
        self._metaData = experimentMetaData
        self._output = ExperimentOutput(experimentName)
        self._actions = []
        self.instHandler = getInstrumentHandler()
        self.scanner = getScanner()

    def loadScanner(self):
        self._actions = self.scanner.compile()
    
    def printActions(self):
        for action in self._actions:
            print(action)

    def addAction(self,instName,actionType,actionData):
        self._actions.append(Action(instName,actionType,actionData))

    def addActionFunction(self,actionfunc):
        self._actions = actionfunc()

    def runExperiment(self):
        for currAction in self._actions:
            #try:## add level of failure as well , by returning strings
            print(currAction)
            currOutput  = self.instHandler.runAction(currAction)
            print(f'Output for action {currAction._actionType} with data {currAction._actionData} is {currOutput}')
            self._output.addStepData(currAction,currOutput)
            #except:
              #  print(f"Action {currAction._actionType} for instrument {currAction._instName} failed to execute" )

if __name__=="__main__":
    exp = Experiment('myfirstday')
    exp.loadScanner()
    exp.runExperiment()