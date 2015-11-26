#import ij.gui
from ij.plugin import ZProjector, Duplicator

from ij import WindowManager as WindowManager
from ij import IJ, ImagePlus, ImageStack
from ij import IJ as IJ
from ij.gui import GenericDialog
import math


def setupDialog(imp):

    gd = GenericDialog("TimeCompactor options")
    gd.addMessage("Welcome to TimeCompactor 0.1, you are analyzing: "+imp.getTitle())
    calibration = imp.getCalibration()

    if calibration.frameInterval > 0:
        default_interval=calibration.frameInterval
    else:
        default_interval = 4

    gd.addNumericField("Frame interval:", default_interval, 2)  # show 2 decimals    
    gd.addStringField("time unit",calibration.getTimeUnit(), 3)
    gd.addSlider("Start compacting at frame:", 1, imp.getNFrames(), 1)
    gd.addSlider("Stop compacting at frame:", 1, imp.getNFrames(), imp.getNFrames())
    gd.addNumericField("Number of frames to project in to one:", 15, 0)  # show 0 decimals
    
    
    gd.addChoice('Method to use for frame projection:', methods_as_strings, methods_as_strings[1])
    gd.showDialog()  
	  
    if gd.wasCanceled():  
        IJ.log("User canceled dialog!")  
        return

    return gd

#Start by getting the active image window and creating a ZProjector object from it
imp = WindowManager.getCurrentImage()
cal = imp.getCalibration()
nChannels = imp.getNChannels()
nSlices = 1 #TODO fiz this in case you want to do Z-stacks
title = imp.getTitle()
zp = ZProjector(imp)

#Make a dict containg method_name:const_fieled_value pairs for the projection methods
methods_as_strings=['Average Intensity', 'Max Intensity', 'Min Intensity', 'Sum Slices', 'Standard Deviation', 'Median']
methods_as_const=[zp.AVG_METHOD, zp.MAX_METHOD, zp.MIN_METHOD, zp.SUM_METHOD, zp.SD_METHOD, zp.MEDIAN_METHOD]
medthod_dict=dict(zip(methods_as_strings, methods_as_const))

# Run the setupDialog, read out and store the options
gd=setupDialog(imp)
frame_interval = gd.getNextNumber()
time_unit = gd.getNextString()

#Set the frame interval and unit, and store it in the ImagePlus calibration
cal.frameInterval = frame_interval
cal.setTimeUnit(time_unit)
imp.setCalibration(cal)

#If a subset of the image is to be projected, these lines of code handle that
start_frame = int(gd.getNextNumber())
stop_frame = int(gd.getNextNumber())

if (start_frame > stop_frame):
    IJ.showMessage("Start frame > Stop frame!")
    raise RuntimeException("Start frame > Stop frame!")

if ((start_frame != 1) or (stop_frame != imp.getNFrames())):
    imp = Duplicator().run(imp, start_frame, stop_frame);
    #imp.show();

#The Z-Projection magic happens here
total_no_frames_to_project=imp.getNFrames()
no_frames_per_integral = int(gd.getNextNumber())
method=gd.getNextChoice()
chosen_method=medthod_dict[method]
zp.setMethod(chosen_method)
outstack=imp.createEmptyStack()

for frame in range(1, total_no_frames_to_project, no_frames_per_integral):
    zp.setStartSlice(frame)
    zp.setStopSlice(frame+no_frames_per_integral)
    zp.doProjection()
    outstack.addSlice(zp.getProjection().getProcessor())

imp2=ImagePlus(title+'_'+method+'_'+str(no_frames_per_integral)+'_frames', outstack)
nFrames=imp2.getImageStackSize()
imp2.setDimensions(1, 1, nFrames)
imp2.show()
    


