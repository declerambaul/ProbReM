'''
The posterior distribution results from running inference for a given query using MCMC.
This module contains

* Data structures to collect posterior samples
* Convergence diagnostics

The convergence diagnostics have to be called by the ProbReM project script, e.g. from outside the framework.

'''

import logging


import numpy as N
import pylab as PL

from network.vertices import ReferenceVertex

from inference import engine 
'''The engine module contains the :class:`.GBNgraph` instance
'''



samples = {}
'''
Dicitonary containing all the samples collected during inference. It is common to run more than one chain to montitor convergence, the key/value pairs are stored

    { key = 'chainIdentification' : value = :class:`numpy.array` }
'''

currentChain = None
'''
:class:`numpy.array` that is currently being used by the sampler
'''

posteriorVertices = None
'''
Dictionary of vertices that we are collecting samples from (e.g. the event vertices or all sampling vertices including latent variables), set 
'''

currentIndex = {}
'''
Dictionary mapping each event variable `ID` to an index used to access :attr:`.currentChain`
'''

def initChain(chainID,ITER,onlyEvent=False):
    '''
    Initializes a new MCMC run. Note that `onlyEvent=False`, so the samples or all `engine.GBN.samplingVertices` are collected. But the posterior is a joint distribution over the event variables (thus the other sampling variables are already marginalized)
    
    :arg chainID: String identification for new chain
    :arg ITER: Number of samples to be collected
    :arg onlyEvent: Bolean, if `True` only the values of the event vertices are collected (i.e. not latent sampling variables)
    '''
    global samples,currentChain,currentIndex,posteriorVertices
    
    posteriorVertices = engine.GBN.samplingVertices

    if onlyEvent:
        posteriorVertices = engine.GBN.eventVertices

    currentIndex = {}
    for i,vertexID in enumerate(posteriorVertices.keys()):
        currentIndex[vertexID] = i
        

    nVariables = len(posteriorVertices)

    samples[chainID] = N.zeros((ITER,nVariables))
    currentChain = samples[chainID]
        

def collectSamples(nSample):
    '''
    Extracting the value of a node and storing it in the appropriate `numpy.array`, :attr:`.currentChain`.
    
    :arg nSample: Int Count of the collected sample, i.e. the row number
    '''    
    
    for gbnID,gbnV in posteriorVertices.items():
        
        # If the vertex is a reference vertex, we collect the current reference 
        if isinstance(gbnV,ReferenceVertex):

            i = currentIndex[gbnID]

            # at this point we are assuming that k=1
            # we can extract the ID using the 1st entry of the obj list of the attribute, e.g.  2 in e.g. 'Professor.fame.2' 
            currentChain[nSample,i] = gbnV.references.values()[0].obj[0]
            

        # If the vertex is a normal vertex, we collect the sampled value
        else:
            
            i = currentIndex[gbnID]
            currentChain[nSample,i] = gbnV.value


def plotCumulativeMeanAllChains(**kwargs):
    '''
    Plots the cumulative mean of all available chains using :meth:`.cumulativeMean`.
    If the plots are to be displayed on the same figure, use the `figID` keyword.
    If the plots are to display only a specific variable, use the `gbnV` or `varIndex` keyword.

    :arg kwargs: Optional arguments for :meth:`.cumulativeMean`
    '''    
    # create new figure to plot all chains in
    fig = PL.figure()     
    for chainID in samples.keys():        
        plotCumulativeMean(fig=fig,chainID=chainID, **kwargs)        


