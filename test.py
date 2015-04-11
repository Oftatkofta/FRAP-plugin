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
import ij.gui.Overlay as Overlay

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
stack1 = imp.createEmptyStack()
stack2 = imp.createEmptyStack()
cal = imp.getCalibration()
title = imp.getTitle()
n_channels = imp.getNChannels()

channel_to_track=imp.getChannel()
start_frame=imp.getFrame()
n_frames=imp.getNFrames()
stack_to_track=1
no_of_centerings=3


# Get the ROIs
roi_manager = RoiManager.getInstance()
roi_list    = roi_manager.getRoisAsArray()
 
# We will use the first ROI in the Roi manager.
roi_1 = roi_list[0];

roi_x=roi_1.getXBase()
roi_y=roi_1.getYBase()
roi_w=roi_1.getFloatWidth()
roi_h=roi_1.getFloatHeight()

c1x, c1y=[],[]
c2x, c2y=[],[]
means1, means2=[],[]

#overlay = Overlay()

for i in range(start_frame, n_frames+1):
    # Get the current frame
    #imp.setPositionWithoutUpdate(channel_to_track,stack_to_track,i)
    #ip=imp.getProcessor()
    ip = stack.getProcessor(imp.getStackIndex(channel_to_track,stack_to_track,i))
    roi = OvalRoi(roi_x, roi_y, roi_w, roi_h)
    
    for i in range (no_of_centerings):
        roi=roiCenterer(ip, roi, cal)
        roi_x=roi_1.getXBase()
        roi_y=roi_1.getYBase()
    
    
    #roi2 = roi.clone()
    #roi.setPosition(channel_to_track,stacktoanalyze,i)
    #roi.setImage(imp)
    #overlay.add(roi)

    #Go to channel 1 of current frame position
    ip = stack.getProcessor(imp.getStackIndex(1,stack_to_track,i))
    #Apply the Centered roi to it
    ip.setRoi(roi)
    #Analyse and record the IP stats of the roi in channel 1
    stats = ImageStatistics.getStatistics(ip, ImageStatistics.CENTER_OF_MASS, cal)
    x=cal.getRawX(stats.xCenterOfMass)
    y=cal.getRawY(stats.yCenterOfMass)
    c1x.append(x)
    c1y.append(y)
    means1.append(stats.mean)

    #Copy the IP
    ip1 = ip.duplicate()
    ip1.setRoi(roi)
    ip1.setColor(255)
    ip1.draw(roi)
    stack1.addSlice(ip1)
    #stack2.update(ip2)

    #Go to channel 2 of current frame position
    ip = stack.getProcessor(imp.getStackIndex(1,stack_to_track,i))
    #Get the imageProcessor
    ip = imp.getProcessor()
    #Apply the Centered roi to it
    ip.setRoi(roi)
    #Analyse and record the IP stats of the roi in channel 1
    stats = ImageStatistics.getStatistics(ip, ImageStatistics.CENTER_OF_MASS, cal)
    means2.append(stats.mean)
    x=cal.getRawX(stats.xCenterOfMass)
    y=cal.getRawY(stats.yCenterOfMass)
    c2x.append(x)
    c2y.append(y)
    
    #Copy the IP
    ip2 = ip.duplicate()
    ip2.setRoi(roi)
    ip2.setColor(255)
    ip2.draw(roi)
    stack2.addSlice(ip2)
    #stack2.update(ip2)

    
imp1 = ImagePlus(imp.getTitle()+'_Processed', stack1)
imp2 = ImagePlus(imp.getTitle()+'_Processed', stack2)

imp1.show()
imp2.show()

#imp.setOverlay(overlay)
#imp.show()
    
IJ.run("Clear Results")

rt=ResultsTable()

for i in range(len(means1)):
    rt.incrementCounter() 
    rt.addValue('Cannel.1.Mean',means1[i])
    rt.addValue('Cannel.2.Mean',means2[i])
    rt.addValue('Center.of.mass.C1.X', c1x[i])
    rt.addValue('Center.of.mass.C1.Y', c1y[i])
    rt.addValue('Center.of.mass.C2.X', c2x[i])
    rt.addValue('Center.of.mass.C2.Y', c2y[i])
	
    #rt.addValue("Frame.interval",frame_interval)
rt.disableRowLabels()
#rt.show(title)

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


