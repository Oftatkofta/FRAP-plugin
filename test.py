from ij import IJ, ImagePlus, ImageStack
from ij.measure import Measurements as Measurements
from ij.measure import ResultsTable
from ij import WindowManager as WindowManager
from ij.plugin.frame import RoiManager as RoiManager

# Get current image plus and image processor
current_imp  = WindowManager.getCurrentImage()
n_Frames = current_imp.getNFrames()

# Get ROIs
roi_manager = RoiManager.getInstance()
roi_list    = roi_manager.getRoisAsArray()
 
# We assume first one is PML roi.
roi_PML    = roi_list[0];

 

for i in range(0, n_slices):
  
    # Get the current slice
    ip = stack.getProcessor(i+1)
  
    # Put the ROI on it
    ip.setRoi(roi_FRAP)
imp = IJ.getImage()

IJ.makeOval(60,60,60,10)

p=imp.getProcessor(2)

p.show()