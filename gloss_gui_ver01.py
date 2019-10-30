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
from scipy.signal import savgol_filter

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
from astropy.io import fits

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
    self.freq_axis=80
    self.smooth_freq=51
    self.xindx=0
    self.yindx=0
    self.st_freq=35
    self.st_freq_curr=35
    self.stp_freq=435
    self.stp_freq_curr=435
    self.freq_Hz=1e6
    self.st_time_ut=0
    self.stp_time_ut=10
    self.Nfreq = 401
    self.Nspec = 3500
#    self.ax = ax
#    self.lx = ax.axhline(color='k')  # the horiz line
#    self.ly = ax.axvline(color='k')  # the vert line
#    self.lx.set_ydata=0
#    self.ly.set_xdata=0
    
# Default of defaults!
    nH = 200
    Npix = 512   # Image pixel size. Must be a power of 2
    DefaultMod = 'Nebula.model'
    DefaultArray = 'Long_Golay_12.array'

# Overwrite defaults from config file:
#    d1 = os.path.dirname(os.path.realpath(__file__))
    d1 = os.path.dirname(os.path.realpath(sys.argv[0]))
    print(d1)

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


    self.Npix= Npix
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

#    self.readModels(str(model_file))
#    self.readAntennas(str(antenna_file))
    self.GUI() #makefigs=makefigs)


  def GUI(self): # ,makefigs=True):
    print('I am here')

    mpl.rcParams['toolbar'] = 'None'

    self.Nphf = self.Npix/2
    self.robfac = 0.0
    self.figSPEC = pl.figure(figsize=(20,16))
#    self.gs1 = self.figSPEC.add_gridspec(nrows=4, ncols=3, left=0.05, right=0.48,
#                        wspace=0.05)
    if self.tks is None:
       self.canvas = self.figSPEC.canvas
    else:
      self.canvas = FigureCanvasTkAgg(self.figSPEC, master=self.tks)
      self.canvas.show()
      menubar = Tk.Menu(self.tks)
      menubar.add_command(label="Help", command=self._getHelp)
      menubar.add_command(label="Quit", command=self.quit)

      self.tks.config(menu=menubar)
      self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
      
    self.specPlot = self.figSPEC.add_subplot(221)
    self.freqPlot = self.figSPEC.add_subplot(222)
    self.timePlot = self.figSPEC.add_subplot(223)
   # self.eventprofilePlot = self.figSPEC.add_subplot(224)
    self.specPlot.set_position([0.1,0.45,0.45,0.45])
    self.freqPlot.set_position([0.58,0.45,0.125,0.45])
    self.timePlot.set_position([0.1,0.28,0.45,0.15])   
   # self.dirtyPlot = self.figUV.add_subplot(236,aspect='equal')

    #self.spherePlot = pl.axes([0.53,0.82,0.12,0.12],projection='3d',aspect='equal')

    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    x = 10 * np.outer(np.cos(u), np.sin(v))
    y = 10 * np.outer(np.sin(u), np.sin(v))
    z = 10 * np.outer(np.ones(np.size(u)), np.cos(v))
    #self.spherePlotPlot = self.spherePlot.plot_surface(x, y, z,  rstride=4, cstride=4, color=(0.8,0.8,1.0))
    #self.spherePlot._axis3don = False
    #self.spherePlot.patch.set_alpha(0.8)
    #beta = np.zeros(100)
    #self.arrayPath = [np.zeros(self.nH), np.zeros(self.nH), np.zeros(self.nH)]
    #self.sphereArray = self.spherePlot.plot([],[],[],'y',linewidth=3)
    #self.spherePlot.set_xlim3d((-6,6))
    #self.spherePlot.set_ylim3d((-6,6))
    #self.spherePlot.set_zlim3d((-6,6))
    #self.spherePlot.patch.set_alpha(0.8)
    #self.spherePlot.elev = 45.

    self.canvas.mpl_connect('button_press_event',self.on_press)

    #self.figSPEC.subplots_adjust(left=0.01,right=0.99,top=0.95,bottom=0.071,hspace=0.15)
    #self.canvas.mpl_connect('mouse_event', self.mouse_move)
    #self.canvas.mpl_connect('motion_notify_event', self._onAntennaDrag)
    #self.canvas.mpl_connect('button_release_event',self._onRelease)
    #self.canvas.mpl_connect('button_press_event',self._onPress)
    #self.canvas.mpl_connect('key_press_event', self._onKeyPress)
    self.pickAnt = False

    self.fmtH = r'$\phi = $ %3.1f$^\circ$   $\delta = $ %3.1f$^\circ$' "\n" r'H = %3.1fh / %3.1fh'
    self.fmtBas = r'Bas %i $-$ %i  at  H = %4.2fh'
    self.fmtVis = r'Amp: %.1e Jy.   Phase: %5.1f deg.' 
    self.fmtA = 'N = %i'
    self.fmtA2 = '  Picked Ant. #%i' 
    self.fmtA3 = '\n%6.1fm | %6.1fm'

    self.wax = {}
    self.widget = {}
    self.wax['freq'] = pl.axes([0.075,0.15,0.1,0.04])
    self.wax['freq_min'] = pl.axes([0.4,0.15,0.1,0.04])
    self.wax['freq_max'] = pl.axes([0.6,0.15,0.1,0.04])
    self.wax['smooth'] = pl.axes([0.045,0.25,0.1,0.04])
    self.wax['open'] = pl.axes([0.002,0.90,0.075,0.04])
    self.wax['plot'] = pl.axes([0.003,0.8,0.075,0.04])
    self.wax['reduce'] = pl.axes([0.07,0.1,0.25,0.04])

    self.widget['freq'] = Slider(self.wax['freq'],r'frequency',self.st_freq,self.stp_freq,valinit=80.0)
    self.widget['freq_min'] = Slider(self.wax['freq_min'],r'frequency_min',self.st_freq,self.stp_freq,valinit=45.0) 
    self.widget['freq_max'] = Slider(self.wax['freq_max'],r'frequency_max',self.st_freq,self.stp_freq,valinit=155.0)
    self.widget['smooth'] = Slider(self.wax['smooth'],r'smooth',valmin=1,valmax=101,valinit=51.0)
    self.widget['open'] = Button(self.wax['open'],r' Open File')
    self.widget['plot'] = Button(self.wax['plot'],r' plot')
    self.widget['reduce'] = Button(self.wax['reduce'],r'Reduce data')
    self.widget['freq'].on_changed(self.onFreq)
    self.widget['freq_min'].on_changed(self.onFreq_min_axis_change)
    self.widget['freq_max'].on_changed(self.onFreq_max_axis_change)
    self.widget['smooth'].on_changed(self.onSmooth)    
