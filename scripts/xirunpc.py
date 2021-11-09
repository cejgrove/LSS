import os
import argparse
import logging
import numpy as np
from astropy.table import Table, vstack
from matplotlib import pyplot as plt

from pycorr import TwoPointCorrelationFunction, utils, project_to_multipoles, project_to_wp, setup_logging
from LSS.tabulated_cosmo import TabulatedDESI
cosmo = TabulatedDESI()
distance = cosmo.comoving_radial_distance

parser = argparse.ArgumentParser()
parser.add_argument("--type", help="tracer type to be selected")
parser.add_argument("--basedir", help="base directory for output, default is desi catalog directory",default='/global/cfs/cdirs/desi/survey/catalogs')
parser.add_argument("--version", help="catalog version; use 'test' unless you know what you are doing!",default='test')
parser.add_argument("--verspec",help="version for redshifts",default='everest')
parser.add_argument("--survey",help="e.g., SV3 or main",default='SV3')
parser.add_argument("--nran",help="number of random files to combine together (1-18 available)",default=10)
parser.add_argument("--weight_type",help="types of weights to use",default='angular_bitwise')
parser.add_argument("--bintype",help="log or lin",default='log')

args = parser.parse_args()

ttype = args.type
basedir = args.basedir
version = args.version
specrel = args.verspec
survey = args.survey
nran = int(args.nran)
weight_type = args.weight_type

if args.bintype == 'log':
    bine = np.logspace(-1.5, 2.2, 80)
if args.bintype == 'lin':
    bine = np.linspace(1e-4, 200, 40)

dirxi = os.environ['CSCRATCH']+'/'+survey+'xi/'
lssdir = basedir+'/'+survey+'/LSS/'+specrel+'/LSScats/'
dirname = lssdir + version
#dirout = svdir+'LSScats/'+version+'/'

zmask = ['']
minn = 0

subt = None

if ttype[:3] == 'LRG':
    zl = [0.4,0.6,0.8,1.1]


if ttype[:3] == 'ELG':# or type == 'ELG_HIP':
    #minn = 5
    zl = [0.8,1.1,1.5]
    #zmask = ['','_zmask']
    
    #zmin = 0.8
    #zmax = 1.6


if ttype == 'QSO':
    zl = [0.8,1.1,1.5,2.1]
    #zmin = 1.
    #zmax = 2.1

   

if ttype[:3] == 'BGS':
    #minn = 2
    zl = [0.1,0.3,0.5]
    #zmin = 0.1
    #zmax = 0.5 


