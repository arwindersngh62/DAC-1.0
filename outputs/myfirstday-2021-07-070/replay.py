from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg 
import os
import config
import h5py
from scipy import stats
path = 'OscData.hdf5'
fileh = h5py.File(path, "r")
def get_data(count):
    data = fileh[f"step{count}"]
    data  = data[14500:15500]
    #print(data.shape)
    #mid  = max(data)+min(data)/2
    mid = stats.mode(data) 
    print(mid)
    data = data - mid[0]
    return data
count = 4000
app = QtGui.QApplication([])
win = pg.GraphicsLayoutWidget(show=True, title="Replay")
win.resize(2000,1200)
win.setWindowTitle('Replay')
p6 = win.addPlot(title="Recorded data")
p6.addLegend()
p6.setRange(yRange=[-0.0001,.01])
curve = p6.plot(pen='y')
plotItem = pg.PlotDataItem(name='dataset')
p6.addItem(plotItem)

data = np.random.normal(size=(10,1000))
ptr = 0

axes  = config.axes
axes_ticks = []
steps = []
print(axes)
axis_map = {'X':0,'Y':1,'Z':2}
for i in axes:
    index = axis_map[i]
    steps = (int(abs(config.stopCoords[index] - config.startCoords[index])/config.step_size[index]+1))
class iterator():
    def __init__(self):
        self._start_coords = config.startCoords
        self._stop_coords = config.stopCoords
        self._step_size = config.step_size
        self.current = config.startCoords.copy()
        self._axes = config.axes
        self._axis_map = {'X':0,'Y':1,'Z':2}
    
    def reset(self):
        self.current = self._start_coords.copy()

    def step(self,input):
        #print(self.current)
        if input >= len(self._axes):
            self.reset()
            return(self.current)
        else:
            index = self._axis_map[self._axes[input]]
        #print(f"start coordinates are : {self._start_coords}")
        next = self.current
        next[index] = self.current[index] + self._step_size[index]
        if next[index] > self._stop_coords[index]:
            self.current[index] = self._start_coords[index]
            return(self.step(input+1))

        else:
            self.current = next
            return(next)
iter = iterator()
background = get_data(count)
count+=1
def update():
    
    global curve, data, ptr, p6,count,iter,plotItem,background
    a = get_data(count)
    #super_threshold_indices = a < 0.000001
    #a[super_threshold_indices] = 0
    new = iter.step(0)
    print(new)
    p6.legend.removeItem(plotItem)
    p6.legend.addItem(plotItem, f"x={new[0]},y={new[1]}")
    curve.setData(a-background)

    #if ptr == 0:
     #   p6.enableAutoRange('', False)  ## stop auto-scaling after the first data set is plotted
    count += 1
    print(count)
    if count >10201:
        count = 1
if __name__ == "__main__":
    timer = QtCore.QTimer() 
    timer.timeout.connect(update)
    timer.start(100)
    QtGui.QApplication.instance().exec_()
