'''
An implementation of a Metropolis Hastings within Gibbs algorithm. 

The random walk samples the full conditional distributions for normal :class:`.GBNvertex` instances (i.e. Gibbs sampling) and uses a Metropolis within Gibbs step to sample :class:`.ReferenceVertex` instances.

    See :ref:`References<references>` for more details
    
'''

import logging

import numpy as N
import random 

from network.vertices import ReferenceVertex

from inference.mcmc.likelihood import Likelihood
from inference.mcmc import posterior

from analytics.performance import time_analysis

# CHAINS = 1
CHAINS = 3
'''Number of chains to be run
'''

BURNIN = 0
# BURNIN = 100
'''Number of burn in samples 
'''


# ITER = 4
#ITER = 30000
ITER = 1000
'''Number of samples to collect
'''

from inference import engine 
'''The engine module contains the :class:`.GBNgraph` instance
'''

#the likelihood functions for all attributes
likelihoods = {}
'''
Dictionary of likelihood functions that are precomputed when the sampler is configured using :meth:`inference.mcmc.configure`

    { key = :class:`.Attribute` instance : value =  :class:`.Likelihood` of attribute }
    
'''

def run():
    '''
    Sequentally runs :attr:`CHAINS` MCMC runs, the posterior samples are stored in
    :attr:`.posterior.samples`.
    '''

    #  reset collected samples
    posterior.samples = {}

    chain = 'chain_'
    for c in range(CHAINS):
        init(chainID = '%s%s'%(chain,c))

        logging.info('Chain %s, Running Metropolis Hastings sampler (%s iterations)'%((c+1),ITER))
        runChain()
        

@time_analysis
def runChain():
    '''
    Generates posterior samples for the event variables. After :attr:`BURNIN` are sampled,
    :attr:`ITER` samples are collected and stored in :attr:`posterior.currentchain` using
    :meth:`collectSamples`. The initial state of the markov chain has to set in order to
    run a chain, see :meth:`inference.mcmc.mh.init`.
    '''                
    
    #BURNIN phase
    for i in range(BURNIN):        
        mcmcStep()
    
    #Collecting samples
    for i in range(ITER):
        # logging.info("Step %d"%(i+1))
        mcmcStep()        
        posterior.collectSamples(i)
        



# @time_analysis
def mcmcStep():
    '''
    Performs a MCMC sampling step, either a Gibbs step or a Metropolis Hastings. In case of :class:`.GBNvertex` instances we use Gibbs sampling and for :class:`.ReferenceVertex` instances we use a Metropolis within Gibbs step.

    Note that we can exploit the conditional independence by `Lazy Aggregation`. When sampling all event vertices of a certain attribute, we need to perform the (potential aggregation) on the parent vertices only once (see references).
    '''
    
    # Sampling every sampling vertex in the GBN
    for gbnV in engine.GBN.samplingVertices.values():



        # If the vertex is a reference vertex, we apply a MH step
        if isinstance(gbnV,ReferenceVertex):
            mhStep(gbnV)
            

        # If the vertex is a normal vertex, we apply a Gibbs step
        else:
            
            gibbsStep(gbnV)

    # for attrS,gbnVs in engine.GBN.samplingVerticesByAttribute.items():

        
    #     for gbnV in gbnVs:



    #     for dep in attrS.dependenciesParent:
    #         attrC = dep.child
    
    #         if attrC in engine.GBN.allByAttribute:
    #             for gbnV in engine.GBN.allByAttribute[attrC]:
    #                 gbnV.parentAssignments()
        
    #     for gbnV in engine.GBN.samplingVerticesByAttribute[attrS]:      
            
    #         gbnV.parentAssignments()
    #         #we sample new state            
    #         gbnV.value = gibbsStep(gbnV)




