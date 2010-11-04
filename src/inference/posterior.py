'''
The posterior distribution results from running inference for a given query using MCMC.
This module contains

* Data structures to collect posterior samples
* Convergence diagnostics

The convergence diagnostics have to be called by the ProbReM project script, e.g. from outside the framework.

'''
import numpy as N
import pylab as PL

from network.groundBN import computeID

samples = {}
'''
Dicitonary containing all the samples collected during inference. It is common to run more than one chain to montitor convergence, the key/value pairs are stored

    { key = 'chainIdentification' : value = :class:`numpy.array` }
'''



currentChain = None
'''
:class:`numpy.array` that is currently being used by the sampler
'''


currentIndex = {}
'''
Dictionary mapping each event variable `ID` to an index used to access :attr:`.currentChain`
'''

def initChain(chainID,ITER,eventVariables):
    '''
    Initializes a new Gibbs run.
    
    :arg chainID: String identification for new chain
    :arg ITER: Number of samples to be collected
    :arg eventVariables: Dictionary containing all event attribute objects
    '''
    global samples,currentChain,currentIndex
    
    currentIndex = {}
    for i,eventVertexID in enumerate(eventVariables.keys()):
        currentIndex[eventVertexID] = i
        

    nVariables = len(eventVariables)

    samples[chainID] = N.zeros((ITER,nVariables))
    currentChain = samples[chainID]
        

def cumulativeMean(chainID=None,gbnV=None,sVarInd=None):
    '''
    Convergence diagnostics that plots the cumulative mean of all the sampling variables in the `currentChain`. If a `chainID` is provided the cumulative mean of the associated chain is plotted instead. If `sVarInd` is provided - e.g. the index of a sampling variable - only the cumulative mean of this variable is plotted.
    
    :arg chainID: Optional identification of chain to be analyzed
    :arg sVarInd: Optional index of event variable to be analyzed
    '''
    chain = currentChain
    if chainID is not None:
        chain = samples[chainID]
    
    #calculate cumulative mean
    cumChain = chain.cumsum(axis=0)
    for i in range(cumChain.shape[0]):
        cumChain[i,:] = cumChain[i,:]/(i+1.)    
        
    #plotting one or all cumulative mean(s)
    PL.figure()
    if sVarInd is not None:
        PL.plot(cumChain[:,sVarInd])
    else:
        for i in range(cumChain.shape[1]):
            PL.plot(cumChain[:,i])


def histogramm(chainID=None, gbnV=None, sVarInd=None):
    '''
    Convergence diagnostics that plots the posterior density function (using the matplotlib histogram) mean of all the sampling variables in the currentChain. 
    If a `chainID` is provided the histogram of the associated chain is plotted instead. If `sVarInd` or `gbnV` is provided, only the histogram of this variable is plotted.
    
    :arg chainID: Optional identification of chain to be analyzed
    :arg sVarInd: Optional index of event variable to be analyzed
    :arg gbnV: Optional :class:`GBNvertex` event variable to be analyzed    
    '''
    chain = currentChain
    if chainID is not None:
        chain = samples[chainID]
            
    #plotting hist for one or all variables?
    PL.figure()
    if gbnV is not None:
        ind = currentIndex[gbnV]
        PL.hist(chain[:,ind])
    
    elif sVarInd is not None:
        PL.hist(chain[:,sVarInd])
    else:
        PL.hist(chain)

def mean(chainID=None, gbnV=None, sVarInd=None, combined=False):
    '''
    Convergence diagnostics. Returns the posterior mean of all the sampling variables in the currentChain. 
    If a `chainID` is provided the mean of the associated chain is returned instead. If `sVarInd` or `gbnV` is provided, only the mean of this variable is returned.
    
    The :meth:`pylab.hist` method is used to compute the histogram
    
    :arg chainID: Optional identification of chain to be analyzed
    :arg sVarInd: Optional index of event variable to be analyzed
    :arg gbnV: Optional :class:`GBNvertex` event variable to be analyzed 
    :arg combined: Optional (default `False`), if `True` the mean of the mean of all event variables is returned (single value).   
    :returns: Posterior mean as :class:`numpy.array`. If `sVarInd` or `gbnV` are specified, this is a single value
    '''
    chain = currentChain
    if chainID is not None:
        chain = samples[chainID]
            
    #computing mean for one or all variables?
    if combined:
        return N.mean(chain)
    elif sVarInd is not None:
        return N.mean(chain[:,sVarInd])
    elif gbnV is not None:
        ind = currentIndex[gbnV]    
        return N.mean(chain[:,ind])
    else:
        return N.mean(chain,0)

def hist():
    '''
    Convergence diagnostics. Returns a histogram of the currentchain in a :class:`numpy.array`. Fast.
    
    The :meth:`numpy.hist` method is used to compute the histogram
    
    :returns: :class:`numpy.array` histogram
    '''
    return N.histogram(currentChain)


def __marginalize(margVariables):
    # not needed
    '''
    Marginalize margVariables which is a subset of all variables
    '''



    
def __repr__():                      
    return 'Posterior distribution module'
            