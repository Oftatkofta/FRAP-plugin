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

imp  = WindowManager.getCurrentImage()
stack=imp.getImageStack()
stack2=imp.createEmptyStack()
cal=imp.getCalibration()
title=imp.getTitle()
n_channels=imp.getNChannels()

channeltoanalyze=[1]
stacktoanalyze=1


# Get ROIs
roi_manager = RoiManager.getInstance()
roi_list    = roi_manager.getRoisAsArray()
 
# We assume first one is FRAP roi, the 2nd one is normalizing roi.
roi_1 = roi_list[0];

roi_x=roi_1.getXBase()
roi_y=roi_1.getYBase()
roi_w=roi_1.getFloatWidth()
roi_h=roi_1.getFloatHeight()
roi_b=roi_1.getBounds()

#print roi_x, roi_y, roi_w, roi_h, roi_b
#im2=ImagePlus('copy',stack)
#im2.setRoi(int(roi_x), int(roi_y), int(roi_w), int(roi_h))
#im2.show()
#print imp.getStackIndex(1,1,100)
#imp.setT(34)
#imp.setC(2)

n_frames=imp.getNFrames()
cx, cy=[],[]
means=[]
for i in range(1, n_frames+1):
    # Get the current slice
    ip = stack.getProcessor(imp.getStackIndex(channeltoanalyze,stacktoanalyze,i))
    roi = OvalRoi(roi_x, roi_y, roi_w, roi_h)
    ip.setRoi(roi)
    # Make a measurement in it
    stats = ImageStatistics.getStatistics(ip, ImageStatistics.CENTER_OF_MASS, cal)
    x=cal.getRawX(stats.xCenterOfMass)
    y=cal.getRawY(stats.yCenterOfMass)
    roi_x=x-roi_w/2
    roi_y=y-roi_h/2
    roi = OvalRoi(int(roi_x), int(roi_y), int(roi_w), int(roi_h))
    ip.setRoi(roi)
    stats = ImageStatistics.getStatistics(ip, ImageStatistics.CENTER_OF_MASS, cal)
    x=cal.getRawX(stats.xCenterOfMass)
    y=cal.getRawY(stats.yCenterOfMass)
    roi_x=x-roi_w/2
    roi_y=y-roi_h/2
    means.append(stats.mean)
    cx.append(x)
    cy.append(y)
    ip2=ip.duplicate()
    ip2.draw(roi)
    stack2.addSlice(ip2)
    
im2 = ImagePlus(imp.getTitle()+'_Processed', stack2)
im2.show()

IJ.run("Clear Results")


rt=ResultsTable()

for i in range(len(means)):
	rt.incrementCounter()
	rt.addValue('Mean',means[i])
	rt.addValue('Center.of.mass.X', cx[i])
	rt.addValue('Center.of.mass.Y', cy[i])
	
	#rt.addValue("Frame.interval",frame_interval)
rt.disableRowLabels()
rt.show(title)
