#import ij.gui
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
from ij.gui import GenericDialog


def setupDialog(imp):

    gd = GenericDialog("PML Buddy options")
    gd.addMessage("Welcome to PML Buddy 0.1, you are analyzing: "+imp.getTitle())
    calibration = imp.getCalibration()

    if calibration.frameInterval > 0:
        default_interval=calibration.frameInterval
    else:
        default_interval = 0

    gd.addNumericField("Frame interval (s):", default_interval, 2)  # show 2 decimals    
    gd.addMessage("(optional)")
    channels = [str(ch) for ch in range(1, imp.getNChannels()+1)]  
    gd.addChoice("Channel to track:", channels, channels[1])

    roichoises = ['Current active Roi','First Roi in RoiManager']    
    gd.addChoice('Roi to use for tracking: (not implemented yet)', roichoises, roichoises[1])
    
    gd.addNumericField("Number of Roi centerings to perform per frame (3-6 is generally ok):", 6, 0)
    gd.addNumericField("Diameter of analysis Roi (in pixels):)",20,0)
    gd.addSlider("Start tracking at frame:", 1, imp.getNFrames(), imp.getFrame())
    gd.addSlider("Stop tracking at frame:", 1, imp.getNFrames(), imp.getNFrames())
    gd.addCheckbox("Display tracking in new window", True)
    gd.addCheckbox("Show plot", False)
    gd.addCheckbox("Show results table", False)
    
    gd.showDialog()  
	  
    if gd.wasCanceled():  
        IJ.log("User canceled dialog!")  
        return

    return gd

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

def roiScaler(roi, new_diameter):
    """Agruments: roi: Region of intrest, new_diameter: returned roi diameter
    Returns a new OvalRoi centered on the input roi diameter""" 
    roi_x=roi.getXBase()
    roi_y=roi.getYBase()
    roi_w=roi.getFloatWidth()
    roi_h=roi.getFloatHeight()
    
    roi_x=roi_x+roi_w*0.5-new_diameter*0.5
    roi_y=roi_y+roi_h*0.5-new_diameter*0.5
    scaled_roi=OvalRoi(roi_x, roi_y, new_diameter, new_diameter)

    return scaled_roi
    

     
#Start by getting the active image window
imp = WindowManager.getCurrentImage()
cal = imp.getCalibration()

# Run the setupDialog and read out the options
gd=setupDialog(imp)  	

frame_interval = gd.getNextNumber()
channel_to_track = int(gd.getNextChoice())
roi_to_use = gd.getNextChoice()  
no_of_centerings = int(gd.getNextNumber())
analsis_roi_diameter = int(gd.getNextNumber())
start_frame = int(gd.getNextNumber())
stop_frame = int(gd.getNextNumber())

if (start_frame > stop_frame):
    IJ.showMessage("Start frame > Stop frame!")
    raise RuntimeException("Start frame > Stop frame!")

#Setting flags
showTrackFlag=gd.getNextBoolean()
showPlotFlag=gd.getNextBoolean()
showResultsFlag=gd.getNextBoolean()
showCropFlag=1
analysisRoiFlag=0
    
#Set the frame interval in calibration
    
cal.frameInterval = frame_interval
imp.setCalibration(cal)
    

stack = imp.getImageStack()
stack_track = imp.createEmptyStack()

title = imp.getTitle()
n_channels = imp.getNChannels()
stack_to_track=1



# Get the ROIs
roi_manager = RoiManager.getInstance()
roi_list    = roi_manager.getRoisAsArray()

# We will use the first ROI in the Roi manager for now.
roi_1 = roi_list[0];

roi_x=roi_1.getXBase()
roi_y=roi_1.getYBase()
roi_w=roi_1.getFloatWidth()
roi_h=roi_1.getFloatHeight()

stack_crop = ImageStack(int(roi_w), int(roi_h))
#Create a bunch of empty lists to keep track of results
c1x, c1y, c2x, c2y, means1, means2=[],[],[],[],[],[]

#loop through the frames that you want to track
for i in range(start_frame, stop_frame+1):
    # Get the imageProcessor of the channel to track and at the current frame
    track_ip = stack.getProcessor(imp.getStackIndex(channel_to_track,stack_to_track,i))
    track_roi = OvalRoi(roi_x, roi_y, roi_w, roi_h)
    
    #Do the Roi centering the desired number of times
    for i in range (no_of_centerings):
        track_roi=roiCenterer(track_ip, track_roi, cal)
    
    roi_x=track_roi.getXBase()
    roi_y=track_roi.getYBase()
    track_ip.setRoi(track_roi)

    if analysisRoiFlag:
        analysis_roi=roiScaler(track_roi, analsis_roi_diameter)
    else:
        analysis_roi=track_roi.clone()
    #Get Channel 1 IP and apply the centered roi with the desired diameter
    ip1 = stack.getProcessor(imp.getStackIndex(1,stack_to_track,i))

    ip1.setRoi(analysis_roi)
    
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
    ip2.setRoi(analysis_roi)
    stats = ImageStatistics.getStatistics(ip2, ImageStatistics.CENTER_OF_MASS, cal)
    x=cal.getRawX(stats.xCenterOfMass)
    y=cal.getRawY(stats.yCenterOfMass)
    means2.append(stats.mean)
    c2x.append(x)
    c2y.append(y)

    if showTrackFlag:
        ip_track=track_ip.duplicate()
        ip_track.setColor(track_ip.maxValue()/2)
        ip_track.draw(track_roi)
        ip_track.setColor(track_ip.maxValue())
        ip_track.draw(analysis_roi)
        stack_track.addSlice(ip_track)

    if showCropFlag:
        ip1 = stack.getProcessor(imp.getStackIndex(1,stack_to_track,i))
        ip2 = stack.getProcessor(imp.getStackIndex(2,stack_to_track,i))
        ip1.setRoi(track_roi)
        ip2.setRoi(track_roi)
        ip1_crop=ip1.crop()
        ip2_crop=ip2.crop()
       
        #ip_crop.setColor(ip.maxValue())
        #ip_crop.draw(analysis_roi)
        stack_crop.addSlice(ip1_crop)
        stack_crop.addSlice(ip2_crop)


if showTrackFlag:    
    imp_track = ImagePlus(title+'_Processed', stack_track)
    imp_track.setCalibration(cal)
    imp_track.show()

if showCropFlag:
    imp_crop = IJ.createHyperStack(title, int(roi_w), int(roi_h), n_channels, 1, (stop_frame+1)-start_frame, imp.getBitDepth())
    imp_crop.setStack(stack_crop)
    imp_crop.setCalibration(cal)
    #imp_crop.setDimensions(2,1,(stop_frame+1)-start_frame)
    imp_crop.show()

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

if showResultsFlag:
    rt.show(title)

maxc1=max(means1)
maxc2=max(means2)
if maxc1>maxc2:
    plotlim = maxc1
else:
    plotlim = maxc2


if frame_interval > 0:
    time = [frame_interval*frame for frame in range(0,len(means1))]
    xlab="Time (s)"
else:
    time=range(0,len(means1))
    xlab="frame"
plot = Plot("Traced intensity curve for " + imp.getTitle(), xlab, "Mean intensity", [], [])
plot.setLimits(1, max(time), 0, plotlim );
plot.setLineWidth(2)

plot.setColor(Color.GREEN)
plot.addPoints(time, means1, Plot.LINE)

plot.setColor(Color.RED)
plot.addPoints(time, means2, Plot.LINE)
 
plot.setColor(Color.black)

if showPlotFlag:
    plot_window =  plot.show()

