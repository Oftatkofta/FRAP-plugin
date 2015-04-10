import ij.gui
import ij.gui.Roi as Roi
import ij.gui.OvalRoi as OvalRoi
import ij.measure
from ij.measure import ResultsTable
from ij import WindowManager as WindowManager
from ij.plugin.frame import RoiManager as RoiManager
from ij import IJ, ImagePlus, ImageStack
import ij.process.ImageStatistics as ImageStatistics
from ij.measure import Measurements as Measurements
from ij import IJ as IJ

imp = WindowManager.getCurrentImage()
stack = imp.getImageStack()
stack2 = imp.createEmptyStack()
cal = imp.getCalibration()
title = imp.getTitle()
n_channels = imp.getNChannels()

channel_to_track=imp.getChannel()
start_frame=imp.getFrame()
n_frames=imp.getNFrames()
stacktoanalyze=1


# Get the ROIs
roi_manager = RoiManager.getInstance()
roi_list    = roi_manager.getRoisAsArray()
 
# We assume first one is FRAP roi, the 2nd one is normalizing roi.
roi_1 = roi_list[0];

roi_x=roi_1.getXBase()
roi_y=roi_1.getYBase()
roi_w=roi_1.getFloatWidth()
roi_h=roi_1.getFloatHeight()

cx, cy, means1, means2=[],[],[],[]

for i in range(start_frame, n_frames+1):
    # Get the current slice
    ip = stack.getProcessor(imp.getStackIndex(channel_to_track,stacktoanalyze,i))
    roi = OvalRoi(roi_x, roi_y, roi_w, roi_h)
    ip.setRoi(roi)
    # Make a measurement in it
    stats = ImageStatistics.getStatistics(ip, ImageStatistics.CENTER_OF_MASS, cal)
    x=cal.getRawX(stats.xCenterOfMass)
    y=cal.getRawY(stats.yCenterOfMass)
    roi_x=x-roi_w/2
    roi_y=y-roi_h/2
    roi = OvalRoi(roi_x, roi_y, roi_w, roi_h)
    ip.setRoi(roi)
    stats = ImageStatistics.getStatistics(ip, ImageStatistics.CENTER_OF_MASS, cal)
    x=cal.getRawX(stats.xCenterOfMass)
    y=cal.getRawY(stats.yCenterOfMass)
    roi_x=x-roi_w/2
    roi_y=y-roi_h/2
    means1.append(stats.mean)
    cx.append(x)
    cy.append(y)
    ip2=ip.duplicate()
    ip2.setColor(255)
    ip2.draw(roi)
    stack2.addSlice(ip2)
    
im2 = ImagePlus(imp.getTitle()+'_Processed', stack2)
im2.show()

IJ.run("Clear Results")


rt=ResultsTable()

for i in range(len(means1)):
	rt.incrementCounter()
	rt.addValue('Channel.1.Mean',means1[i])
	rt.addValue('Channel.2.Mean',means2[i])
	rt.addValue('Center.of.mass.X', cx[i])
	rt.addValue('Center.of.mass.Y', cy[i])
	
	#rt.addValue("Frame.interval",frame_interval)
rt.disableRowLabels()
rt.show(title)