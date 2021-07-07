import os
import config
import shutil

def create_config(dir_name):
    ############add files that need to be copied to new folder of experiment#########
    files_to_copy = ["replay.py","replay.bat","heatmap_plot.bat","heatmap.py"]
    for file in files_to_copy:
        shutil.copyfile(file, os.path.join(dir_name,file))
    ###############copying the config file###########################################
    filename = os.path.join(dir_name,"config.py")
    file = open(filename,"a")
    configfile = open("config.py","r")
    ignore_lines = ["","from","def","scanner"]
    file.writelines("from ctypes import * \n")
    for i in configfile.readlines():
        if i.split(" ")[0] not in ignore_lines:
            file.writelines(i)
    file.close()
    configfile.close()

#create_config("test_exp")