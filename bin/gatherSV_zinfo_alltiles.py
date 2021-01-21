'''
gather redshift info across all observations for a given target type; for now from a single tile
'''

#standard python
import sys
import os
import shutil
import unittest
from datetime import datetime
import json
import numpy as np
import fitsio
import glob
import argparse
from astropy.table import Table,join,unique,vstack
from matplotlib import pyplot as plt

sys.path.append('../py')

#from this package
import LSS.zcomp.zinfo as zi


parser = argparse.ArgumentParser()
parser.add_argument("--type", help="tracer type to be selected")
#parser.add_argument("--tile", help="observed tile to use") #eventually remove this and just gather everything
parser.add_argument("--release", help="what spectro release to use, e.g. blanc or daily") #eventually remove this and just gather everything
args = parser.parse_args()
type = args.type
#tile = args.tile
release = args.release


from desitarget.sv1 import sv1_targetmask

tarbit = int(np.log2(sv1_targetmask.desi_mask[type]))

#if type == 'LRG':
#    tarbit = 0 #targeting bit
#if type == 'QSO':
#    tarbit = 2
#if type == 'ELG':
#    tarbit = 1

print('gathering all tile data for type '+type +' in '+release)

tp = 'SV1_DESI_TARGET'
print('targeting bit,  target program type; CHECK THEY ARE CORRECT!')
print(tarbit,tp)



#outputs
svdir = '/project/projectdirs/desi/users/ajross/catalogs/SV/'
version = 'v0'
dirout = svdir+'redshift_comps/'+release+'/'+version+'/'+type



if not os.path.exists(svdir+'redshift_comps'):
    os.mkdir(svdir+'redshift_comps')
    print('made '+svdir+'redshift_comps directory')

if not os.path.exists(svdir+'redshift_comps/'+release):
    os.mkdir(svdir+'redshift_comps/'+release)
    print('made '+svdir+'redshift_comps/'+release+' directory')

if not os.path.exists(svdir+'redshift_comps/'+release+'/'+version):
    os.mkdir(svdir+'redshift_comps/'+release+'/'+version)
    print('made '+svdir+'redshift_comps/'+release+'/'+version+' directory')

if not os.path.exists(dirout):
    os.mkdir(dirout)
    print('made '+dirout)
  
expf = '/global/cfs/cdirs/desi/users/raichoor/fiberassign-sv1/sv1-exposures.fits'  
exposures = fitsio.read(expf) #this will be used in depth calculations  

#location of inputs
tiledir = '/global/cfs/cdirs/desi/spectro/redux/'+release+'/tiles'

tiles = np.unique(exposures['TILEID'])
print('looking for data in these tiles:')
print(tiles)

tilew = []
for tile in tiles:
    if tile != 80615: #that tile used cmx target bits
        tile = str(tile)
        coaddir = '/global/cfs/cdirs/desi/spectro/redux/'+release+'/tiles/'+tile
        subsets = [x[0][len(coaddir):].strip('/') for x in os.walk(coaddir)] #something must work better than this, but for now...
        if len(subsets) > 1:
            #print(subsets)
            print('going through tile '+tile)
            outf = dirout +'/'+tile+'_'+type+'zinfo.fits'
            try:
                fitsio.FITS(outf)
                print(outf+' exists already')
                tilew.append(tile)
            except:
                a = zi.comb_subset_vert(tarbit,tp,subsets,tile,coaddir,exposures,outf)
                if a:
                    tilew.append(tile)
        else:
            print('did not find data in '+release +' for tile '+tile)    
      

#combine all the tiles

dt = Table.read(dirout +'/'+tilew[0]+'_'+type+'zinfo.fits')
dt['TILEID'] = int(tilew[0])
for i in range(1,len(tilew)):
    dtn = Table.read(dirout +'/'+tilew[i]+'_'+type+'zinfo.fits')
    dtn['TILEID'] = int(tilew[i])
    dt = vstack([dt,dtn])

dt.sort('TARGETID')
outfall = dirout +'/alltiles_'+type+'zinfo.fits'
dt.write(outfall,format='fits', overwrite=True) 
print('wrote to '+outfall)
    