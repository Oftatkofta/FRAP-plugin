#@ String (visibility=MESSAGE, value="<html>Perimeter Meter 0.3 <br></html>") docmsg
#@ Float(label="Depth of cortex (um)", required=true, value=10, stepSize=0.1) band_thickness
#@ Boolean(label="Do Gaussian blur background subtraction?", value=true) blurFlag
#@ Float(label="radius of blur (µm)", value=5) blurSigma
#@ Boolean(label="Show blurred image", value=false) showBlurFlag


"""
A plugin that measures the intenisies of equally thick bands around organoids.

Count frames represented in RM
Make empty imw with correct dimensions
Extract frames from ROIS
duplicate -> Gaussian blur 5 um
subtract blur from frames
run analysis

"""
from ij import IJ, ImageStack, ImagePlus
from ij.gui import Roi, Overlay
from ij.plugin.frame import RoiManager
from ij.plugin.filter import Analyzer, GaussianBlur
from ij.plugin import HyperStackConverter, ImageCalculator
from ij.measure import ResultsTable

from java.awt import Color

import math

def getCurrentRoiMean(imp, channel):
    #Returns the mean of the rurrent roi active in imp for channel
    
    imp.setC(channel)
    return imp.getStatistics().mean
    


def getBandMean(imp, roi, band_thickness, channel):
    """
    Returns the mean of a band_thickness thick band
    around the supplied roi, positive value for growing
    the band, negative for shrinking.
    """
    imp.setRoi(roi)    
    strt = getCurrentRoiMean(imp, channel)
    
    IJ.run("Enlarge...", "enlarge="+str(band_thickness))
    roi_o = imp.getRoi()
    out = getCurrentRoiMean(imp, channel)

    #Are we growing or shrinking the ROI?
    if band_thikness > 0:
        return(out-strt)
    else:
        return(strt-out)
  

def getOutsideBand(imp, contourRoi, band_thickness, label, addToRm = False):
    """
    Returns a ROI consisting of controurRoi expanded by band_thickness
    minus (XOR) contourRoi. Roi is named: "Outside band frame NN".
    addToRm specifies if ROI is to be added to the RoiManager.
    """
    
    _rm = RoiManager(True) #secret RoiManager
    _rm.addRoi(contourRoi)
    roi_idx = _rm.getIndexes()[-1] #record index for XOR 
    imp.setRoi(contourRoi)

    #enlarge contourRoi
    IJ.run("Enlarge...", "enlarge="+str(band_thickness))
    roi_o = imp.getRoi()
    _rm.addRoi(roi_o)
    roi_o_idx = _rm.getIndexes()[-1]
    _rm.setSelectedIndexes([roi_o_idx, roi_idx])
    _rm.runCommand('XOR')
    roi_o = imp.getRoi()
    roi_o.setName("Outside band frame "+label)
    roi_o.setPosition(imp)
    roi_o.setFillColor(Color(0, 0, 255, 32)) #12,5% transparent red
    
    if addToRm:
        RoiManager.getRoiManager().addRoi(roi_o)
    
    return roi_o

def getCortexBand(imp, contourRoi, band_thickness, label, addToRm = False):
    """
    Returns a ROI consisting of controurRoi minus contourRoi shrunk
    by band_thicness. addToRm specifies if ROI is to be added to the
    RoiManager.
    """
    _rm = RoiManager(True) #secret RoiManager
    _rm.addRoi(contourRoi)
    roi_idx = _rm.getIndexes()[-1] #record index for XOR 
    imp.setRoi(contourRoi)

    #shrink contourRoi
    IJ.run("Enlarge...", "enlarge="+str(-band_thickness))
    roi_o = imp.getRoi()
    _rm.addRoi(roi_o)
    roi_o_idx = _rm.getIndexes()[-1]
    _rm.setSelectedIndexes([roi_o_idx, roi_idx])
    _rm.runCommand('XOR')
    
    roi_o = imp.getRoi()
    roi_o.setName("Cortex band frame "+label)
    roi_o.setPosition(imp)
    
    if addToRm:
        RoiManager.getRoiManager().addRoi(roi_o)
        
    return roi_o

    
def getInside(imp, contourRoi, band_thickness, label, addToRm=False):
    """
    Returns a ROI consisting of controurRoi shrunk
    by band_thickness. addToRm specifies if ROI is to be added to the
    RoiManager.
    """
    
    
    imp.setRoi(contourRoi)

    #shrink contourRoi
    IJ.run("Enlarge...", "enlarge="+str(-band_thickness))

    roi_o = imp.getRoi()
    roi_o.setName("Inside frame "+label)
    roi_o.setPosition(imp)
    roi_o.setStrokeColor(Color.red)
    roi_o.setFillColor(Color(255, 0, 0, 32)) #12,5% transparent red

    if addToRm:
        RoiManager.getRoiManager().addRoi(roi_o)
        
    return roi_o


def listTimepointsInRoiManager(rm):
	"""
	Returns a list of the unique time points represented in a
	RoiManager
	"""
	out = []
	
	for idx in range(rm.getCount()):
		t = rm.getRoi(idx).getTPosition()
		
		if (t not in out):
			out.append(t)
		
	return out
    

