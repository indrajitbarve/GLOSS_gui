# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 11:31:08 2019

@author: Indrajit
"""

import FileDialog
import matplotlib as mpl
mpl.use('TkAgg')
import numpy as np
import pylab as pl
import scipy.ndimage.interpolation as spndint
import scipy.optimize as spfit
from matplotlib.widgets import Slider, Button
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.cm as cm
import matplotlib.image as plimg
from ScrolledText import ScrolledText


from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
try:
  import Tkinter as Tk
except:
  import tkinter as Tk


from matplotlib.backend_bases import NavigationToolbar2
import tkFileDialog
from tkMessageBox import showinfo
import os
import time
import sys

__version__ = '1.1-b'


class gloss_data_analysis(object):


  def quit(self,event=None):
  
    self.tks.destroy()
    sys.exit()

  def __init__(self,antenna_file="",model_file="",tkroot=None):

    self.__version__ = __version__

  #  if tkroot is None:
  #    self.tks = Tk.Tk()
  #  else:
    self.tks = tkroot
    self.tks.protocol("WM_DELETE_WINDOW", self.quit)
    self.Hfac = np.pi/180.*15.
    self.deg2rad = np.pi/180.
    self.curzoom = [0,0,0,0]
    self.robust = 0.0
    self.deltaAng = 1.*self.deg2rad
    self.gamma = 0.5  # Gamma correction to plot model.
    self.lfac = 1.e6   # Lambda units (i.e., 1.e6 => Mlambda)
    self.ulab = r'U (M$\lambda$)'
    self.vlab = r'V (M$\lambda$)'
    self.W2W1 = 1.0  # Relative weighting for subarrays.
    self.currcmap = cm.jet

    self.GUIres = True # Make some parts of the GUI respond to events
    self.antLock = False # Lock antenna-update events

    self.myCLEAN = None  # CLEANer instance (when initialized)

# Default of defaults!
    nH = 200
    Npix = 512   # Image pixel size. Must be a power of 2
    DefaultMod = 'Nebula.model'
    DefaultArray = 'Long_Golay_12.array'

# Overwrite defaults from config file:
#    d1 = os.path.dirname(os.path.realpath(__file__))
    d1 = os.path.dirname(os.path.realpath(sys.argv[0]))
    print d1

#   execfile(os.path.join(os.path.basename(d1),'APSYNSIM.config'))
    try:
      conf = open(os.path.join(d1,'APSYNSIM.config'))
    except:
      d1 = os.getcwd()
      conf = open(os.path.join(d1,'APSYNSIM.config'))
      
    for line in conf.readlines():
      temp=line.replace(' ','')
      if len(temp)>2:
         if temp[0:4] == 'Npix':
           Npix = int(temp[5:temp.find('#')])
         if temp[0:2] == 'nH':
           nH = int(temp[3:temp.find('#')])
         if temp[0:10] == 'DefaultMod':
           DefaultModel = temp[12:temp.find('#')].replace('\'','').replace('\"','')
         if temp[0:12] == 'DefaultArray':
           DefaultArray = temp[14:temp.find('#')].replace('\'','').replace('\"','')

    conf.close()

# Set instance configuration values:
    self.nH = nH
    self.Npix = Npix

    self.datadir = os.path.join(d1,'..','PICTURES')
    self.arraydir  = os.path.join(d1,'..','ARRAYS')
    self.modeldir  = os.path.join(d1,'..','SOURCE_MODELS')
    self.userdir  = os.path.join(d1,'..','SAVED_IMAGES')

 # Try to read a default initial array:
    if len(antenna_file)==0:
      try:
        antenna_file = os.path.join(self.arraydir,DefaultArray)
      except:
        pass

 # Try to read a default initial model:
    if len(model_file)==0:
      try:
        model_file = os.path.join(self.modeldir,DefaultModel)
      except:
        pass


    self.lock=False
    self._onSphere = False
#
#    self.readModels(str(model_file))
#    self.readAntennas(str(antenna_file))
#    self.GUI() #makefigs=makefigs)






if __name__ == "__main__":

  root = Tk.Tk()
  TITLE = 'GLOSS TYPE II data analysis tool  %s'%__version__
  root.wm_title(TITLE)


  myint = gloss_data_analysis(tkroot=root)
  Tk.mainloop()
