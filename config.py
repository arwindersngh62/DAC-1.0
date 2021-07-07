from ctypes import *
from hardware.instrumentComponent import instrumentHandler
from utils.modules import Scanner
instruments = []
#################Change Configurations Here ################################################
#Please do not delete any lines!!!!!!!!!!
#If you do not want any line to be considered for the purpose of an expriment you can comment 
# it out by putting a '#' at the start of the line.
########################## Add Oscilloscopes  ##############################################
#here you can add oscilloscopes with different configuration currently only the DPO4102B model 
#of techtronics is programmed
# data format of oscilloscope setup is ['Model of scope','Name (user decided) for the scope','ip address of osc']
data = ['Tektronix_DPO4102B','ScanOsc',{'ipAddress':'192.168.1.5'}] 
#Instrument added to the list of intruments
instruments.append(data)


########################## Add kinesis stages ##############################################
#Here you can add kinesis stages 
stageData = []
# the format for stage data below is: ['name of stage','type of stage',serial_number,axis of the stage]
# There can only be one 'X','Y'and 'Z' axis each but there can be multiple 'R' axis stages
#stage type can be linear of roational
#more stages can be added or removed by adding or commenting out lines of the form 'stageData.append([....])'
stageData.append(['X-Stage','linear',c_char_p(b'27256338'),'X'])
stageData.append(['Y-Stage','linear',c_char_p(b'27255894'),'Y'])
#stageData.append(['Z-Stage','linear',c_char_p(b'27005114'),'Z'])
stageData.append(['rotating','rotational',c_char_p(b'27005004'),'R'])
stageData.append(['wiregrid','rotational',c_char_p(b'27255354'),'R'])
##############################################################################################
#the line below is used to set the overall parameters, currently only homestages is an editable parameter
#you can set home stages to be true or false ,deepending upon if stages need to be homed
data = ['KinesisController','ScanStage',{'createStages':True,'stageData':stageData,'homeStages':False}]  
instruments.append(data)


######################### Scan Config #######################################################
#here you can set things about the scan
moduleType = '2DScan'     #this decided the type of the scan it can be 1DScan,2DScan,3DScan
axes = ['X','Y']           #you can add axes here the first axes will be the major axis and others will be considered minor in that order  
startCoords = [8,13,0]    # 3D coordinates  always   
stopCoords = [10,14,0]     #  3D coordinates  always 
step_size =  [1,1,1]  #step sizes for each axis
scanStage = 'ScanStage'    #name of the instrument to use as stage for the scan
scanReader = 'ScanOsc'     #name of the instrument  to use as reader for the scan     
stageSettleTime = 0.5       #time to wait for stage to finish movement
resolution = 100             #This is the resolution of step size of the scan this must be larger than 10^n where n is the number of decimal places in the smallest step size of all axis.
scanner = Scanner(moduleType,axes,startCoords,stopCoords,step_size,scanStage,scanReader,stageSettleTime,1000)

###########################Do not change anything after this point##############################
def getInstrumentHandler():
    instHandler = instrumentHandler()
    for inst in instruments:
        instHandler.add_instrument(inst)
    return instHandler

def getScanner():
    global scanner
    return scanner    







