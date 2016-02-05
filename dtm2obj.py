#!/usr/bin/python
import os, sys, time, gdal
import numpy as np
from gdalconst import *
import matplotlib.pyplot as plt

#dtm2obj interpolates a topograpgy mesh using a Digital Terrain Model (DTM)
#        The mesh is output as an ascii obj, that can be used for 3D
#        printing.

#VARIABLES#################################################################

#IN/OUT Files
dtmFile  = 'sanraf/Ground.flt'
meshFile = 'hebes.obj'

#LAB = the geometry of the 3D printed block
#DTM = the geometry of the real world elevation model
#x0, west  x coordinate; x1, east  x coordinate
#y0, south y coordinate; y1, north y coordinate
#dx, x resolution; dy, y resolution

LAB_Width = 10 #x-direction width. y-direction height will be proportional
LAB_dx = 0.02
LAB_dy = 0.02
LAB_minThickness = 0.5
LAB_vertExageration = 1.0 #1 = no vert exag, 1/111120 = m w/ latlong

#Desired Geographic Range (Real World)
DTM_x0 =  488900
DTM_x1 =  491000
DTM_y0 = 4280500
DTM_y1 = 4282900

###########################################################################


def faceDefine(n,rowct,colct): #find vertices for faces
	'''
	Face Define Function
	Takes the square number (ij+j), 
		        number of rows (i), and
		        number of columns (j).
	Pairs the square up to four numbered vertices and
	splits into two CCW triangles.
	Returns obj style face strings.
	'''
	#face 0: f 2 (col+1) 1
	#face 1: f 2 (col+2) (col+1)
	
	#top left corner
	#n starts with zero
	#vertices start with one
	scolct = colct-1
	n=n+1
	
	srow = int((n-1)/scolct)
	v1 = n+srow #top left vertex of square
	v2 = v1 + 1
	v3 = v1 + colct
	v4 = v3 + 1
	
	tri1 = 'f '+str(v2)+' '+str(v3)+' '+str(v1)
	tri2 = 'f '+str(v2)+' '+str(v4)+' '+str(v3)
	
	return  tri1, tri2

#Check that DTM region and LAB region are valid
if(LAB_Width<=0):
	print '\nERROR: Desired lab block has a negative or 0 width!'
	print '  Check LAB_Width variables'
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

LAB_x0 = 0
LAB_x1 = LAB_Width
LAB_y0 = 0
LAB_y1 = float(LAB_Width) * (DTM_y1-DTM_y0) / (DTM_x1-DTM_x0)

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

print ('\nLoaded Geotiff, "%s"' % dtmFile)
print ' Raster Statistics:'
print '  Rows: ',rows,'\tCols: ',cols,'\tBands: ',bands
print '  Upper Left  Corner: (',xOrigin,',',yOrigin,')'
print '  Lower Right Corner: (',(xOrigin+(cols*pixelWidth)),',',\
	(yOrigin+(rows*pixelHeight)),')'
print '  Pixel Dimensions: (',pixelWidth,',',pixelHeight,')\n'

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
vct = int(meshRows*meshCols)
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
LABXmg,LABYmg = np.meshgrid(LAB_xSpace,LAB_ySpace) #mesh with y rows, x cols
DTM_xSpace = np.linspace(DTM_x0,DTM_x1,meshCols)
DTM_ySpace = np.linspace(DTM_y0,DTM_y1,meshRows)
DTMXmg,DTMYmg = np.meshgrid(DTM_xSpace,DTM_ySpace) #mesh with y rows, x cols
Zmg = np.empty(np.shape(LABXmg))


#Load and interpolate raster onto sub-region mesh

#in advance of y for loop, figure out column numbers used in interpolation
# for each DTM_x, identify the Raster column left and right
xCols    = (DTM_xSpace-xOrigin)/pixelWidth
WColLocs = np.floor(xCols).astype(int) #Row of west-adjacent column to x loc
EColLocs = np.ceil(xCols).astype(int)  #Row east
xOffsets = xCols - EColLocs
WColLocs[np.where(WColLocs<0)]       = 0      #shift so nothing is off grid
EColLocs[np.where(EColLocs>(cols-1))] = cols-1

#load elevation values
band = gt.GetRasterBand(1)

#for each DTM_y, identify the Raster row above and below.
for yct,y in enumerate(DTM_ySpace):
	#identify the raster row (row 0 is northmost row)
	yRow    = (y-yOrigin)/pixelHeight
	NRowLoc = int(np.floor(yRow)) #Row north of the current y location
	SRowLoc = int(np.ceil(yRow))  #Row south
	
	#Weight average of the entire row. If N/S rows outside boundary, just
	# use the other row with no weight.
	if NRowLoc < 0:
		RowData = band.ReadAsArray(0,SRowLoc,cols,1)[0]
	elif (SRowLoc > (rows-1)):
		RowData = band.ReadAsArray(0,NRowLoc,cols,1)[0]
	else:
		yOffset = yRow - NRowLoc
		NRow = band.ReadAsArray(0,NRowLoc,cols,1)[0]
		SRow = band.ReadAsArray(0,SRowLoc,cols,1)[0]
		RowData = NRow*((1-yOffset)**2) + SRow*(yOffset**2) #weighted average of two rows
		RowData *= 1.0/(((1-yOffset)**2)+(yOffset**2))
	# for each DTM_x, identify the Raster column left and right
	Zmg[yct] = RowData[WColLocs]*(1-xOffsets) + RowData[EColLocs]*(xOffsets)

