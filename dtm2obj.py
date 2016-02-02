#!/usr/bin/python
import os, sys, time, gdal
import numpy as np
from gdalconst import *

#dtm2obj interpolates a topograpgy mesh using a Digital Terrain Model (DTM)
#        The mesh is output as an ascii obj, that can be used for 3D
#        printing.

#VARIABLES
#IN/OUT Files
dtmFile  = 'momotumbo_20m.tif'
meshFile = 'momotumbo_20m.obj'

#LAB = the geometry of the 3D printed block
#DTM = the geometry of the real world elevation model
#x0, west  x coordinate; x1, east  x coordinate
#y0, south y coordinate; y1, north y coordinate
#dx, x resolution; dy, y resolution
LAB_x0 = 0
LAB_x1 = 10
LAB_dx = 1
LAB_y0 = 0
LAB_y1 = 10
LAB_dy = 1
LAB_minThickness = 1

#Desired range
DTM_x0 = 539784
DTM_x1 = 560683
DTM_y0 = 1363777
DTM_y1 = 1381556

#Check that DTM region and LAB region are valid
if((LAB_x1<=LAB_x0) or (LAB_y1<=LAB_y0)):
	print '\nERROR: Desired lab block has a negative or 0 area!'
	print '  Check LAB_** variables'
	sys.exit(1)
	
if(LAB_minThickness <= 0):
	print '\nERROR: Desired lab block has a negative or 0 thickness!'
	print '  Check LAB_minThickness variable'
	sys.exit(1)

if((LAB_dx <= 0) or (LAB_dy <= 0)):
	print '\nERROR: Desired lab block has 0 or negative row/column thickness!'
	print '  Check LAB_d* variable'
	sys.exit(1)

if((DTM_x1<=DTM_x0) or (DTM_y1<=DTM_y0)):
	print '\nERROR: Desired geographic region has a negative or 0 area!'
	print '  Check DTM_** variables'
	sys.exit(1)

#Load dtmFile
gt = gdal.Open(dtmFile, GA_ReadOnly)
if gt is None:
	print 'ERROR: Could not open image'
	sys.exit(1)

#Capture DTM geospatial information
rows = gt.RasterYSize
cols = gt.RasterXSize
bands = gt.RasterCount
transform = gt.GetGeoTransform()
xOrigin = transform[0] #upper left
yOrigin = transform[3]
pixelWidth = transform[1]
pixelHeight = transform[5]

print ('\nIncoming Raster Range (W/E/S/N):\n  -R%0.2f/%0.2f/%0.2f/%0.2f\n' % (xOrigin,
	(xOrigin + (cols*pixelWidth)),(yOrigin + (rows*pixelHeight)),yOrigin) )

#Check that output region lay within the raster coverage
if(DTM_x0 < xOrigin):
	print '\nERROR: Desired geographic region exceeds Raster boundary!'
	print '  User-input western boundary: %0.2f' % DTM_x0
	sys.exit(1)
if(DTM_x1 > (xOrigin + (cols*pixelWidth))):
	print '\nERROR: Desired geographic region exceeds Raster boundary!'
	print '  User-input eastern boundary: %0.2f' % DTM_x1
	sys.exit(1)
if(DTM_y0 > yOrigin):
	print '\nERROR: Desired geographic region exceeds Raster boundary!'
	print '  User-input northern boundary: %0.2f' % DTM_y0
	sys.exit(1)
if(DTM_y1 < (yOrigin + (rows*pixelHeight))):
	print '\nERROR: Desired geographic region exceeds Raster boundary!'
	print '  User-input southern boundary: %0.2f' % DTM_y1
	sys.exit(1)

##############
#It seems that the input variables are valid.
#Now set-up the grid to interpolate the raster to.

meshRows = 1+round((LAB_y1-LAB_y0)/float(LAB_dy))
meshCols = 1+round((LAB_x1-LAB_x0)/float(LAB_dx))
#check and remake dy,dx to keep boundaries and row numbers the same
if((LAB_y0+((meshRows-1)*LAB_dy)) != LAB_y1):
	print ('LAB_dy has been shifted to preserve block geometry: %0.3f -> %0.3f' %
		(LAB_dy,(LAB_y1-LAB_y0)/float(meshRows-1.0)) )
	LAB_dy = (LAB_y1-LAB_y0)/float(meshRows-1.0)
	
if((LAB_x0+((meshCols-1)*LAB_dx)) != LAB_x1):
	print ('LAB_dx has been shifted to preserve block geometry: %0.3f -> %0.3f' %
		(LAB_dx,(LAB_x1-LAB_x0)/float(meshCols-1.0)) )
	LAB_dx = (LAB_x1-LAB_x0)/(meshCols-1.0)

LAB_xSpace = np.linspace(LAB_x0,LAB_x1,meshCols)
LAB_ySpace = np.linspace(LAB_y0,LAB_y1,meshRows)
DTM_xSpace = np.linspace(DTM_x0,DTM_x1,meshCols)
DTM_ySpace = np.linspace(DTM_y0,DTM_y1,meshRows)

#Load and interpolate raster onto sub-region mesh
#Write out vertex and faces to the outfile
#Identify and export side and bottom face.