def plotCumulativeMean(**kwargs):    
    '''
    Convergence diagnostics that plots the cumulative mean of all the sampling variables in the `currentChain`. If a `chainID` is provided the cumulative mean of the associated chain is plotted instead. If `sVarInd` is provided - e.g. the index of a sampling variable - only the cumulative mean of this variable is plotted.
    
    :arg chainID: Optional identification of chain to be analyzed
    :arg varIndex: Optional index of event variable to be analyzed
    :arg gbnV: Optional :class:`GBNvertex` to be analyzed
    :arg fig: Optional `matplotlib.figure.Figure` to be used 
    '''

    chain = currentChain
    if 'chainID' in kwargs:
        chain = samples[kwargs['chainID']]
    
    #calculate cumulative mean
    cumChain = cumulativeMean(chain)
        
    # either plot on a new or specific figure window
    fig = None
    if 'fig' in kwargs:
        fig = kwargs['fig']
        PL.figure(fig.number)
    else:
        fig = PL.figure()
        

    if 'varIndex' in kwargs:
        PL.plot(cumChain[:,kwargs['varIndex']])        
        PL.xlabel('Samples for index %s'%kwargs['varIndex'])
        PL.ylabel('Mean')        
    elif 'gbnV' in kwargs:
        gbnID = kwargs['gbnV'].ID
        PL.plot(cumChain[:,currentIndex[gbnID]])
        PL.xlabel('Samples for %s'%gbnID)
        PL.ylabel('Mean')        
    else:
        # plot cumulative for all posterior variables in subplots

        for i,pID in enumerate(posteriorVertices.keys()):        
            PL.subplot(len(posteriorVertices),1,(i+1))            
            PL.plot(cumChain[:,currentIndex[pID]])            
            PL.xlabel('Samples for %s'%pID)
            PL.ylabel('Mean')


def cumulativeMean(chain):
    '''
    Returns the cumulative mean of `chain`. 

    :arg chain: `numpy.array` 
    '''
    cumChain = chain.cumsum(axis=0)
    for i in range(cumChain.shape[0]):
        cumChain[i,:] = cumChain[i,:]/(i+1.)    

    return cumChain

