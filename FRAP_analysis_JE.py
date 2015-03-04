"""
This plugin is extensively based on the Jython FRAP analysis script from:
http://fiji.sc/Analyze_FRAP_movies_with_a_Jython_script
"""

import java.awt.Color as Color
from ij import WindowManager as WindowManager
from ij.plugin.frame import RoiManager as RoiManager
from ij.process import ImageStatistics as ImageStatistics
from ij.measure import Measurements as Measurements
from ij.measure import ResultsTable
from ij import IJ as IJ
from ij.measure import CurveFitter as CurveFitter
from ij.gui import Plot as Plot
from ij.gui import PlotWindow as PlotWindow
from ij.gui import GenericDialog
from ij.plugin import ChannelSplitter
import math

def FRAPsetupDialog(imp):

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
	gd.addCheckbox("Automatic post bleach frame detection?", True)
	gd.addNumericField("First post bleach frame:", 6, 0)
	gd.addMessage("Automatic checkbox has to be unchecked for maual selection to work")
		
	gd.showDialog()  
	  
  	if gd.wasCanceled():  
		IJ.log("User canceled dialog!")  
		return  
  	# Read out the options 
  	
  	frame_interval = gd.getNextNumber()
  	channel = int(gd.getNextChoice())  
  	max_frame = int(gd.getNextNumber())
  	manual_FRAP_frame = int(gd.getNextNumber()-1) #Sic 0-index!
  	autoFRAPflag=gd.getNextBoolean()

	#Set the frame interval in calibration

	calibration.frameInterval = frame_interval
	imp.setCalibration(calibration)
	
	#Extract the desired channel
  	   
  	imp=channelSelector(imp,channel)	
  	
  	return imp, max_frame, manual_FRAP_frame, autoFRAPflag

def channelSelector(imp, channelno):
	'''
	arguments imp: imageProcessor, channelno: imteger, channel number
	returns an imp containing the desired channel
	'''
	imps=ChannelSplitter.split(imp)
	return imps[(channelno-1)]


 
# Get ROIs
roi_manager = RoiManager.getInstance()
roi_list    = roi_manager.getRoisAsArray()
 
# We assume first one is FRAP roi, the 2nd one is normalizing roi.
roi_FRAP    = roi_list[0];
roi_norm    = roi_list[1];
 

# Get current image plus and image processor
current_imp  = WindowManager.getCurrentImage()
# Pass current imp through the FRAPsetupDialog
current_imp, max_frame, manual_FRAP_frame, autoFRAPflag = FRAPsetupDialog(current_imp)
stack        = current_imp.getImageStack()
calibration  = current_imp.getCalibration()
title		 = current_imp.getTitle()
# Specify up to what frame to fit and plot, set in FRAPsetupDialog
n_slices = max_frame

#############################################
 
# Collect intensity values
 
# Create empty lists of number
If = []  # Frap values
In = []  # Norm values
 
# Loop over each slice of the stack
for i in range(0, n_slices):
  
    # Get the current slice
    ip = stack.getProcessor(i+1)
  
    # Put the ROI on it
    ip.setRoi(roi_FRAP)
  
    # Make a measurement in it
    stats = ImageStatistics.getStatistics(ip, Measurements.MEAN, calibration);
    mean  = stats.mean
  
    # Store the measurement in the list
    If.append( mean  )
 
    # Do the same for non-FRAPed area
    ip.setRoi(roi_norm)
    stats = ImageStatistics.getStatistics(ip, Measurements.MEAN, calibration);
    mean = stats.mean
    In.append( mean  )
  
# Gather image parameters
frame_interval = calibration.frameInterval
time_units = calibration.getTimeUnit()
IJ.log('For image ' + title )
IJ.log('Time interval is ' + str(frame_interval) + ' ' + time_units)
  
#Automatic FRAP frame detection minimal intensity value in FRAP and bleach frame
if autoFRAPflag:
	min_intensity = min( If )
	bleach_frame = If.index( min_intensity )
else:
	min_intensity = If[manual_FRAP_frame]
	bleach_frame = manual_FRAP_frame

IJ.log('FRAP frame is ' + str(bleach_frame+1) + ' at t = ' + str(bleach_frame * frame_interval) + ' ' + time_units )
  
# Compute mean pre-bleach intensity
mean_If = 0.0
mean_In = 0.0
for i in range(bleach_frame):         # will loop until the bleach time
    mean_If = mean_If + If[i]
    mean_In = mean_In + In[i]
mean_If = mean_If / bleach_frame
mean_In = mean_In / bleach_frame
  
# Calculate normalized curve
normalized_curve = []
for i in range(n_slices):
    normalized_curve.append( (If[i] - min_intensity) / (mean_If - min_intensity)   *   mean_In / In[i] )
     
x = [i * frame_interval for i in range( n_slices ) ]
y = normalized_curve
 
xtofit = [ i * frame_interval for i in range( n_slices - bleach_frame ) ]
ytofit = normalized_curve[ bleach_frame : n_slices ]
  
# Fitter
fitter = CurveFitter(xtofit, ytofit)
fitter.doFit(CurveFitter.EXP_RECOVERY_NOOFFSET)
IJ.log("Fit FRAP curve by " + fitter.getFormula() )
param_values = fitter.getParams()
IJ.log( fitter.getResultString() )
  
# Overlay fit curve, with oversampling (for plot)
xfit = [ (t / 10.0  + bleach_frame) * frame_interval for t in range(10 * len(xtofit) ) ]
yfit = []
for xt in xfit:
    yfit.append( fitter.f( fitter.getParams(), xt - xfit[0]) )
 
  
plot = Plot("Normalized FRAP curve for " + current_imp.getTitle(), "Time ("+time_units+')', "NU", [], [])
plot.setLimits(0, max(x), 0, 1.2 );
plot.setLineWidth(2)
 
 
plot.setColor(Color.BLACK)
plot.addPoints(x, y, Plot.LINE)
plot.addPoints(x,y,PlotWindow.X);
 
  
plot.setColor(Color.RED)
plot.addPoints(xfit, yfit, Plot.LINE)
 
plot.setColor(Color.black);
plot_window =  plot.show()
 
 
# Output FRAP parameters
thalf = math.log(2) / param_values[1]
mobile_fraction = param_values[0]
 
str1 = ('Half-recovery time = %.2f ' + time_units) % thalf
IJ.log( str1 )
str2 = "Mobile fraction = %.1f %%" % (100 * mobile_fraction)
IJ.log( str2 )

headers=['File','Half.recovery.time', 'Mobile.fraction']


