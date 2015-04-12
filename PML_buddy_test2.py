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
import java.awt.Color as Color
from ij.gui import Plot as Plot
from ij.gui import PlotWindow as PlotWindow

def roiCenterer(ip, roi, cal):
    """Arguments: ip:ImageProcessor, roi:Region of intrest, cal:calibration of ip.
    Returns an OvalRoi which is centered on the center of mass of the input roi
    applied to the ImageProcessor"""
    
    roi_w=roi.getFloatWidth()
    roi_h=roi.getFloatHeight()
    ip.setRoi(roi)
    stats = ImageStatistics.getStatistics(ip, ImageStatistics.CENTER_OF_MASS, cal)
    x=cal.getRawX(stats.xCenterOfMass)
    y=cal.getRawY(stats.yCenterOfMass)
    roi_x=x-roi_w/2
    roi_y=y-roi_h/2
    roi = OvalRoi(roi_x, roi_y, roi_w, roi_h)
    return roi

imp = WindowManager.getCurrentImage()
stack = imp.getImageStack()
stack2 = imp.createEmptyStack()
cal = imp.getCalibration()
title = imp.getTitle()
n_channels = imp.getNChannels()

channel_to_track=imp.getChannel()
start_frame=imp.getFrame()
n_frames=imp.getNFrames()
stack_to_track=1
no_of_centerings=6


# Get the ROIs
roi_manager = RoiManager.getInstance()
roi_list    = roi_manager.getRoisAsArray()
 
# We assume first one is FRAP roi, the 2nd one is normalizing roi.
roi_1 = roi_list[0];

roi_x=roi_1.getXBase()
roi_y=roi_1.getYBase()
roi_w=roi_1.getFloatWidth()
roi_h=roi_1.getFloatHeight()

#Create a bunch of empty lists to keep track of results
c1x, c1y, c2x, c2y, means1, means2=[],[],[],[],[],[]

#loop through the frames that you want to track
for i in range(start_frame, n_frames+1):
    # Get the imageProcessor of the channel to track and at the current frame
    ip = stack.getProcessor(imp.getStackIndex(channel_to_track,stack_to_track,i))
    roi = OvalRoi(roi_x, roi_y, roi_w, roi_h)
    
    #Do the Roi centering the desired number of times
    for i in range (no_of_centerings):
        roi=roiCenterer(ip, roi, cal)
        roi_x=roi.getXBase()
        roi_y=roi.getYBase()
    ip.setRoi(roi)

    
    #Get Channel 1 IP and apply the centered roi
    ip1 = stack.getProcessor(imp.getStackIndex(1,stack_to_track,i))
    ip1.setRoi(roi)
    # Make a measurement in it and record the stats
    stats = ImageStatistics.getStatistics(ip1, ImageStatistics.CENTER_OF_MASS, cal)
    x=cal.getRawX(stats.xCenterOfMass)
    y=cal.getRawY(stats.yCenterOfMass)
    means1.append(stats.mean)
    c1x.append(x)
    c1y.append(y)
    
    #Get Channel 2 IP, apply the centered roi and do the analysis
    ip2 = stack.getProcessor(imp.getStackIndex(2,stack_to_track,i))
    #roi = OvalRoi(roi_x, roi_y, roi_w, roi_h)
    ip2.setRoi(roi)
    stats = ImageStatistics.getStatistics(ip2, ImageStatistics.CENTER_OF_MASS, cal)
    x=cal.getRawX(stats.xCenterOfMass)
    y=cal.getRawY(stats.yCenterOfMass)
    means2.append(stats.mean)
    c2x.append(x)
    c2y.append(y)

    ip2=ip.duplicate()
    ip2.setColor(ip.maxValue())
    ip2.draw(roi)
    stack2.addSlice(ip2)

    
im2 = ImagePlus(title+'_Processed', stack2)
im2.setCalibration(cal)
im2.show()

IJ.run("Clear Results")

rt=ResultsTable()

for i in range(len(means1)):
	rt.incrementCounter()
	rt.addValue('Channel.1.Mean',means1[i])
	rt.addValue('Channel.2.Mean',means2[i])
	rt.addValue('Ch1.Center.of.mass.X', c1x[i])
	rt.addValue('Ch1.Center.of.mass.Y', c1y[i])
	rt.addValue('Ch2.Center.of.mass.X', c2x[i])
	rt.addValue('Ch2.Center.of.mass.Y', c2y[i])

rt.disableRowLabels()
rt.show(title)

maxc1=max(means1)
maxc2=max(means2)
if maxc1>maxc2:
    plotlim = maxc1
else:
    plotlim = maxc2

time=range(0,len(means1))
plot = Plot("Traced intensity curve for " + imp.getTitle(), "Time", "Mean intensity", [], [])
plot.setLimits(1, n_frames+1, 0, plotlim );
plot.setLineWidth(2)

plot.setColor(Color.GREEN)
plot.addPoints(time, means1, Plot.LINE)

plot.setColor(Color.RED)
plot.addPoints(time, means2, Plot.LINE)
 
plot.setColor(Color.black)
plot_window =  plot.show()