print "Interpolation Complete!"

#Reduce Z values to Lab coordinates
Zmg -= np.min(Zmg)
Zmg *= float(LAB_vertExageration)*(LAB_x1-LAB_x0)/(DTM_x1-DTM_x0)
Zmg += LAB_minThickness

#print out vertices to mesh file
vertarray = np.ndarray(shape=((vct+4),4), dtype='|S6')
vertarray[:,0] = 'v'
vertarray[:vct,1] = LABXmg.reshape(-1)
vertarray[:vct,2] = LABYmg.reshape(-1)
vertarray[:vct,3] = Zmg.reshape(-1)
np.savetxt(meshFile,vertarray, fmt='%s')

#base vertices
vertarray[-4,1], vertarray[-3,1] = LAB_x0, LAB_x0
vertarray[-2,1], vertarray[-1,1] = LAB_x1, LAB_x1
vertarray[-2,2], vertarray[-4,2] = LAB_y0, LAB_y0
vertarray[-1,2], vertarray[-3,2] = LAB_y1, LAB_y1
vertarray[-4:,3] = '0.00'

with open(meshFile, 'w') as mf:
	mf.write('#Created with gtiff2mesh_q.py, Jacob Richardson\n#\n')
	
	mf.write('#Vertices\n')
	mf.write('#No. Vertices: '+str(vct)+'\n')
	
	np.savetxt(mf,vertarray, fmt='%s')
	print "Vertices saved."


	'''
	print "Plotting."

	plt.subplot(1, 1, 1)
	plt.pcolor(LABXmg,LABYmg,Zmg, cmap='RdBu', vmin=np.min(Zmg), vmax=np.max(Zmg))
	plt.title('pcolor')
	# set the limits of the plot to the limits of the data
	plt.axis([LAB_x0, LAB_x1, LAB_y0, LAB_y1])
	plt.colorbar()
	plt.show()
	'''

	#print faces to the outfile
	scount = int((meshCols-1)*(meshRows-1)) #square count
	fcount = int(2*scount) #triangular face count
	print '\nWriting ', fcount, ' Faces...'

	mf.write('#\n#Faces\n')
	mf.write('#No. Faces: '+str(fcount)+'\n#\n')

	for s in range(scount): #for every square, there will be two faces
		if (s%int(scount/10+1))==0: #user screen output
			sys.stdout.write('\rFaces completed: '+str(100*s/scount)+'%')
			sys.stdout.flush()
		
		(face1,face2) = faceDefine(s,meshRows,meshCols) #main face function
		mf.write(str(face1)+'\n'+str(face2)+'\n') #write to obj file

	sys.stdout.write('\rFaces completed: 99%. Identifying Base and Sides...')
	#Write out vertex to the outfile
	#define and print vertices with faceDefine

	#Identify and export side and bottom face. CCW
	#Base Vertices: -1 NE, -2 SE, -3 NW, -4 SW
	#                +4     +3     +2     +1
	mf.write('f %d %d %d %d\n' % (vct+2,vct+4,vct+3,vct+1))
	
	#South
	#101 -> 1, vct+1, vct+3.
	#mf.write('f %d %d %d %d\n' % (1,vct+1,vct+3,101))
	mf.write('f')
	for i in range(int(meshCols)):
		mf.write(' %d' % (meshCols-i))
	mf.write(' %d %d\n' % (vct+1,vct+3))
	
	#North
	mf.write('f')
	for i in range(int(meshCols)):
		mf.write(' %d' % (vct-(meshCols-1)+i))
	mf.write(' %d %d\n' % (vct+4,vct+2))
	
	#West
	mf.write('f')
	for i in np.arange(1,vct+1,meshCols,dtype=(int)):
		mf.write(' %d' % i)
	mf.write(' %d %d\n' % (vct+2,vct+1))
	
	#East
	mf.write('f')
	for i in reversed(np.arange(meshCols,vct+1,meshCols,dtype=(int))):
		mf.write(' %d' % i)
	mf.write(' %d %d\n' % (vct+3,vct+4))

sys.stdout.write('\rFaces completed: 100%.                             \n')
print "Faces saved."


#print meshCols, meshRows
#print (np.arange(1,vct+1,101,dtype=(int)))
#print (np.arange(101,vct+1,101,dtype=(int)))
print ('\nCreated 3D object file, "%s"' % meshFile)
print ' OBJ Statistics:'
print '  Rows: ',meshRows,'\tCols: ',meshCols
print '  X-range: Lab (',LAB_x0,',',LAB_x1,') Geog. (',DTM_x0,',',DTM_x1,')'
print '  Y-range:     (',LAB_y0,',',LAB_y1,')       (',DTM_y0,',',DTM_y1,')'
print '  Base (Z) Thickness: ',np.min(Zmg),('  Max thickness: %0.2f' % np.max(Zmg))
print '  Grid Resolution: (',LAB_dx,',',LAB_dy,')\n'

