import os
import matplotlib.pyplot as plt
import matplotlib.colors as matcols
from matplotlib import patches
import h5py
import config
import numpy as np
from scipy import stats
path = 'OscData.hdf5'
fileh = h5py.File(path, "r")
def get_data(count):
    data = fileh[f"step{count}"]
    data  = data[14500:15500]
    #print(data.shape)
    #mid  = max(data)+min(data)/2
    mid = stats.mode(data) 
    data = data - mid[0]



    return data
#fileh.close()
marks = np.empty(0)
count = 1
steps = []
axes  = config.axes
axes_ticks = []
print(axes)
axis_map = {'X':0,'Y':1,'Z':2}
for i in axes:
    index = axis_map[i]
    steps.append(int(abs(config.stopCoords[index] - config.startCoords[index])/config.step_size[index]+1))
    axes_ticks.append(np.round_(np.arange(config.startCoords[index],config.stopCoords[index],0.5),decimals=3))
    #axes_ticks.append(np.round_(np.arange(13.0,23.0,0.5), decimals = 3))
background = get_data(1)
total_steps = np.prod(steps)
for _ in range(total_steps):
    data = get_data(count)-background
    for i in range(len(data)):
        if data[i]<0:
            data[i] = 0
    data = sum(data)
    marks = np.append(marks,data)
    if count%100==0:
        print(f'{count/total_steps} completed')
    #print(new_temp)
    count+=1
marks = np.reshape(marks, steps)
fig, ax = plt.subplots()
plt.xticks(ticks = np.arange(0,100,5),labels=axes_ticks[1],rotation=90)
plt.yticks(ticks = np.arange(0,100,5),labels= axes_ticks[0])
maxpower = np.amax(marks)
hpbw = maxpower/2
x = 0
for first in marks:
    x+=1
    y=0
    inside = False
    for val in first:
        y+=1
        if val < hpbw:
            if inside == True:
                plt.plot(y,x,'b*')
                inside = False
        if val > hpbw:
            if inside:
                continue
            else:
                inside = True
                plt.plot(y,x,'g*')

hm = ax.imshow(marks, cmap='CMRmap',norm=matcols.LogNorm())
#hm = ax.imshow(marks, cmap='CMRmap')
plt.colorbar(hm)
#min_val = np.amax(marks)
#max_val = np.amin(marks)
#print(min_val,max_val)
#cbar = fig.colorbar(hm, ticks=[min_val, min_val+max_val/2, max_val])
#cbar.ax.set_yticklabels(['< -1', '0', '> 1']) 
#rect = patches.Rectangle((10, 10), 40, 30, linewidth=1,
   #                      edgecolor='r', facecolor="none")
  
# Add the patch to the Axes
#ax.add_patch(rect)

plt.show()