@time_analysis
def mhStep(gbnV):

    '''
    Performs a Metropolis Hastings step on the :class:`ReferenceVertex` argument.    
    
    :arg gbnV: :class:`ReferenceVertex` instance    
    '''

    '''
    for now, we assume k=1

    '''
    # the first and only reference, e.g. Professor.1 (k=1)
    old = gbnV.references.values()[0] 

    # select a new proposal
    new = random.choice(engine.GBN.allByAttribute[gbnV.dependency.kAttribute])    
    
    #  the row indices of the CPD entries for the parent assignments

    # logging.info('gbnV = %s'%gbnV.ID)
    # logging.info('gbnV.parentAssignments(old) = %s'%gbnV.parentAssignments(old))
    # logging.info('old parentIndex = %s'%gbnV.attr.CPD.indexRow(gbnV.parentAssignments(old)))

    # logging.info('gbnV.parentAssignments(new) = %s'%gbnV.parentAssignments(new))
    # logging.info('new parentIndex = %s'%gbnV.attr.CPD.indexRow(gbnV.parentAssignments(new)))

    old_pa = gbnV.attr.CPD.indexRow(gbnV.parentAssignments(old))
    new_pa = gbnV.attr.CPD.indexRow(gbnV.parentAssignments(new))
    
    
    # extract the probabilities from the CPD to calculate tha acceptance probability
    p_old0 = gbnV.attr.CPD.cpdMatrix[old_pa,0]
    p_new1 = gbnV.attr.CPD.cpdMatrix[new_pa,1]

    p_old1 = gbnV.attr.CPD.cpdMatrix[old_pa,1]
    p_new0 = gbnV.attr.CPD.cpdMatrix[new_pa,0]

    # acceptance probability
    alpha = p_old0*p_new1/(p_old1*p_new0)

    # logging.info('Old prop.: %s\nNew prop: %s'%(old.ID,new.ID))    
    # logging.info('\t\t%s *  %s'%(p_old0,p_new1))
    # logging.info('alpha= ----------------------= %s'%alpha)
    # logging.info('\t\t%s *  %s'%(p_old1,p_new0))

    # uniform between 0 and 1
    u = N.random.uniform()

    # check whether to accept the proposal
    if u <= alpha:
        gbnV.replaceReference(gbnV_new=new,gbnV_old=old)

    #     logging.info('Accepted new proposal')
    # else:
    #     logging.info('Rejected new proposal')




@time_analysis    
def gibbsStep(gbnV):
    '''
    Computes a random sample distributed according to the sampling distribution - e.g. the 
    full conditional distribution in case of a Gibbs sampler - of the attribute class of `gbnV`.
    
    :arg gbnV: :class:`GBNvertex` instance    
    '''
   
    cumFC = None
    
        
    #TODO  AVOID CREATING NEW LISTS NUMPY.ARRAYS WITH EVERY ITERATION.
    fc = N.ones((1,gbnV.attr.cardinality))
    #fcLog = N.zeros((1,gbnV.attr.cardinality))

    
    # PARENTS assignment    
    gbnV.parentAssignments()

    ri = gbnV.attr.CPD.indexRow(gbnV.parentAss)

    #The local distribution factor of the full conditional
    fc = fc * gbnV.attr.CPD.cpdMatrix[ri,:]
    # fcLog +=  gbnV.attr.CPD.cpdLogMatrix[ri,:]


          
    # print 'Sample Full Conditional for %s'%gbnV.ID
    # print 'paAss:',gbnV.parentAss
    # print 'index:',ri
    # print 'reverse:',gbnV.attr.CPD.reverseIndexRow(ri)
    
    # print 'Prior FC :'
    # print fc    
    # print N.exp(fcLog) / N.exp(fcLog).sum(axis=1)
    

    '''
    CHILDREN likelihoods
    '''     
    for (a,gbnVs) in gbnV.children.items():
    
        for childV in gbnVs.values():
            #the conditional likelihood function
            clf = likelihoods[a][gbnV.attr]            
            #the assignment of conditional variables
            condAss = [childV.value]
        
            #TODO DANGEROUS , ONLY VALID FOR BLOCK GIBBS
            childV.parentAssignments()
        
            # print 'childV.parentAss',childV.parentAss
            # print 'childV.parents',childV.parents
        
            condAss.extend(clf.conditionalAssignment(childV.parentAss[:]))                                     
            #the row index of the conditional variables assignment condAss
        
            # print '%s : condAss=%s'%(childV.ID,condAss)
            li = clf.indexRow(condAss)


            #prob
        
            lik = clf.likMatrix[li,:] 
            fc = fc * lik 
            
            #normalize for stability
            # fc = fc / fc.sum(axis=1)
                        
            # prob 
            # print 'LH for %s (conditional Assign. is %s)'%(childV,condAss)
            # print lik
            # print 'Updated Full conditional'
            # print fc
            # print fc / fc.sum(axis=1)
            
            
            
            #logprob  
            '''
            likLog = clf.likLogMatrix[li,:] 
            fcLog +=  likLog
            '''
            
            # logprob                     
            # print 'LH for %s (conditional Assign. is %s)'%(childV,condAss)
            # print N.exp(likLog)            
            # print 'Updated Full conditional'
            # print fcLog
            # print N.exp(fcLog)
            # print N.exp(fcLog) / N.exp(fcLog).sum(axis=1)
                       
        


    #prob

    #Normalize
    fc = fc / fc.sum(axis=1)
    #Compute cumulative dist
    cumFC = fc.cumsum(axis=1)
    


    '''
    #logprob
    #print fcLog
    fcLog = N.exp(fcLog)
    #Normalize
    fcLog = fcLog / fcLog.sum(axis=1)
    #Compute cumulative dist
    cumLogFC = fcLog.cumsum(axis=1)
    '''
    
    
    '''   
    print 'Children Values:'
    for (a,gbnVs) in gbnV.children.items():
        if len(gbnVs)!=0:
            print '%s: '%a.name,[c.value for c in gbnVs.values()]
    
    '''
    
    '''    
    print 'Normalized FC for %s'%gbnV
    print fcLog            
 
    print 'Cumulative FC for %s'%gbnV
    print cumLogFC
    '''
    '''  
    print 'Normalized FC for %s'%gbnV
    print fc            
 
    print 'Cumulative FC for %s'%gbnV
    print cumFC
    '''            
           
    
    '''
    SAMPLING
    '''    

    u = N.random.uniform()
    

    # prob 
    cumFC[0,:]
    
    for i,cumprop in enumerate(cumFC[0,:]):
        if u <= cumprop:
            gbnV.value = gbnV.attr.domain[i]
            # return!
            return
    '''
    # logprob
    print 'Full conditional', cumLogFC
    for i,cumprop in enumerate(cumLogFC[0,:]):
        if u <= cumprop:
            
            gbnV.value = gbnV.attr.domain[i]
    '''
    

        
    