#   self.widget['loadfile'].on_clicked(self.loadFile)
    self.widget['open'].on_clicked(self.loadFile)
    self.widget['plot'].on_clicked(self.onPlot)

    self._prepareSpec_data() 

    self.canvas.draw()  
    
    
    
  def on_press(self,event):
      
      if event.inaxes == self.specPlot:
      
        print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
          ('double' if event.dblclick else 'single', event.button,
           event.x, event.y, event.xdata, event.ydata))
        self.xindx=event.xdata
        self.yindx=event.ydata
        self._plotFreq_Time_both(self.yindx,self.xindx,redo=True)
           
           
# 
#        if event.mouseevent.inaxes == self.specPlot:          
#
#            x, y = event.xdata, event.ydata
#        # update the line positions
#            print((y))
#            print((x))
#            print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
#          ('double' if event.dblclick else 'single', event.button,
#           event.x, event.y, event.xdata, event.ydata))

        
        #self.txt.set_text('x=%1.2f, y=%1.2f' % (x, y))
        #self.ax.figure.canvas.draw()

  def _plotSpec(self,redo=True):
      
      if redo:
          self.specPlot.cla()
          self.specPlotPlot = self.specPlot.pcolormesh(self.spec_1d_time_data,self.spec_1d_freq_data,self.spec_2d_data, vmin=-50.1, vmax=-8, cmap=self.currcmap)        
          self.specPlot.set_ylabel('Frequency')
          self.specPlot.set_xlabel('TIME (UT)')
          self.specPlot.set_title('GLOSS SPEC')
          self.specPlot.set_ylim([self.st_freq,self.stp_freq])
        #  self.specPlot.set_position([0.9,0.99,0.9,0.7])
          self.specPlot.set_position([0.1,0.45,0.45,0.45])
          self.freqPlot.set_position([0.58,0.45,0.125,0.45])
          self.timePlot.set_position([0.1,0.28,0.45,0.15])          
          self.specPlot.set_adjustable('datalim')

         # left=0.05,right=0.99,top=0.95,bottom=0.07,
         
      else:
          self.specPlotPlot.set_data(self.spec_2d_data)
          self.specPlot.set_position([0.1,0.45,0.45,0.45])
          #self.specPlotPlot.norm.vmin = extr[0]
          #self.specPlotPlot.norm.vmax = extr[1]


  def _plotFreq_Time(self,freqaxis_indx,redo=True):
      
      self.freq_axis= int(freqaxis_indx)
      if redo:
         # self.freqPlot.cla()
          self.timePlot.cla()
          
          #self.freqPlotPlot = self.freqPlot.plot(self.spec_2d_data[:,self.freq_index])
          self.timePlotPlot = self.timePlot.plot(self.spec_2d_data[self.freq_axis,:])    
