#import ij.gui
import ij.gui.Roi as Roi
import ij.gui.OvalRoi as OvalRoi
import ij.gui.Overlay as Overlay
#import ij.measure
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
import math
from ij.measure import CurveFitter as CurveFitter


def setupDialog(imp):

    gd = GenericDialog("PML Buddy options")
    gd.addMessage("Welcome to PML Buddy 0.1, you are analyzing: "+imp.getTitle())
    calibration = imp.getCalibration()

    if calibration.frameInterval > 0:
        default_interval=calibration.frameInterval
    else:
        default_interval = 0

    gd.addNumericField("Frame interval:", default_interval, 2)  # show 2 decimals    
    gd.addStringField("time unit", "sec",3)
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
    gd.addCheckbox("Show cropped region", True)
    gd.addCheckbox("Use scaled analysis ROI", True)
    gd.addCheckbox("Do colocalization analysis on Ch1 & Ch2", True)
    gd.addCheckbox("Plot Colocalization coefficients", False)
    
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
    
def channelStats(ip, channel, roi, resultdict, cal):
    """Arguments:
    ip:ImageProcessor, channel: int, roi:roi, resultdict:dict, cal:calibration
    Returns: ip, cropped to roi
    """
    ip.setRoi(roi)
    stats = ImageStatistics.getStatistics(ip, ImageStatistics.CENTER_OF_MASS, cal)
    x=cal.getRawX(stats.xCenterOfMass)
    y=cal.getRawY(stats.yCenterOfMass)
    resultdict['means_ch'+str(channel)].append(stats.mean)
    resultdict['ch'+str(channel)+'x'].append(x)
    resultdict['ch'+str(channel)+'y'].append(y)

    return ip.crop()

def colocRecorder(ip1, ip2, resultdict):
    """Arguments:
    ip1&ip2:ImageProcessors, resultdict:dict
    Returns: nothing, updates resultdict
    """
    M=CalcMandersCoefficients(ip1, ip2)
    resultdict['M1'].append(M[0])
    resultdict['M2'].append(M[1])
    resultdict['Pearson'].append(CalcPearsonsCoefficient(ip1, ip2))
    resultdict['overlap_coefficient'].append(CalcOverlapCoefficient(ip1, ip2))

    return
    
def CalcOverlapCoefficient(ip1, ip2):
    """
    Calculates Manders Overlap Coeficcient, MOC, as
    specified in Manders et al. 1993. 
    Aguments: ip1, ip2, two imageProcessors of equal size
    Returns: float, representing overlap coefficient
    """
    G = ip1.getPixels()
    R = ip2.getPixels()
    accum = 0
    Gsum = 0
    Rsum = 0
    for i in range(len(G)):
         accum+=G[i]*R[i]
         Gsum += G[i]**2
         Rsum += R[i]**2

    if Gsum*Rsum==0:
        return 0
    return accum/math.sqrt(Gsum*Rsum)
    

def CalcMandersCoefficients(ip1, ip2):
    """
    Calculates Mandlers colocalization coefficients, MCC, , as
    specified in Manders et al. 1993.
    Aguments: ip1, ip2, two imageProcessors of equal size
    Returns: floats M1, M2, representing Manders coefficients
    """
    G = ip1.getPixels()
    R = ip2.getPixels()
    Gcoloc = 0
    Rcoloc = 0
    for i in range(len(G)):
         if G[i]>0:
             Rcoloc+=R[i]
         if R[i]>0:
             Gcoloc+=G[i]
         
    Gsum = sum(G)
    Rsum = sum(R)
    
    if Gsum*Rsum==0:
        return 0,0
        
    return Gcoloc/float(Gsum), Rcoloc/float(Rsum)

