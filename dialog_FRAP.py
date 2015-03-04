import java.awt.Color as Color
from ij import WindowManager as WindowManager
from ij.plugin.frame import RoiManager as RoiManager
from ij.process import ImageStatistics as ImageStatistics
from ij.measure import Measurements as Measurements
from ij import IJ as IJ
from ij.measure import CurveFitter as CurveFitter
from ij.gui import Plot as Plot
from ij.gui import PlotWindow as PlotWindow
import math

from ij.gui import GenericDialog  
from ij.plugin import ChannelSplitter



def FRAPsetup(imp):

	gd = GenericDialog("FRAP analysis options")
	calibration = imp.getCalibration()
	if calibration.frameInterval is None:
		default_interval=0
	else:
		default_interval=calibration.frameInterval
		
	gd.addNumericField("Frame interval (s):", default_interval, 3)  # show 3 decimals    
	channels = [str(ch) for ch in range(1, imp.getNChannels()+1)]  
	gd.addChoice("Analyze channel:", channels, channels[0])
	

	gd.addSlider("Number of frames to analyze:", 1, imp.getNFrames(), 30)  
	gd.showDialog()  
	  
  	if gd.wasCanceled():  
		IJ.log("User canceled dialog!")  
		return  
  # Read out the options 
  	
  	frame_interval = gd.getNextNumber()
  	channel = int(gd.getNextChoice())  
  	max_frame = gd.getNextNumber()

#Extract the desired channel
  	   
  	imp=channelSelector(imp,channel)	
  	
  	return imp, frame_interval, max_frame  

def channelSelector(imp, channelno):
	'''
	arguments imp: imageProcessor, channelno: imteger, channel number
	returns an imp containing the desired channel
	'''
	imps=ChannelSplitter.split(imp)
	return imps[(channelno-1)]


current_imp  = WindowManager.getCurrentImage()
current_imp, frame_interval, max_frame = FRAPsetup(current_imp)
current_imp.show()
