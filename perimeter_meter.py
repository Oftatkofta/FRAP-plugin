#@ Float(label="Depth of cortex (um)", required=true, value=10, stepSize=0.1) band_thickness

"""
A plugin that measures the intenisies of equally thick bands around organoids.

"""
from ij import IJ
from ij.gui import Roi, Overlay
from ij.plugin.frame import RoiManager
from ij.plugin.filter import Analyzer
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

  

def getOutsideBand(imp, contourRoi, band_thickness, addToRm = False):
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
    roi_o.setName("Outside band frame "+str(contourRoi.getTPosition()))
    roi_o.setPosition(imp)
    roi_o.setFillColor(Color(0, 0, 255, 32)) #12,5% transparent red
    
    if addToRm:
        RoiManager.getRoiManager().addRoi(roi_o)
    
    return roi_o

def getCortexBand(imp, contourRoi, band_thickness, addToRm = False):
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
    roi_o.setName("Cortex band frame "+str(contourRoi.getTPosition()))
    roi_o.setPosition(imp)
    
    if addToRm:
        RoiManager.getRoiManager().addRoi(roi_o)
        
    return roi_o

    
def getInside(imp, contourRoi, band_thickness, addToRm=False):
    """
    Returns a ROI consisting of controurRoi shrunk
    by band_thicness. addToRm specifies if ROI is to be added to the
    RoiManager.
    """
    imp.setRoi(contourRoi)

    #shrink contourRoi
    IJ.run("Enlarge...", "enlarge="+str(-band_thickness))

    roi_o = imp.getRoi()
    roi_o.setName("Inside frame "+str(contourRoi.getTPosition()))
    roi_o.setPosition(imp)
    roi_o.setStrokeColor(Color.red)
    roi_o.setFillColor(Color(255, 0, 0, 32)) #12,5% transparent red

    if addToRm:
        RoiManager.getRoiManager().addRoi(roi_o)
        
    return roi_o

    
# Get current ImagePlus & set up variables
imp = IJ.getImage()
title = imp.getTitle()
rm = RoiManager.getRoiManager() #user facing RoiManager

#band_thickness = 10 # um from pixel calibration
rt_ch2 = ResultsTable()
rt_ch3 = ResultsTable()
anal_2 = Analyzer(imp, rt_ch2)
anal_3 = Analyzer(imp, rt_ch3)
olay = Overlay()


# Go through the ROIs currently in ROImanager
for idx in range(rm.getCount()):

    rm.select(idx)
    contourRoi = imp.getRoi()
    contourRoi.setName("Contour Frame " + str(contourRoi.getTPosition()))
    o_band_roi = getOutsideBand(imp, contourRoi, band_thickness, False)
    c_band_roi = getCortexBand(imp, contourRoi, band_thickness, False)
    in_roi = getInside(imp, contourRoi, band_thickness, False)
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
            rt.addValue("Frame", contourRoi.getTPosition())


    for roi in roiz:
        imp.setRoi(roi)
        stack_idx = imp.getStackIndex(1, 1, roi.getTPosition())
        #roi.setPositon(stack_idx)
        olay.add(roi)

imp.setOverlay(olay)
rt_ch2.show(title+"_Ch2")
rt_ch3.show(title+"_Ch3")


	


