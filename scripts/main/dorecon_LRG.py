import os
import logging
import datetime
import argparse
import re

import numpy as np
import yaml

from astropy.table import Table

import pyrecon
from pyrecon import  utils,IterativeFFTParticleReconstruction,MultiGridReconstruction

from LSS.tabulated_cosmo import TabulatedDESI
cosmo = TabulatedDESI()
comoving_distance = cosmo.comoving_radial_distance


parser.add_argument("--basedir", help="base directory for output, default is CSCRATCH",default=os.environ['CSCRATCH'])
parser.add_argument("--version", help="catalog version; use 'test' unless you know what you are doing!",default='test')
parser.add_argument("--verspec",help="version for redshifts",default='everest')
parser.add_argument("--nthreads",default=1)
parser.add_argument("rectype",help="IFT or MG supported so far",default='MG')
parser.add_argument("convention",help="recsym or disp supported so far",default='recsym')


args = parser.parse_args()
print(args)

basedir = args.basedir
version = args.version
specrel = args.verspec


maindir = basedir +'/main/LSS/'

ldirspec = maindir+specrel+'/'
    
dirout = ldirspec+'LSScats/'+version+'/'


regl = ['_N','_S','_DN']
position_columns = ['RA','DEC','Z']
zmin = 0.3
zmax = 1.2
bias = 1.8
beta = 0.4
ff = beta*bias

if args.rectype == 'MG':
    recfunc = MultiGridReconstruction
if args.rectype == 'IFT':
    recfunc = IterativeFFTParticleReconstruction

def getrdz_fromxyz(cat):
    distance, ra, dec = utils.cartesian_to_sky(cat)
    distance_to_redshift = utils.DistanceToRedshift(comoving_distance())
    z = distance_to_redshift(distance)   
    return ra,dec,z 
    
for reg in regl:
    fb = dirout+'LRGzdone'+reg
    fcr = fb+'_0_clustering.ran.fits'
    fcd = fb+'_clustering.dat.fits'
    
    dat_cat = fitsio.read(fcd)
    seld = dat_cat['Z'] > zmin
    seld &= dat_cat['Z'] < zmax
    dat_cat = dat_cat[seld]
    
    ran_cat = fitsio.read(fcr)
    selr = ran_cat['Z'] > zmin
    selr &= ran_cat['Z'] < zmax
    ran_cat = ran_cat[seld]

    dat_dis = comoving_distance(dat_cat[position_columns[2]])
    pos_dat = utils.sky_to_cartesian(distance,dat_cat[position_columns[0]],dat_cat[position_columns[1]])
    ran_dis = comoving_distance(ran_cat[position_columns[2]])
    pos_ran = utils.sky_to_cartesian(distance,ran_cat[position_columns[0]],ran_cat[position_columns[1]])
    
    recon = recfunc(f=0.8, bias=2.0, los='local',positions=pos_ran,nthreads=args.nthreads)
    recon.assign_data(pos_dat,dat_cat['WEIGHT'])
    recon.assign_randoms(pos_ran,ran_cat['WEIGHT'])
    recon.set_density_contrast()
    recon.run()
    
    positions_rec = {}
    if args.rectype == 'IFT':
        positions_rec['data'] = pos_dat - recon.read_shifts('data', field='disp+rsd')
    else:
        positions_rec['data'] = pos_dat - recon.read_shifts(pos_dat, field='disp+rsd')
    
    positions_rec['randoms'] = pos_ran - recon.read_shifts(pos_ran, field='disp+rsd' if args.convention == 'recsym' else 'disp')
    
    fcro = fb+'_0_clustering_recon.ran.fits'
    fcdo = fb+'_clustering_recon.dat.fits'
    
    datt = Table(dat_cat)
    ra,dec,z = getrdz_fromxyz(positions_rec['data'])
    datt['RA'] = ra
    datt['DEC'] = dec
    datt['Z'] = z
    datt.write(fcdo,format='fits',overwrite=True)
    print('wrote data to '+fcdo)
    
    rant = Table(ran_cat)
    ra,dec,z = getrdz_fromxyz(positions_rec['randoms'])
    rant['RA'] = ra
    rant['DEC'] = dec
    rant['Z'] = z
    rant.write(fcro,format='fits',overwrite=True)
    print('wrote data to '+fcro)
   
    
    