def init(chainID='standardChain'):
    '''
    Inintializes a `MCMC` run given a Ground Bayesian Network and a set of event variables. 
    The initial state of the markov chain is sampled using :meth:`.initializeVertices`.
    
    :arg currentGBN: :class:`GBNgraph` instance
    :arg chainID: Sting identification of the current run. Optional (default='standardChain'). Running more than one chain requires different chain ids
    ''' 
    
    # posterior event samples
    # posterior.initChain(chainID,ITER,engine.GBN.eventVertices)
    # posterior sampling samples
    posterior.initChain(chainID,ITER)

    #init vertices
    initializeVertices()
    
    



def initializeVertices():
    '''
    Creates an initial state for the markov chain by assigning a value to all sampling vertices
    '''
    for gbnV in engine.GBN.samplingVertices.values():

        # Reference vertex 
        if isinstance(gbnV,ReferenceVertex):

            # remove all ref
            gbnV.removeAllReferences()
            
            kGBNv = random.choice(engine.GBN.allByAttribute[gbnV.dependency.kAttribute])                    

            gbnV.addReference(kGBNv)

            
        # If the vertex is a normal vertex, we apply a Gibbs step
        else:                        
            gbnV.value = random.choice(gbnV.attr.domain)
        

def configure():
    '''
    Configuring an inference algorithm allow the algorithm to precompute as much information as possible before making inference.
    
    In the case of Gibbs sampling, all the conditional likelihood functions, of type :class:`.Likelihood`, 
    for the probabilistic attributes can be precomputed.
    
    '''
    import prm.prm as PRM
    
    for attr in PRM.attributes.values():
        if attr.probabilistic and len(attr.parents) != 0:
            if attr.CPD is None:
                raise Exception('ERROR: No CPD for attribute %s'%attr.fullname)
             
            # logging.info('Likelihood for %s (Pa: %s)'%(attr.name,' , '.join([pa.name for pa in attr.parents])))
            likelihoods[attr] = Likelihood(attr.CPD)
            
            
            #iterating all possible parent assignments (CPD rows)
            for i in range(attr.CPD.cpdMatrixDim[0]):
                #extracting the parent assignment of the current row
                paAss = attr.CPD.reverseIndexRow(i)
                
                #print 'paAss',paAss
                
                #iterating over all CLF that need to be computed
                for ip in range(len(attr.parents)):
                    
                    #the CLF of the current parent attribute 
                    clf = likelihoods[attr][attr.parents[ip]]
                    #assigning the index of the likelihood attribute in the parents list of the attributes
                    clf.likIndex = ip
                    
                    #determine assignment of conditional variables of the CLF that are also parent attributes                    
                    condAssPa = clf.conditionalAssignment(paAss[:])                                    
                    #the assignment of the likelihood attribute
                    likAss = paAss[ip]
                    
                    #logging.debug(clf)
                    #logging.debug('condAssPa %s'%condAssPa)
                    

                    #iterating over all possible values of the CPD attribute domain
                    for j in range(attr.cardinality):
                        # the order of the condintional assignments is [a, pa_1,...,pa_(ip-1),pa_(ip+1),...,pa_n]
                        condAss = [attr.domain[j]]
                        condAss.extend(condAssPa)                        

                                                                    
                        #print 'condAss',condAss
                            
                        #extrating the row and column of the CLF for the current condAss and likAss configuration
                        likRowIndex = clf.indexRow(condAss)
                        likColumnIndex = attr.parents[ip].indexingValue(likAss)
                        #setting the probability and log prob values
                        clf.likMatrix[likRowIndex,likColumnIndex] = attr.CPD.cpdMatrix[i,j]
                        clf.likLogMatrix[likRowIndex,likColumnIndex] = attr.CPD.cpdLogMatrix[i,j]
                
                
            


   
  