'''
combine catalogs from single SV1 deep fields
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
import LSS.mkCat_singletile.cattools as ct
import LSS.mkCat_singletile.fa4lsscat as fa
import LSS.mkCat_singletile.xitools as xt


parser = argparse.ArgumentParser()
parser.add_argument("--type", help="tracer type to be selected")
args = parser.parse_args()

type = args.type

release = 'blanc'
version = 'test'


svdir = '/global/cfs/cdirs/desi/survey/catalogs/SV1/LSS/'
dirout = svdir+'LSScats/'+version+'/'


ffds = glob.glob(dirout+type+'*_deep_full.dat.fits')

dt = Table.read(ffds[0])
for i in range(1,len(ffds)):
    dtn = Table.read(ffds[i])
    dt = vstack([dt,dtn])
dt.write(dirout+type+'alltiles_deep_full.dat.fits',overwrite=True,format='fits')


fcds = glob.glob(dirout+type+'*_deep_clustering.dat.fits')
dt = Table.read(fcds[0])
for i in range(1,len(fcds)):
    dtn = Table.read(fcds[i])
    dt = vstack([dt,dtn])
dt.write(dirout+type+'alltiles_deep_clustering.dat.fits',overwrite=True,format='fits')

rm = 0
rx = 10
for i in range(rm,rx):
    ffrs = glob.glob(dirout+type+'*_deep_'+str(i)+'_full.ran.fits'
    dt = Table.read(fffs[0])
    for ii in range(1,len(ffrs)):
        dtn = Table.read(ffrs[ii])
        dt = vstack([dt,dtn])
    dt.write(dirout+type+'alltiles_deep_full.ran.fits',overwrite=True,format='fits')    

    ffrs = glob.glob(dirout+type+'*_deep_'+str(i)+'_clustering.ran.fits'
    dt = Table.read(fffs[0])
    for ii in range(1,len(ffrs)):
        dtn = Table.read(ffrs[ii])
        dt = vstack([dt,dtn])
    dt.write(dirout+type+'alltiles_deep_clustering.ran.fits',overwrite=True,format='fits')

subts = ['LRG','ELG','QSO','LRG_IR','LRG_OPT','LRG_SV_OPT','LRG_SV_IR','ELG_SV_GTOT','ELG_SV_GFIB','ELG_FDR_GTOT','ELG_FDR_GFIB','QSO_COLOR_4PASS',\
'QSO_RF_4PASS','QSO_COLOR_8PASS','QSO_RF_8PASS']
subtl = []
for subt in subts:
	if subt[:3] == type:
		subtl.append(subt)
print(subtl)
ffd = dirout+type+'alltiles_deep_0_full.dat.fits'
fcd = dirout+type+'alltiles_deep_0_clustering.dat.fits'
fcr = dirout+type+'alltiles_deep_0_clustering.ran.fits'
for subt in subtl:
	fout = dirout+subt+'alltiles_deep_nz.dat'
	ct.mknz(ffd,fcd,fcr,subt,fout)