#          self.specPlot.set_ylabel('Frequency')
#          self.specPlot.set_xlabel('TIME (UT)')
#          self.specPlot.set_title('GLOSS SPEC')
#        #  self.specPlot.set_position([0.9,0.99,0.9,0.7])
#          self.specPlot.set_position([0.1,0.45,0.45,0.45])
#          self.freqPlot.set_position([0.58,0.45,0.125,0.45])
#          self.timePlot.set_position([0.1,0.28,0.45,0.15])          
#          self.specPlot.set_adjustable('datalim')
#          
#         # left=0.05,right=0.99,top=0.95,bottom=0.07,
#         
#      else:
#          self.specPlotPlot.set_data(self.spec_2d_data)
#          self.specPlot.set_position([0.1,0.45,0.45,0.45])
#          #self.specPlotPlot.norm.vmin = extr[0]
#          #self.specPlotPlot.norm.vmax = extr[1]
#


  def _plotFreq_Time_both(self,freqaxis_indx,timeaxis_indx,redo=True):
      
      self.freq_axis= int(freqaxis_indx)
      self.time_axis= int(timeaxis_indx)
      
      if redo:
          self.freqPlot.cla()
          self.timePlot.cla()
          
          self.freqPlotPlot = self.freqPlot.plot(self.spec_2d_data[:,self.time_axis],self.spec_1d_freq_data)
          self.timePlotPlot = self.timePlot.plot(self.spec_2d_data[self.freq_axis,:]) 
          self.freqPlot.set_ylim([self.st_freq,self.stp_freq])






  def _plotFreq_time_smooth(self,smooth_indx,redo=True):
      
      self.smooth_axis= int(smooth_indx)
      if redo:
         # self.freqPlot.cla()
          self.timePlot.cla()
          
          #self.freqPlotPlot = self.freqPlot.plot(self.spec_2d_data[:,self.freq_index])
          self.timePlotPlot = self.timePlot.plot(savgol_filter((self.spec_2d_data[self.freq_axis,:]),self.smooth_axis,3))
          





  def _getHelp(self):
    win = Tk.Toplevel(self.tks)
    win.title("Help")
    helptext = ScrolledText(win)
    helptext.config(state=Tk.NORMAL)
    helptext.insert('1.0',__help_text__)
    helptext.config(state=Tk.DISABLED)

    helptext.pack()
    Tk.Button(win, text='OK', command=win.destroy).pack()
    
    
    
  def _prepareSpec_data(self):
    
    self.spec_2d_data = np.zeros((self.Nspec,self.Nfreq),dtype=np.float32)
    self.spec_1d_freq_data = np.linspace(self.st_freq,self.stp_freq,self.Nfreq)
    self.spec_1d_time_data = np.linspace(0,self.Nspec,self.Nspec)
    

  def loadFile(self,fits_specdata):
      print('I am here')
      self.specPlot.cla()
      self.freqPlot.cla()
      self.timePlot.cla()
      
      fits_file = tkFileDialog.askopenfilename(title='GLOSS Fits file...',initialdir=self.arraydir)
      self.lock=False    
      if '.fits' in fits_file:
        #time()
       # text.insert(tk.END,now + '...You selected a fits file correctly'+'\n')
        data =fits.open(fits_file)
        hdr=data[0].header
        
        #Output_image_folder=os.getcwd()
        if 'GLOSS' in hdr['OBJECT']:
                 
                self.time_freq=data[1].data
    
                self.spec_2d_data=data[0].data
           #  readspec(self,readSpec_data)
#            enabling()
#            time()
#            text.insert(tk.END, now +'...You selected the correct GLOSS fits file'+'\n')
            #return fits_file.name
        else:
            messagebox.showerror('Error','Only GLOSS fits supported')
            time()
#            text.insert(tk.END,now +'...Error ######## Only GLOSS fits supported'+'\n','warning')
              
      else:
        messagebox.showerror('Extension Error','You chose a wrong file!! Please choose a fitsfile')
        time()
#        text.insert(tk.END,now +'...Extension Error ######## You chose a wrong file!! Please choose a fitsfile'+'\n','warning')
                 
        return None
  def onFreq(self,freqaxis_indx):
     print(' I am here changing freq %s ')    
     
     self._plotFreq_Time(freqaxis_indx,redo=True)
     
    
  def onFreq_min_axis_change(self,freq_min_axis_indx):
      
      redo=True
      
      if redo:
          self.st_freq_curr=freq_min_axis_indx      
          self.specPlot.set_ylim([self.st_freq_curr,self.stp_freq_curr])
     
      else:
        
          self.specPlot.set_ylim([self.st_freq_curr,self.stp_freq_curr])
     
     
  def onFreq_max_axis_change(self,freq_max_axis_indx):
      redo=True
      
      if redo:
          self.stp_freq_curr=freq_max_axis_indx      
          self.specPlot.set_ylim([self.st_freq_curr,self.stp_freq_curr])
     
      else:
        
          self.specPlot.set_ylim([self.st_freq_curr,self.stp_freq_curr])
     
  def onSmooth(self,smooth_indx):
     print(' I am here changing freq %s ')
     self._plotFreq_time_smooth(smooth_indx,redo=True)   
     
  def onPlot(self,specplot):
      
      print('I am plotting')
      
      self._plotSpec(redo=True)
      
  def get_hours(self,time_str):
        self.hr, self.min, self.sec = self.time_str.split(':')
        return int(h) + int(m)/ 60.0 + int(s)/3600.0      
            
 

if __name__ == "__main__":

  root = Tk.Tk()
  TITLE = 'GLOSS TYPE II data analysis tool  %s'%__version__
  root.wm_title(TITLE)


  myint = gloss_data_analysis(tkroot=root)
  Tk.mainloop()
