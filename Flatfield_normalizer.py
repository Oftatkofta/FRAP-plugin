from ij import ImagePlus, WindowManager

imp = WindowManager.getCurrentImage()
title = imp.getTitle()
ip = imp.getProcessor().convertToFloat()
ip.resetMinAndMax()
ipMax = ip.getMax()
ipMin = ip.getMin()
corr = 1.0/ipMax
ip.multiply(corr)
ip.resetMinAndMax()
ip=ip.convertToShort(True)
imp = ImagePlus('NORM_'+title, ip)
imp.show() 