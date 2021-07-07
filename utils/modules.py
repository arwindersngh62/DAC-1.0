from .action import Action

class Scanner():
    def __init__(self,mod_type,axes,startCoords,stopCoords,steps,scanStage,scanReader,stageSettleTime,resolution):
        self._type = mod_type
        type_dict = {'1DScan': self.scan1D,'2DScan':self.scan2D ,'3DScan':self.scan3D}
        self._axisMap = {'X':0,'Y':1,'Z':2}
        self._static  = type_dict[mod_type]
        type_dict.clear()
        self._axes = axes
        self.startCoords = startCoords
        self.stopCoords = stopCoords
        self.steps = steps
        self.scanStage = scanStage
        self.scanReader = scanReader
        self.stageSettleTime =stageSettleTime
        self._resolution = resolution
        self._actions = []

    def scan(self,axis,actions):
        temp_actions =[]
        index = self._axisMap[axis]
        startCoords = self.startCoords[index]
        stopCoords = self.stopCoords[index]
        steps = self.steps[index]
        temp_actions.append(Action(self.scanStage,'MoveStage',[f'{axis}-Stage',[startCoords]]))
        coords = []
        for step in range(int((startCoords+steps)*self._resolution),int((stopCoords+steps)*self._resolution),int(steps*self._resolution)):
            temp_actions+=actions
            coord = step/self._resolution
            temp_actions.append(Action(self.scanStage,'MoveStage',[f'{axis}-Stage',[step]]))
            temp_actions.append(Action('SYSTEM','Wait',[self.stageSettleTime]))
        temp_actions+=actions
        coords.append(coord)
        return [temp_actions,coords]
        
    def add_read_actions(self):
        actions =[]
        actions.append(Action(self.scanReader,'SET_ACQ_STATE',['STOP']))
        actions.append(Action('SYSTEM','Wait',[0.5]))
        actions.append(Action(self.scanReader,'GET_DATA',[2]))
        actions.append(Action(self.scanReader,'SET_ACQ_STATE',['RUN']))
        return actions


    def scan1D(self):
        return self.scan(self._axes[0],self.add_read_actions())[0]

    def scan2D(self):
        return self.scan(self._axes[0],self.scan(self._axes[1],self.add_read_actions())[0])[0]

    def scan3D(self):
        return self.scan(self._axes[0],self.scan(self._axes[1],self.scan(self._axes[2],self.add_read_actions())[0])[0])[0]
        
    def get_actions(self):
        return (self._actions)

    def initiate(self):
        for axis in self._axes:
            index = self._axisMap[axis]
            self._actions.append(Action(self.scanStage,'MoveStage',[f'{axis}-Stage',self.startCoords[index]]))

    def compile(self):
        #self.initiate()
        self._actions += self._static()
        #print(self._actions)
        return(self._actions)


        