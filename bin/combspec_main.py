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
from desitarget.io import read_targets_in_tiles
from desitarget.mtl import inflate_ledger
from desimodel.footprint import is_point_in_desi

sys.path.append('../py') #this requires running from LSS/bin, *something* must allow linking without this but is not present in code yet

#from this package
#try:
import LSS.SV3.cattools as ct
#except:
#    print('import of LSS.mkCat_singletile.cattools failed')
#    print('are you in LSS/bin?, if not, that is probably why the import failed')   
import LSS.mkCat_singletile.fa4lsscat as fa

parser = argparse.ArgumentParser()
parser.add_argument("--basedir", help="base directory for output, default is CSCRATCH",default=os.environ['CSCRATCH'])
parser.add_argument("--version", help="catalog version; use 'test' unless you know what you are doing!",default='test')
parser.add_argument("--prog", help="dark or bright is supported",default='dark')

args = parser.parse_args()
print(args)

type = args.type
basedir = args.basedir
version = args.version
prog = args.prob
progu = prog.upper()

mt = Table.read('/global/cfs/cdirs/desi/spectro/redux/daily/tiles.csv')
wd = mt['SURVEY'] == 'main'
wd &= mt['EFFTIME_SPEC']/mt['GOALTIME'] > 0.85
wd &= mt['FAPRGRM'] == prog
mtd = mt[wd]
print('found '+str(len(mtd))+' '+prog+' time main survey tiles that are greater than 85% of goaltime')

tiles4comb = Table()
tiles4comb['TILEID'] = mtd['TILEID']
tiles4comb['ZDATE'] = mtd['LASTNIGHT']

#share basedir location '/global/cfs/cdirs/desi/survey/catalogs'
maindir = basedir +'/main/LSS/'




if not os.path.exists(maindir+'/logs'):
    os.mkdir(maindir+'/logs')
    print('made '+maindir+'/logs')

if not os.path.exists(maindir+'/LSScats'):
    os.mkdir(maindir+'/LSScats')
    print('made '+maindir+'/LSScats')

dirout = maindir+'LSScats/'+version+'/'
if not os.path.exists(dirout):
    os.mkdir(dirout)
    print('made '+dirout)


outf = maindir+'datcomb_'+prog+'_spec_premtlup.fits'
ct.combtile_spec(mtld,outf)