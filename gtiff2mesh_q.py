#!/usr/bin/python
import os, sys, time, gdal
import numpy as num
from gdalconst import *

#makes an array of vectors, an array of faces
#exports these arrays to a simple .obj file


#VARIABLES
GTiffFile = 'sanraf/block_2m.tif'
MeshFile = 'sanraf/block_2m_tif_q.obj'
v_exag = 1 #vertical exaggeration. 1 = no exaggeration

####EOV####

def faceDefine(n,rowct,colct): #find vertices for faces
	#face 0: f 2 1 (col+1)
	#face 1: f 2 (col+1) (col+2)
	
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
	
	tri1 = 'f '+str(v2)+' '+str(v1)+' '+str(v3)
	tri2 = 'f '+str(v2)+' '+str(v3)+' '+str(v4)
	
	return  tri1, tri2
		

startTime = time.time()

#rules, all vertices must be stored counterclockwise in their faces.
#e.g. for three x,y values (0,1) (1,1) (0,0), for the surface to be "up"
#     the order must be (0,0)->(1,1)->(0,1) and can't be (0,0)->(0,1)->(1,1)
#example file:

#Vertices
#v 1 1 1700.06
#v -1 1 1700
#v 1 -1 1700.15
#v -1 -1 1700.04
#
##Faces
#f 2 1 3
#f 2 3 4


#printout
#i Print comments: created by bobcat, number of rows, number of columns
#1 For each x,y location print 'v x y z\n'
	#find geotiff spacing
	#read in 1 line of geotiff for rows
	#foreach column, find value
		#find value
		#print vertex
			

#Open GeoTiff
gt = gdal.Open(GTiffFile, GA_ReadOnly)
if gt is None:
	print 'Could not open image'
	sys.exit(1)

rows = gt.RasterYSize
cols = gt.RasterXSize
bands = gt.RasterCount

#georeference info
transform = gt.GetGeoTransform()
xOrigin = transform[0]
yOrigin = transform[3]
pixelWidth = transform[1]
pixelHeight = transform[5]

print '\nLoaded Geotiff, ',GTiffFile
print 'Raster Statistics:'
print 'Rows: ',rows,'\tCols: ',cols,'\tBands: ',bands
print 'Upper Left Corner: (',xOrigin,',',yOrigin,')'
print 'Pixel Dimensions: (',pixelWidth,',',pixelHeight,')'

#open .OBJ for writing
mf = open(MeshFile,'w')
mf.write('#Created with gtiff2mesh_q.py, Jacob Richardson\n#\n')

#VERTICES
mf.write('#Vertices\n')
vcount = rows*cols
mf.write('#No. Vertices: '+str(vcount)+'\n')

#create x values and v strings up front (for printing to one line)
x = range(cols) #x values are integers to reduce obj size
#x = map(lambda p: str(xOrigin+(p*pixelWidth)), x) #don't need this if x,y values are integers
v = ['v']*cols
scaling = abs(pixelHeight/pixelWidth) #x vs. y scaling


#load elevation values
band = gt.GetRasterBand(1)

print "\nReading Elevations. Writing ", vcount," Vertices..."

#read in one row at a time
for r in range(rows):
	if (r%int(rows/10+1))==0: #user screen output
		sys.stdout.write('\rVertices completed: '+str(100*r/rows)+'%')
		sys.stdout.flush()
	#make y value for each future elevation entry
	northing = "{:.5f}".format((rows-r)*scaling)
	y = [northing]*cols
	
	#make empty elevation list
	elev=[]
	
	#read one row, r, of the GeoTiff
	data = band.ReadAsArray(0,r,cols,1)
	
	for c in range(cols):
		data[0,c] /= pixelWidth #removes vertical exaggeration
		data[0,c] *= v_exag #adds user-defined vertical exaggeration
		elev.append(str(data[0,c]))
	
	#write row of verticies out to file
	line = num.column_stack((v,x,y,elev))
	num.savetxt(mf, line, delimiter=" ", fmt='%s')

sys.stdout.write('\rVertices completed: 100%')
sys.stdout.flush()

endTime = time.time()
elapsedTime = endTime-startTime
print '\nVertices Written.\tSeconds Elapsed: ',elapsedTime

#2 Calculate number of faces =  2(cols-1)(rows-1)
	#print face number comments
#3 for number of faces print 'f v1 v2 v3' (ccw)
	#for i in range 1 to cols - 1
		#for j in range 1 to rows - 1
			#for k in range 1 to 2 (two triangles for each top left point)
				#print face and vertices
				
#faces
scount = (cols-1)*(rows-1) #square count
fcount = 2*scount #triangular face count
print '\nWriting ', fcount, ' Faces...'

mf.write('#\n#Faces\n')
mf.write('#No. Faces: '+str(fcount)+'\n#\n')

for s in range(scount): #for every square, there will be two faces
	if (s%int(scount/10+1))==0: #user screen output
		sys.stdout.write('\rFaces completed: '+str(100*s/scount)+'%')
		sys.stdout.flush()
		
	(face1,face2) = faceDefine(s,rows,cols) #main face function
	mf.write(str(face1)+'\n'+str(face2)+'\n') #write to obj file

sys.stdout.write('\rFaces completed: 100%\n')
sys.stdout.flush()

mf.close()

endTime = time.time()
elapsedTime = endTime-startTime
print "\nFinished.\nTotal Seconds Elapsed: ",elapsedTime
