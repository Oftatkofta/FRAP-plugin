from ij import WindowManager as WindowManager
from ij.plugin import Duplicator, RGBStackMerge, SubHyperstackMaker
from jarray import array 

#from javax.vecmath import Point2f
#from java.awt.event import MouseAdapter
import ij.gui.Roi as Roi
#import ij.gui.OvalRoi as OvalRoi
#import ij.gui.Overlay as Overlay
#import ij.measure
from ij.measure import ResultsTable

from ij.plugin.frame import RoiManager as RoiManager
from ij import ImagePlus, ImageStack
import ij.process.ImageStatistics as ImageStatistics
from ij.measure import Measurements as Measurements
from ij import IJ as IJ
#import java.awt.Color as Color
#from ij.gui import Plot as Plot
#from ij.gui import PlotWindow as PlotWindow
from ij.gui import GenericDialog
#import math
#from ij.measure import CurveFitter as CurveFitter



def setupDialog(imp):

    gd = GenericDialog("Migration Buddy options")
    gd.addMessage("You are analyzing: "+imp.getTitle())

    gd.addNumericField("Increment between frames:", 2,0)  # show 2 decimals    
    #gd.addStringField("time unit", "min",3)
    #gd.addNumericField("Skip every")
    #channels = [str(ch) for ch in range(1, imp.getNChannels()+1)]  
    #gd.addChoice("Channel to track:", channels, channels[1])

    #roichoises = ['Current active Roi','First Roi in RoiManager']    
    #gd.addChoice('Roi to use for tracking: (not implemented yet)', roichoises, roichoises[1])
    
    
    #gd.addNumericField("Diameter of analysis Roi (in pixels):)",20,0)
    gd.addSlider("Mitosis onset at frame:", 1, imp.getNFrames(), imp.getFrame())
    gd.addSlider("Stop tracking at frame:", 1, imp.getNFrames(), 1)
    gd.addCheckbox("Do you want to extend an old point list? (shortcuts disabled)", False)
    #gd.addCheckbox("Show plot", False)
    #gd.addCheckbox("Show results table", False)
    #gd.addCheckbox("Show cropped region", True)
    #gd.addCheckbox("Use scaled analysis ROI", True)
    #gd.addCheckbox("Do colocalization analysis on Ch1 & Ch2", True)
    #gd.addCheckbox("Plot Colocalization coefficients", False)
    
    gd.showDialog()  
	  
    if gd.wasCanceled():  
        IJ.log("User canceled dialog!")  
        return

    return gd


#Start by getting the active image window
imp = WindowManager.getCurrentImage()
cal = imp.getCalibration()
title = imp.getTitle()


# Run the setupDialog and read out the options
gd=setupDialog(imp)

frame_increment = int(gd.getNextNumber())
 
#time_unit = gd.getNextString()
#channel_to_track = int(gd.getNextChoice())
#roi_to_use = gd.getNextChoice()  
#no_of_centerings = int(gd.getNextNumber())
#analsis_roi_diameter = int(gd.getNextNumber())
lastT = int(gd.getNextNumber())
firstT = int(gd.getNextNumber())
extendFlag = gd.getNextBoolean()

firstZ, lastZ = 1,1

#if (firstT < lastT):
#    IJ.showMessage("Start frame < Stop frame!")
#    raise RuntimeException("Start frame < Stop frame!")

#imp2 = Duplicator().run(imp, firstC,lastC,firstZ,lastZ,firstT,lastT)

#imp = IJ.run(imp, "Make Substack...", "channels=1-2 frames="+str(firstT)+"-"+str(lastT)+"-"+str(frame_increment))
imp = SubHyperstackMaker().makeSubhyperstack(imp,"1-2",str(firstZ), str(firstT)+"-"+str(lastT)+"-"+str(frame_increment))

imp1 = Duplicator().run(imp, 1,1,firstZ,lastZ,1,imp.getNFrames())
imp2 = Duplicator().run(imp, 2,2,firstZ,lastZ,1,imp.getNFrames())


IJ.run(imp1, "Reverse", "")
IJ.run(imp2, "Reverse", "")



arr = array([imp1, imp2],ImagePlus)
imp = RGBStackMerge().mergeHyperstacks(arr, False)
imp.setTitle(title+" Reversed")
if not extendFlag:
    IJ.run(imp, "RGB Color", "frames")

imp.show()
IJ.run(imp, "PointPicker", "")

