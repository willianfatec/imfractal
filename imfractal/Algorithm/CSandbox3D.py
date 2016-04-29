"""
Copyright (c) 2015 Rodrigo Baravalle
All rights reserved.
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.
3. The name of the author may not be used to endorse or promote products
derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


from Algorithm import *
from random import randrange,randint,seed
from math import log
from scipy import ndimage
import Image
import numpy as np
import scipy
import scipy.stats
import sys
import os
import matplotlib
import matplotlib.pyplot as plt
import time, qs3D	
import dicom
import os

class CSandbox3D (Algorithm):

    """

    :3D sandbox multifractal spectrum in cython
    :version: 1.0
    :author: Rodrigo Baravalle
    """

    # how many multifractal dimentions should the algorithm return
    def __init__(self, c):
        self.cant = c

    def setDef(self,x,y,p,params):
        self.total_pixels = params["total_pixels"]  # number of pixels for averaging
        self.v = x
        self.b = y
        self.param = p
        self.params = params

       
    def openData(self, filename):
        return qs3D.volume(self.params, 256, 256)

        # test (should be = 3 for every DF)
        #data = np.ones((256,256,256))
        #return data

    def openMatlab(self, name, filename, threshold):

        import scipy.io as sio
        arr = np.array(sio.loadmat(filename)[name]).astype(np.int32)
        if name == "S":
            arr = arr > threshold

        # debug - to see the spongious structure
        # plt.imshow((arr[:,:,50]), cmap=plt.gray())
        # plt.show()

        return arr

    # loads a dicom set of files into a 3d numpy array
    def readDicom(self,path):
        lstFilesDCM = []  # create an empty list
        for dirName, subdirList, fileList in os.walk(path):
            for filename in fileList:
                if ".dcm" in filename.lower():  # check whether the file's DICOM
                    lstFilesDCM.append(os.path.join(dirName,filename))

        # Get ref file
        RefDs = dicom.read_file(lstFilesDCM[0])

        # Load dimensions based on the number of rows, columns, and slices (along the Z axis)
        ConstPixelDims = (int(RefDs.Rows), int(RefDs.Columns), len(lstFilesDCM))

        # Load spacing values (in mm)
        ConstPixelSpacing = (float(RefDs.PixelSpacing[0]), float(RefDs.PixelSpacing[1]), float(RefDs.SliceThickness))

        x = numpy.arange(0.0, (ConstPixelDims[0]+1)*ConstPixelSpacing[0], ConstPixelSpacing[0])
        y = numpy.arange(0.0, (ConstPixelDims[1]+1)*ConstPixelSpacing[1], ConstPixelSpacing[1])
        z = numpy.arange(0.0, (ConstPixelDims[2]+1)*ConstPixelSpacing[2], ConstPixelSpacing[2])

        # The array is sized based on 'ConstPixelDims'
        ArrayDicom = numpy.zeros(ConstPixelDims, dtype=RefDs.pixel_array.dtype)

        print "Loading Dicom..."
        # loop through all the DICOM files
        for filenameDCM in lstFilesDCM:
            # read the file
            ds = dicom.read_file(filenameDCM)
            # store the raw image data
            ArrayDicom[:, :, lstFilesDCM.index(filenameDCM)] = ds.pixel_array

        ArrayDicom= numpy.logical_and(ArrayDicom > 3000, ArrayDicom < 6000)
        plt.imshow((ArrayDicom[:,:,220]), cmap=plt.gray())
        plt.show()
        print "loaded!"


        return ArrayDicom


    # get multifractal dimensions
    def getFDs(self,filename):
        cantSelected = 0

        fmask = self.params["mask_filename"]

        threshold = self.params["threshold"]

        data = self.openMatlab(self.params["eight"], filename, threshold)
        data_mask = self.openMatlab(self.params["nine"], fmask, threshold)

        # volume of interest
        # voi = self.params["voi"]

        #data = data*(dataMask==voi)

        # Masking
        data = data * (data_mask > 0)

        # debug
        # print "MAX, MIN: ", np.max(data), np.min(data)

        Nx, Ny, Nz = data.shape

        # debug
        # print data.shape

        self.P = 30#min(Nx,Ny,Nz)-100
        P = self.P

        while Nx < 2*P or Ny < 2*P or Nz < 2*P:
            P /= 2
            self. P = P
            print "P too large. New P: ",  P

        L = float(Nx*Ny*Nz)

        t = time.clock()
        points = []     # number of elements in the structure
        visited_points = [] # points attempted to add

        Nx, Ny, Nz = data.shape

        # Summed Area Table
        intImg = data.cumsum(0).cumsum(1).cumsum(2)
        
        m0 = intImg[Nx-1][Ny-1][Nz-1]

        # debug
        # print m0

        if m0 == 0 :
            print "EMPTY Volume!!!"
            return np.zeros(self.cant*2+1, dtype=np.double )

        if m0 < self.total_pixels :
            print "Warning: volume has less points than expected"
            self.total_pixels = m0/2 # FIX ME

        # FIX ME! Replace all this while's with a selection on white pixels
        # i.e. compute set of white pixels and select from it

        x = randint(P, Nx-1-P)
        y = randint(P, Ny-1-P)
        z = randint(P, Nz-1-P)
        while data[x][y][z] == 0 :
            x = randint(P, Nx-1-P)
            y = randint(P, Ny-1-P)
            z = randint(P, Nz-1-P)
            
        # list with selected points (the points should be in the "structure")
        # points shouldn't be close to the borders, in order for the windows to have the same size

        threshold_trials = 300

        while cantSelected < self.total_pixels:
            trials = 0
            while ([x,y,z] in points) or ([x,y,z] in visited_points) or data[x][y][z] == 0 :
                visited_points.append([x, y, z])

                x = randint(P, Nx-1-P)
                y = randint(P, Ny-1-P)
                z = randint(P, Nz-1-P)
                trials += 1
                if trials > threshold_trials :
                    self.total_pixels = len(points)
                    print "Warning: no more points can be added. Total: ", self.total_pixels
                    break

            if trials > threshold_trials :
                break

            # new point, add to list
            points.append([x, y, z])
            cantSelected += 1

        np.set_printoptions(precision=5)
        np.set_printoptions(suppress=True)

        points = np.array(points).astype(np.int32)

        res = qs3D.aux(self.P, self.total_pixels, Nx, Ny, Nz,
                       points,
                       np.array(intImg).astype(np.int32),
                       m0,
                       self.cant)

        return res

