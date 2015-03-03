import java.awt.Color as Color
from ij import WindowManager as WindowManager
from ij.plugin.frame import RoiManager as RoiManager
from ij.process import ImageStatistics as ImageStatistics
from ij.measure import Measurements as Measurements
from ij import IJ as IJ
from ij.measure import CurveFitter as CurveFitter
from ij.gui import Plot as Plot
from ij.gui import PlotWindow as PlotWindow
from ij.gui import GenericDialog  
import math


def getOptions(imp):

	gd = GenericDialog("FRAP analysis options")
	calibration = imp.getCalibration()
	#if calibration.frameInterval
	gd.addNumericField("Frame interval (s):", 0, 3)  # show 3 decimals    
	channels = [str(ch) for ch in range(1, imp.getNChannels()+1)]  
	gd.addChoice("Analyze channel:", channels, channels[0])

	gd.addSlider("Number of frames to analyze:", 1, imp.getNFrames(), 30)  
	gd.showDialog()  
	  
  	if gd.wasCanceled():  
		IJ.log("User canceled dialog!")  
		return  
  # Read out the options 
  	
  	frame_interval = gd.getNextNumber()
  	channel = gd.getNextChoice()  
  	max_frame = gd.getNextNumber()

#Extract the desired channel as a new imp instance
  	   
  	stack_in = imp.getImageStack()
	stack_out = ImageStack(imp.width, imp.height)  
  	for i in xrange(1, imp.getNSlices()+1):
  		
  	
  	return frame_interval, channel, max_frame  

current_imp  = WindowManager.getCurrentImage()
out=getOptions(current_imp)

IJ.log(out[1])