def CalcPearsonsCoefficient(ip1, ip2, Th_G=0, Th_R=0):
    """
    Calculates Pearson's correlation coeficcient, PCC.
    
    Aguments:
        ip1, ip2, two imageProcessors of equal size
        Th1, Th2, Threshold values, calculates PCC for
        pixels above These values, defaluts to 0
        
    Returns:
        float R, representing Pearson's coefficient.
    """
    G = ip1.getPixels()
    R = ip2.getPixels()

    if (Th_G > 0) or (Th_R > 0):
        G,R = thresholder(G, R, Th_G, Th_R)

    Gsq = 0
    Rsq = 0
    
    Gavg=sum(G)/float(len(G))
    Ravg=sum(R)/float(len(R))

    num=0
    
    for i in range(len(G)):
         Rdiff = R[i]-Ravg
         Gdiff = G[i]-Gavg
         num+=Rdiff*Gdiff
         Gsq+=(Rdiff**2)
         Rsq+=(Gdiff**2)
         
    if Gsq*Rsq==0:
        return 0
    return num/(math.sqrt(Gsq*Rsq))

def thresholder(Ch1_pix, Ch2_pix, Th1, Th2):
    """Returns the pixels above thresholds 1 and 2.

    This function is called from inside the CalcPearsonsCoefficient
    function if you supply it with at least one threshold value.

    Args:
        Ch1_pix: Array with the channel 1 pixels
        Ch2_pix: array with the channel 2 pixels
        Th1: Threshold for channel 1
        Th2: Threshold for channel 2
        
    Returns:
        A tuple containing the pixels that pass the threshold for 
        both channel 1 and channel 2.
        
        ([ch1],[ch2])
     """
    out1 = []
    out2 = []
        
    for g, r in zip(Ch1_pix, Ch2_pix):
        if (g > Th1) and (r > Th2):
            out1.append(g)
            out2.append(r)

    return out1, out2
    
def getLinfit(ch1_pix, ch2_pix):

    fitter = CurveFitter(ch1_pix, ch1_pix)
    fitter.doFit(CurveFitter.STRAIGHT_LINE)

    return fitter

    
#Start by getting the active image window
imp = WindowManager.getCurrentImage()
cal = imp.getCalibration()

# Run the setupDialog and read out the options
gd=setupDialog(imp)  	

frame_interval = gd.getNextNumber()
time_unit = gd.getNextString()
channel_to_track = int(gd.getNextChoice())
roi_to_use = gd.getNextChoice()  
no_of_centerings = int(gd.getNextNumber())
analsis_roi_diameter = int(gd.getNextNumber())
start_frame = int(gd.getNextNumber())
stop_frame = int(gd.getNextNumber())

if (start_frame > stop_frame):
    IJ.showMessage("Start frame > Stop frame!")
    raise RuntimeException("Start frame > Stop frame!")

no_frames_tracked=(stop_frame-start_frame)+1

#Setting flags
showTrackFlag=gd.getNextBoolean()
showPlotFlag=gd.getNextBoolean()
showResultsFlag=gd.getNextBoolean()
showCropFlag=gd.getNextBoolean()
analysisRoiFlag=gd.getNextBoolean()
colocalizationFlag=gd.getNextBoolean()
showColPlotFlag=gd.getNextBoolean()
    
#Set the frame interval in calibration
    
cal.frameInterval = frame_interval
cal.setTimeUnit(time_unit)
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

if analysisRoiFlag:
    stack_crop = ImageStack(int(analsis_roi_diameter), int(analsis_roi_diameter))
else:
    stack_crop = ImageStack(int(roi_w), int(roi_h))


#Create a dictionary to keep track of results
result_dict={}
result_keys=['means_ch1','means_ch2','ch1x','ch1y','ch2x','ch2y']
    
if colocalizationFlag:
    extra_keys=['M1', 'M2', 'Pearson', 'overlap_coefficient']
    for extra in extra_keys: 
        result_keys.append(extra)
    
for key in result_keys:
    result_dict[key]=[]
  