def compute_correlation_function(mode, edges, tracer='LRG', region='_N', nrandoms=4, zlim=(0., np.inf), weight_type=None, nthreads=8, dtype='f8', wang=None):
    data_fn = os.path.join(dirname, '{}{}_clustering.dat.fits'.format(tracer, region))
    randoms_fn = [os.path.join(dirname, '{}{}_{:d}_clustering.ran.fits'.format(tracer, region, iran)) for iran in range(nrandoms)]
    data = Table.read(data_fn)
    randoms = vstack([Table.read(fn) for fn in randoms_fn])
    corrmode = mode
    if mode == 'wp':
        corrmode = 'rppi'
    if mode == 'multi':
        corrmode = 'smu'
    if corrmode == 'smu':
        edges = (edges, np.linspace(0., 1., 101))
    if corrmode == 'rppi':
        edges = (edges, np.linspace(0., 40., 41))
    
    def get_positions_weights(catalog, name='data'):
        mask = (catalog['Z'] >= zlim[0]) & (catalog['Z'] < zlim[1])
        positions = [catalog['RA'][mask], catalog['DEC'][mask], distance(catalog['Z'][mask])]
        if weight_type is None:
            weights = None
        else:
            weights = np.ones_like(positions[0])
        if name == 'data':
            if 'photometric' in weight_type:
                rfweight = RFWeight(tracer=tracer)
                weights *= rfweight(positions[0], positions[1])
            if 'zfail' in weight_type:
                weights *= catalog['WEIGHT_ZFAIL'][mask]
            if 'completeness' in weight_type:
                weights *= catalog['WEIGHT'][mask]/catalog['WEIGHT_ZFAIL'][mask]
            elif 'bitwise' in weight_type:
                weights = list(catalog['BITWEIGHTS'][mask].T) + [weights]
        return positions, weights
    
    data_positions, data_weights = get_positions_weights(data, name='data')
    randoms_positions, randoms_weights = get_positions_weights(randoms, name='randoms')

    kwargs = {}
    if 'angular' in weight_type and wang is None:
        
        data_fn = os.path.join(dirname, '{}_full.dat.fits'.format(tracer))
        randoms_fn = [os.path.join(dirname, '{}_{:d}_full.ran.fits'.format(tracer, iran)) for iran in range(nrandoms)]
        parent_data = Table.read(data_fn)
        parent_randoms = vstack([Table.read(fn) for fn in randoms_fn])
        
        def get_positions_weights(catalog, fibered=False):
            mask = catalog['PHOTSYS'] == region
            if fibered: mask &= catalog['LOCATION_ASSIGNED']
            positions = [catalog['RA'][mask], catalog['DEC'][mask], catalog['DEC'][mask]]
            if fibered: weights = list(catalog['BITWEIGHTS'][mask].T)
            else: weights = np.ones_like(positions[0])
            return positions, weights
    
        fibered_data_positions, fibered_data_weights = get_positions_weights(parent_data, fibered=True)
        print(len(fibered_data_weights),len(fibered_data_positions[0]),len(parent_data))
        parent_data_positions, parent_data_weights = get_positions_weights(parent_data)
        parent_randoms_positions, parent_randoms_weights = get_positions_weights(parent_randoms)
        
        tedges = np.logspace(-3.5, 0.5, 31)
        # First D1D2_parent/D1D2_PIP angular weight
        wangD1D2 = TwoPointCorrelationFunction('theta', tedges, data_positions1=fibered_data_positions, data_weights1=fibered_data_weights,
                                               randoms_positions1=parent_data_positions, randoms_weights1=parent_data_weights,
                                               estimator='weight', engine='corrfunc', position_type='rdd', nthreads=nthreads, dtype=dtype)

        # First D1R2_parent/D1R2_IIP angular weight
        # Input bitwise weights are automatically turned into IIP
        wangD1R2 = TwoPointCorrelationFunction('theta', tedges, data_positions1=fibered_data_positions, data_weights1=fibered_data_weights,
                                               data_positions2=parent_randoms_positions, data_weights2=parent_randoms_weights,
                                               randoms_positions1=parent_data_positions, randoms_weights1=parent_data_weights,
                                               randoms_positions2=parent_randoms_positions, randoms_weights2=parent_randoms_weights,
                                               estimator='weight', engine='corrfunc', position_type='rdd', nthreads=nthreads, dtype=dtype)
        wang = {}
        wang['D1D2_twopoint_weights'] = wangD1D2
        wang['D1R2_twopoint_weights'] = wangD1R2
    
    kwargs.update(wang or {})

    result = TwoPointCorrelationFunction(corrmode, edges, data_positions1=data_positions, data_weights1=data_weights,
                                         randoms_positions1=randoms_positions, randoms_weights1=randoms_weights,
                                         engine='corrfunc', position_type='rdd', nthreads=nthreads, dtype=dtype, **kwargs)
    if mode == 'multi':
        return project_to_multipoles(result), wang
    if mode == 'wp':
        return project_to_wp(result), wang
    return result.sep, result.corr, wang    

ranwt1=False

regl = ['_N','_S']

if survey == 'main':
    regl = ['_DN','_DS','_N','_S','']

for i in range(0,len(zl)):
    if i == len(zl)-1:
        zmin=zl[0]
        zmax=zl[-1]
    else:
        zmin = zl[i]
        zmax = zl[i+1]
    print(zmin,zmax)
    for zma in zmask:
        for reg in regl:
            (sep, xiell), wang = compute_correlation_function(mode='multi', edges=bine, tracer=ttype, region=reg, zlim=(zmin,zmax), weight_type=weight_type)
            #fo = open(dirxi+'xi024'+ttype+survey+version+args.bintype+'.dat','w')
            #for i in range(0,len(sep)):
            #    fo.write(str(sep[i])+' '+str(xiell[0][i])+' '+str(xiell[2][i])+' '+str(xiell[4][i])+'\n')
            #fo.close()
            if args.bintype == 'log':
                plt.loglog(sep,xiell[0])
            if args.bintype == 'lin':
                plt.plot(sep,sep**2.*xiell[0])
            plt.title(ttype+' '+str(zmin)+'<z<'+str(zmax)+' in '+reg)
            plt.show()    