def extractFrame(frameNumber, imp, z=1):
    """
    Extracts and returns all channels from one single frame of imp as an ImageStack
    frameNumber is one based
    z is slice, defaults to 1
    """
    inStack = imp.getStack()
    outStack = ImageStack(imp.width, imp.height)
    
    for c in range(imp.getNChannels()):
        stk_idx = imp.getStackIndex(c+1, z, frameNumber) 
        ip = inStack.getProcessor(stk_idx)
        ip = ip.duplicate()
        slice_lab = inStack.getSliceLabel(stk_idx)
        outStack.addSlice(slice_lab, ip)
     
    #outStack.update(ip) #Sets stack attributes to match ip

    return outStack
    
def extractFrames(frameList, imp):
    """
    Extracts and returns all channels corresponding to frame numbers in frameList
    returns imp as HyperStack
    frameNumber is one based
    """
    
    outStack = ImageStack(imp.width, imp.height)
    n_chan = imp.getNChannels()
    for fn in frameList:
        stk = extractFrame(fn, imp)
        for stk_idx in range(1, stk.getSize()+1):
            ip = stk.getProcessor(stk_idx)
            outStack.addSlice(ip)
    imp_o = ImagePlus("extracted", outStack)
    
    imp_o = HyperStackConverter().toHyperStack(imp_o, n_chan, 1, len(frameList))
    
    return  imp_o

    
def blurStack(inStack, sigma):
    """
    Returns an gaussian blurred version of ImageStack
    with sigma (int) applied
    """
    blur = GaussianBlur()
    outStack = ImageStack()
    inStack = inStack.duplicate()
    for stk_idx in range(1, inStack.getSize()+1):
        ip = inStack.getProcessor(stk_idx)
        #ip = ip.duplicate() #don't mess with the original
        blur.blurGaussian(ip, float(sigma))
        outStack.addSlice(ip)
    
    return outStack

def blurImp(imp, sigma):
    """
    runs blurStack on imp
    returns imp
    """
    n_chan = imp.getNChannels()
    n_frames = imp.getNFrames()
    inStack = imp.getStack()
    outStack = blurStack(inStack, sigma)
    imp_o = ImagePlus("blurred_"+str(sigma), outStack)
    imp_o = HyperStackConverter().toHyperStack(imp_o, n_chan, 1, n_frames)
    
    return imp_o
    
def subtractImps(imp1, imp2):
    """
    Subtracts the pixels in imp2 from imp1

    Returns imp
    """
    ic = ImageCalculator()
    #imp_o = ic.run("Subtract create stack", imp2, imp1)
    imp_o = ic.run("Subtract create stack", imp2, imp1)
    return imp_o 
    
def _runAnalysis(imp):
    imp.setActivated()
    imp.show()
    rt_ch2 = ResultsTable()
    rt_ch3 = ResultsTable()
    anal_2 = Analyzer(imp, rt_ch2)
    anal_3 = Analyzer(imp, rt_ch3)
    olay = Overlay()

    for idx in range(rm.getCount()):
       
        imp.setT(idx+1)  
        contourRoi = rm.getRoi(idx).clone()
        contourRoi.setPosition(imp)    
        imp.setRoi(contourRoi)
        label = str(rm.getRoi(idx).getTPosition())
        contourRoi.setName("Contour Frame " + label)
        o_band_roi = getOutsideBand(imp, contourRoi, band_thickness, label, False)
        c_band_roi = getCortexBand(imp, contourRoi, band_thickness, label, False)
        in_roi = getInside(imp, contourRoi, band_thickness, label, False)
        roiz = [contourRoi, o_band_roi, c_band_roi, in_roi]
            
        for c in [2,3]:
            
            if c == 2:
                anal = anal_2
                rt = rt_ch2
            else:
                anal = anal_3
                
                rt = rt_ch3
                
            for roi in roiz:
                imp.setRoi(roi)
                imp.setC(c)
                anal.measure()
                rt.addValue("Channel", c)
                rt.addValue("Frame", rm.getRoi(idx).getTPosition())
    
    
        for roi in roiz:
            imp.setRoi(roi)
            stack_idx = imp.getStackIndex(1, 1, roi.getTPosition())
            #roi.setPositon(stack_idx)
            olay.add(roi)
    
    imp.setOverlay(olay)
    rt_ch2.show(title+"_Ch2")
    rt_ch3.show(title+"_Ch3")
    



# Get current ImagePlus & set up variables
imp = IJ.getImage()
title = imp.getTitle()
cal = imp.getCalibration()
luts = imp.getLuts()
sigma_px = blurSigma/cal.pixelHeight

rm = RoiManager.getRoiManager() #user facing RoiManager




frameList = listTimepointsInRoiManager(rm)
imp1 = extractFrames(frameList, imp)
imp1.setCalibration(cal)

if blurFlag:
    imp2 = blurImp(imp1, sigma_px)
    imp2.setCalibration(cal)
    imp3 = subtractImps(imp2, imp1)
    imp3.setTitle(title+" subtracted")
    _runAnalysis(imp3)
    
    if showBlurFlag:
        imp2.show()


else:
    _runAnalysis(imp3)