#loop through the frames that you want to track
for frame in range(start_frame, stop_frame+1):
    # Get the imageProcessor of the channel to track at the current frame
    track_ip = stack.getProcessor(imp.getStackIndex(channel_to_track,stack_to_track,frame))
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
    
    #Get Channel 1&2 IPs and apply the centered roi with the desired diameter
    
    ip1 = stack.getProcessor(imp.getStackIndex(1,stack_to_track,frame))
    ip1_crop=channelStats(ip1, 1, analysis_roi, result_dict, cal)
    
    ip2 = stack.getProcessor(imp.getStackIndex(2,stack_to_track,frame))
    ip2_crop=channelStats(ip2, 2, analysis_roi, result_dict, cal)

    if colocalizationFlag:
        colocRecorder(ip1_crop, ip2_crop, result_dict)

    if showTrackFlag:
        ip_track=track_ip.duplicate()
        ip_track.setColor(track_ip.maxValue())
        ip_track.draw(track_roi)
        
        if analysisRoiFlag:
            ip_track.setColor(track_ip.maxValue()/2)
            ip_track.draw(analysis_roi)
        stack_track.addSlice(ip_track)

    if showCropFlag:       
        #ip_crop.setColor(ip.maxValue())
        #ip_crop.draw(analysis_roi)
        stack_crop.addSlice(ip1_crop)
        stack_crop.addSlice(ip2_crop)


if showTrackFlag:    
    imp_track = ImagePlus(title+'_Processed', stack_track)
    imp_track.setCalibration(cal)
    imp_track.show()

if showCropFlag:
    imp_crop = IJ.createHyperStack(title+"_analysis_crop", int(roi_w), int(roi_h), n_channels, 1, no_frames_tracked, imp.getBitDepth())
    imp_crop.setStack(stack_crop)
    imp_crop.setCalibration(cal)
    imp_crop.show()

if showResultsFlag:
    IJ.run("Clear Results")
    rt=ResultsTable()
    for index in range(no_frames_tracked):
        rt.incrementCounter()
        for key in result_keys:
            rt.addValue(str(key),result_dict[key][index])
        
    rt.disableRowLabels()
    rt.show(title)

if showPlotFlag:
    maxc1=max(result_dict['means_ch1'])
    maxc2=max(result_dict['means_ch2'])
    if maxc1>maxc2:
        plotlim = maxc1
    else:
        plotlim = maxc2

    if frame_interval > 0:
        time = [frame_interval*frame for frame in range(0,no_frames_tracked)]
        xlab="Time ("+time_unit+")"
    else:
        time=range(0,no_frames_tracked)
        xlab="frame"
    
    plot = Plot("Traced intensity curve for " + imp.getTitle(), xlab, "Mean intensity", [], [])
    plot.setLimits(1, max(time), 0, plotlim );
    plot.setLineWidth(2)
    
    plot.setColor(Color.GREEN)
    plot.addPoints(time, result_dict['means_ch1'], Plot.LINE)

    plot.setColor(Color.RED)
    plot.addPoints(time, result_dict['means_ch2'], Plot.LINE)
 
    plot.setColor(Color.black)

    plot_window =  plot.show()

if showColPlotFlag:

    if frame_interval > 0:
        time = [frame_interval*frame for frame in range(0,no_frames_tracked)]
        xlab="Time ("+time_unit+")"
    else:
        time=range(0,no_frames_tracked)
        xlab="frame"

    plot = Plot("Correlationcoefficients over time for " + imp.getTitle(), xlab, "Correlation coefficient", [], [])
    plot.setLimits(1, max(time), -0.5, 3.2 );
    plot.setLineWidth(2)
    
    plot.setColor(Color.GREEN)
    plot.addPoints(time, result_dict['M1'], Plot.LINE)

    plot.setColor(Color.RED)
    plot.addPoints(time, result_dict['M2'], Plot.LINE)

    plot.setColor(Color.BLUE)
    plot.addPoints(time, result_dict['Pearson'], Plot.LINE)

    plot.setColor(Color.BLACK)
    plot.addPoints(time, result_dict['overlap_coefficient'], Plot.LINE)

    plot_window =  plot.show()
    
