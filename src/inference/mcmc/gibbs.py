'''
An implementation of a standard Gibbs sampler. The random walk samples the full conditional distributions 
of the sampling attribute in the GBN. The full conditionals are given by:

.. figure:: figures/full_cond.png
    :scale: 70 %    

    See :ref:`References<references>` for more details
    
'''



import numpy as N
import random 

from inference.mcmc.likelihood import Likelihood
from inference.mcmc import posterior

from analytics.performance import time_analysis

# CHAINS = 1
CHAINS = 3
'''Number of chains to be run
'''

# BURNIN = 0
BURNIN = 100
'''Number of burn in samples 
'''


# ITER = 4
#ITER = 30000
ITER = 1000
'''Number of samples to collect
'''

from inference import engine 
''':class:`.GBNgraph` instance
'''

#the likelihood functions for all attributes
likelihoods = {}
'''
Dictionary of likelihood functions that are precomputed when the sampler is configured using :meth:`inference.mcmc.configure`

    { key = :class:`.Attribute` instance : value =  :class:`.Likelihood` of attribute }
    
'''

BLOCKGIBBS = True # False  
'''
If `True` the sampler will collect samples for all event variables of the same attribute class in one block. 
'''


def run():
    '''
    Sequentally runs :attr:`CHAINS` MCMC runs, the posterior samples are stored in
    :attr:`.posterior.samples`.
    '''
    chain = 'chain_'
    for c in range(CHAINS):
        init(chainID = '%s%s'%(chain,c))
        runChain()
        

@time_analysis
def runChain():
    '''
    Generates posterior samples for the event variables. After :attr:`BURNIN` are sampled,
    :attr:`ITER` samples are collected and stored in :attr:`posterior.currentchain` using
    :meth:`collectSamples`. The initial state of the markov chain has to set in order to
    run a chain, see :meth:`inference.mcmc.gibbs.init`.
    '''    
        
    print 'Running Gibbs Sampler (%s iterations)'%ITER
    
    #BURNIN phase
    for i in range(BURNIN):        
        gibbsStep()
    
    #Collecting samples
    for i in range(ITER):
        gibbsStep()
        collectSamples(i)
        



@time_analysis
def gibbsStep():
    '''
    Performs a GIBBS step, either a Block Gibbs or a standard Gibbs step. 
    The method :meth:`.sampleFullConditional` is called to sample a event variable.
    '''
    # global GBN
    '''  
    STANDARD GIBBS : update every sampling vertex in one step
    IMPORTANT: don't forget to uncomment child.parentAssignment() in the fullcondsampler
    
    for gbnV in engine.GBN.samplingVertices.values():        
        #we sample new state    
        
        gbnV.parentAssignments()
                        
        gbnV.value = sampleFullConditional(gbnV)
          
    '''
    
    
    '''
    RANDOM GIBBS : sample one randomly selected vertex
    
    gbnV = random.choice(engine.GBN.samplingVertices.values())
    #we sample new state 
    gbnV.value = sampleFullConditional(gbnV)
    '''
    
    
    if BLOCKGIBBS:
        '''  
        LAZY BLOCK GIBBS : sample every vertex of the same, randomly selected, attribute
        '''
        attrS = random.choice(engine.GBN.samplingVerticesByAttribute.keys())
        
        # print 'Chosen sampling attr:',attrS.fullname
        
        for dep in attrS.dependenciesParent:
            attrC = dep.child
            if attrC in engine.GBN.allByAttribute:
                for gbnV in engine.GBN.allByAttribute[attrC]:                                                            
                    gbnV.parentAssignments()
        
        for gbnV in engine.GBN.samplingVerticesByAttribute[attrS]:      
                
            gbnV.parentAssignments()
            #we sample new state  
            print 'Old Value for %s : %s'%(gbnV.ID,gbnV.value)   
            gbnV.value = sampleFullConditional(gbnV)
            # print 'New Value for %s : %s'%(gbnV.ID,gbnV.value)
    
    
    else:
        '''  
        LAZY STANDARD GIBBS
        '''
        for attrS in engine.GBN.samplingVerticesByAttribute.keys():
            for dep in attrS.dependenciesParent:
                attrC = dep.child
        
                if attrC in engine.GBN.allByAttribute:
                    for gbnV in engine.GBN.allByAttribute[attrC]:
                        gbnV.parentAssignments()
            
            for gbnV in engine.GBN.samplingVerticesByAttribute[attrS]:      
                
                gbnV.parentAssignments()
                #we sample new state            
                gbnV.value = sampleFullConditional(gbnV)
    


def collectSamples(nSample):
    """
    Stores a sampled state (e.g. one value for each event variable) in the :attr:`posterior.currentchain`
    
    :arg nSample: Int Count of the collected sample.
    """
    # global GBN
    for (i,gbnV) in enumerate(engine.GBN.eventVertices.values()):                
        
        posterior.currentChain[nSample,i] = gbnV.value


@time_analysis    
def sampleFullConditional(gbnV):
    '''
    Returns a random sample distributed according to the sampling distribution - e.g. the 
    full conditional distribution in case of a Gibbs sampler - of the attribute class of `gbnV`.
    
    :arg gbnV: :class:`GBNvertex` 
    :returns: Random sample
    
    '''
   
    cumFC = None
    
        
    #TODO  AVOID CREATING NEW LISTS NUMPY.ARRAYS WITH EVERY ITERATION.
    fc = N.ones((1,gbnV.attr.cardinality))
    #fcLog = N.zeros((1,gbnV.attr.cardinality))

    '''
    PARENTS assignment
    '''
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
    for i,cumprop in enumerate(cumFC[0,:]):
        if u <= cumprop:
            return gbnV.attr.domain[i]
    '''
    # logprob
    print 'Full conditional', cumLogFC
    for i,cumprop in enumerate(cumLogFC[0,:]):
        if u <= cumprop:
            
            return gbnV.attr.domain[i]
    '''
    

        
    
def init(chainID='standardChain'):
    '''
    Inintializes a `MCMC` run given a Ground Bayesian Network and a set of event variables. 
    The initial state of the markov chain is sampled using :meth:`.initializeVertices`.
    
    :arg currentGBN: :class:`GBNgraph` instance
    :arg chainID: Sting identification of the current run. Optional (default='standardChain'). Running more than one chain requires different chain ids
    ''' 
    
    #posterior samples
    posterior.initChain(chainID,ITER,engine.GBN.eventVertices)

    #init vertices
    initializeVertices()
    
    



def initializeVertices():
    '''
    Creates an initial state for the markov chain by assigning a value to all sampling vertices
    '''
    for gbnV in engine.GBN.samplingVertices.values():
        gbnV.value = gbnV.attr.domain[0]        
        

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
             
            print 'Likelihood for %s (Pa: %s)'%(attr.name,' , '.join([pa.name for pa in attr.parents]))
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
                    
                    #print clf
                    #print 'condAssPa',condAssPa
                    

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
                
                
            


   
  