def mean(chainID=None, gbnV=None, sVarInd=None, combined=False):
    '''
    Returns the posterior mean of all the sampling variables in the currentChain. 
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


def histogramm(**kwargs):
    '''
    Convergence diagnostics that plots the posterior density function (using the matplotlib histogram) mean of all the sampling variables in the currentChain. 
    If a `chainID` is provided the histogram of the associated chain is plotted instead. If `varIndex` or `gbnV` is provided, only the histogram of this variable is plotted.
    
    :arg chainID: Optional identification of chain to be analyzed
    :arg varIndex: Optional index of event variable to be analyzed
    :arg gbnV: Optional :class:`GBNvertex` event variable to be analyzed    
    :arg fig: Optional `matplotlib.figure.Figure` to be used 
    '''
    chain = currentChain
    if 'chainID' in kwargs:
        chain = samples[kwargs['chainID']]
        
    
    # either plot on a new or specific figure window
    fig = None
    if 'fig' in kwargs:
        fig = kwargs['fig']
        PL.figure(fig.number)
    else:
        fig = PL.figure()
                
    if 'varIndex' in kwargs:        
        PL.hist(chain[:,kwargs['varIndex']])
    elif 'gbnV' in kwargs:        
        PL.hist(chain[:,currentIndex[kwargs['gbnV'].ID]])
    else:
        logging.info("WARNING: no posterior variable passed as argument for histogramm")
        PL.hist(chain)



def gelman_rubin():
    '''
    Plots the Gelman Rubin convergence diagnostic, according to `Probabilistic Graphical Models` (p. 523).
    '''

    # extract the number of samples M 
    M = engine.inferenceAlgo.ITER
    # number of discarded samples (burnin)
    T = engine.inferenceAlgo.BURNIN
    # number of chains
    K = engine.inferenceAlgo.CHAINS


    # cumulative mean of for all chains
    # f^{bar}_{k} in koller book
    f_bar_K = {}
    for ID,chain in samples.items():
        f_bar_k = cumulativeMean(chain)
        f_bar_K[ID] = f_bar_k
    
    # cumulative mean across all chains
    # f^{bar} in koller book
    f_bar = N.zeros(currentChain.shape,dtype=float)
    for f_bar_k in f_bar_K.values():
        f_bar += f_bar_k
    f_bar /= K

    # between chain variance
    # B in koller book
    B = N.zeros(currentChain.shape,dtype=float)
    for f_bar_k in f_bar_K.values():
        B += (f_bar_k - f_bar)**2
    B *= M/(K-1)

    # with-in chain variance
    # W in koller book
    W = N.zeros(currentChain.shape,dtype=float)
    # With just one sample variance will be inf
    # W[0,:] = N.inf
    W[0,:] = 1
    for ID,chain in samples.items():
        for j in range(1,M):
            W[j,:] += 1./(j)*((chain[0:(j+1),:]-f_bar_K[ID][j,:])**2).sum(axis=0)
        # W += ((chain - f_bar_K[ID])**2).cumsum(axis=0)

    W *= (1./K)

    # An estimator that can be shown to overestimate the variance
    # V in koller book
    V = (M-1.)/M * W + 1./M * B

    # For M to ininity, both V and W converge to the true variance of the estimate
    
    # Measure of disagreement between the chains
    # R_hat is koller book

    R_hat = N.sqrt(V/W)

    # print 'samples',samples.values()
    # print 'f_bar_K',f_bar_K
    # print 'f_bar',f_bar
    # print 'B',B
    # print 'W',W 
    # print 'V',V 
    # print 'R_hat',R_hat

    PL.figure()

    for i,pID in enumerate(posteriorVertices.keys()):        

        PL.subplot(len(posteriorVertices),1,(i+1))
        PL.plot(R_hat[1:,currentIndex[pID]])
        PL.xlabel(pID)
        PL.ylabel('Gelman-Rubin')
    
    return R_hat
    
def autocorrelation(max_l = 50, **kwargs):
    '''
    Plots the autocorrelation. Computed according to `Probabilistic Graphical Models` (p. 521). 

    :arg max_l: The autocorellation will be calculated up to lag `max_l` (default=50)
    :arg chainID: Optional identification of chain to be analyzed
    '''
    chain = currentChain
    if 'chainID' in kwargs:
        chain = samples[kwargs['chainID']]


    # extract the number of samples M 
    M = engine.inferenceAlgo.ITER
    
    # The cumulative mean
    E_bar = cumulativeMean(chain)

    # The `cumulative` Variance (equation 12.27)
    V = N.zeros(chain.shape,dtype=float)
    # Variance with one sample would be infinite I guess
    V[0,:] = N.inf
    for j in range(1,M):
        V[j,:] = 1./(j)*((chain[0:(j+1),:]-E_bar[j,:])**2).sum(axis=0)

    # Note that so far we have calculated the cumulative values or the mean and variance, i.e. E_bar and V are M x |Y| matrices
    # However, for the covariance and the autocorrelation we only use the mean/variance for all M samples, i.e. V[-1,:] and E_bar[-1,:]

    # The covariance (equation 12.28)
    # A max_l x |Y| matrix, column `l` is the covariance with lag `l`
    C = N.zeros((max_l,chain.shape[1]),dtype=float)
    # For l=0, the covariance is equal to the variane
    C[0,:] = V[-1,:]
    for l in range(1,max_l):
        C[l,:] = 1./(M-l) * ((chain[0:(M-l),:]-E_bar[-1])*(chain[l:,:]-E_bar[-1])).sum(axis=0)


    

    # autocorrelation   
    A = C / V[-1,:]

    # print A

    PL.figure()

    for i,pID in enumerate(posteriorVertices.keys()):        

        PL.subplot(len(posteriorVertices),1,(i+1))
        PL.bar(N.arange(max_l), A[:,currentIndex[pID]])        
        PL.xlabel(pID)
        PL.ylabel('Autocorrelation')
    




def __marginalize(margVertices):
    '''
    TODO: Marginalize `margVertices` (which must be a subset of `posteriorVertices`) from the posterior
    '''



    
def __repr__():                      
    return 'Posterior distribution module'
            