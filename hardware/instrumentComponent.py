import sys
#sys.path.append(r'C:\Users\slla\Dropbox\DTU\PhD\code\dtu')
#sys.path.append(r'C:\Users\slla\Dropbox\DTU\PhD\code\dtu\icontrol')
import os
from ctypes import *
from . import motion_controllers
from .oscilloscopes import Tektronix_DPO4102B
import datetime
from time import sleep

# instrument list is like a dictionary , where key is the name of instrument and value is instrument parameters,first parameter is the type of instrument.
class instrumentHandler():
    def __init__(self):
        self._inst = {}
        self._outputData = None
        self._inst['SYSTEM'] = System()
        
    def add_instrument(self,instData):
        if instData[0] == 'KinesisController':
            self._inst[instData[1]] = thorlabsKinesisMotionController(instData[2])

        if instData[0] == 'Tektronix_DPO4102B':
            self._inst[instData[1]] = techtronixOsc(instData[2]['ipAddress'])
        
    def runAction(self,action):
        if action._actionType in self._inst[action._instName].getActions():
            return(self._inst[action._instName].doAction(action))


class System():
    def __init__(self):
        self._actions = ['Wait']
    
    def doAction(self,action):
        if action._actionType=='Wait':
            try:
                sleep(action._actionData[0])
                return [True,[]]
            except:
                return [False,[]]
    
    def getActions(self):
        return self._actions



#FutureWork:This class just needs to be wrapper class for a lower level functionality, so if possible the refernce to dll directory should be moved to a lower level layer.
class thorlabsKinesisMotionController():
    def __init__(self,autoCreationData): # stageDate = [[stageName,stageType,serialNumber,stageCoord],[...],[...],..]{createStages,stageData,homeStages}
        #os.chdir(r"C:\Program Files\Thorlabs\Kinesis")
        #self._lib = cdll.LoadLibrary("Thorlabs.MotionControl.KCube.DCServo.dll")
        #self._lib.TLI_BuildDeviceList()
        self._stageData = {}
        self._stages = {}
        self._axis = {}
        self._actions =['MoveToCoords','MoveStage']
        if autoCreationData['createStages']:
            for stage in autoCreationData['stageData']:
                if autoCreationData['homeStages']:
                    self._stages[stage[0]] = (motion_controllers.KinesisController(serialNumber=stage[2], stageType=stage[1], stageName=stage[0], HomeStage=True))
                    self._axis[stage[3]] = stage[0]
                else:
                    self._stages[stage[0]] = (motion_controllers.KinesisController(serialNumber=stage[2], stageType=stage[1], stageName=stage[0], HomeStage=False))
                    self._axis[stage[3]] = stage[0]
    

    def addStage(self,stageName,stageType):
        self._stageData[stageName] = stageType

    def initStage(self,stageName,serialNumber):
        self._stages[stageName] = (motion_controllers.KinesisController(serialNumber=serialNumber, stageType=self._stageData[stageName], stageName=stageName, HomeStage=True))

    def initUnhomedStage(self,stageName,serialNumber):
        self._stages.append(motion_controllers.KinesisController(serialNumber=serialNumber, stageType=self._stageData[stageName], stageName=stageName, HomeStage=False))

    def initAllStages(self,serialNumDict):
        for stage in self._stageData.keys():
            self._stages.append(motion_controllers.KinesisController(serialNumber=serialNumDict[stage], stageType=self._stageData[stage], stageName=stage, HomeStage=True))

    def initAllUnHomedStages(self,serialNumDict):
        for stage in self._stageData.keys():
            self._stages.append(motion_controllers.KinesisController(serialNumber=serialNumDict[stage], stageType=self._stageData[stage], stageName=stage, HomeStage=False))

    def assignAxis(self,stageName,axis):
        self._axis[axis] = stageName


    def moveToCoords(self,coords):
        self._stages[self._axis['X']].move_device(position=coords[0])
        self._stages[self._axis['Y']].move_device(position=coords[1])
        self._stages[self._axis['Z']].move_device(position=coords[2])

    def doAction(self,action):
        if action._actionType=='MoveToCoords':
            try:
                self.moveToCoords(action._actionData[0])
                return [True,[]]
            except:
                return [False,[]]
        if action._actionType=='MoveStage':
            try:
                self._stages[action._actionData[0]].move_device(position=action._actionData[1][0])
                return [True,[action._actionData[1][0]]]
            except:
                return [False,[]]

    
    def getActions(self):
        return self._actions
            


class techtronixOsc():
    def __init__(self,ipAddress):
        self._ipAddress = ipAddress
        self._osc = Tektronix_DPO4102B(self._ipAddress)
        self._maxNumOscPoints = self._osc.get_horizontal_record_length()
        self._oscConnected = True
        self._actions = ['SET_ACQ_MODE','GET_DATA','SET_ACQ_STATE','GET_ACQ_PARAMS']
    #mode = enum('AVE',..)
    #numOscAverages is a part of optional arguments which can be added depending upon the required parameters for a mode
    def doAction(self,action):
        if action._actionType == 'SET_ACQ_MODE':
            actionData = action._actionData
            try:
                output = self.setAcqMode(actionData[0],actionData[1])
                return [True,[]]
            except:
                return[False,[]]

        if action._actionType == 'SET_ACQ_STATE':
            actionData = self.setAcqState(action._actionData[0])
            try:
                return [True,[]]
            except:
                return [False,[]]

        if action._actionType == 'GET_DATA':
            actionData = self.getData(action._actionData[0])
            try:
                return [True,[actionData]]
            except:
                return [False,[]]
        
        if action._actionType == 'GET_ACQ_PARAMS':
            actionData = self.getAcqParams()
            try:
                return [True,[actionData]]
            except:
                return [False,[]]
        

    def setAcqMode(self,AcqMode,numOscAverages):
        if self._oscConnected:
            self._osc.set_acquisition_mode(mode=AcqMode)
            self._osc.set_number_averages(averages=numOscAverages)

    def setAcqState(self,AcqState):
        if self._oscConnected:
            self._osc.set_acquisition_state(state=AcqState)

    def getData(self,channel):
        return(self._osc.get_data(channel))

    def getActions(self):
        return self._actions

    def getAcqParams(self):
        return(self._osc.query_all_acquisition())
    ## def querry busy():