import numpy as N

from itertools import izip,count 

from analytics.performance import time_analysis

from prm.localdistribution import CPDTabular

class Likelihood(dict):
    '''
    Conditional Likelihood Functions are used to generate the full conditional sampling distributions
    for the Gibbs sampler implemented in :mod:`.mcmc`.
    
    There is an :class:`~!.Likelihood` instance for every probabilistic attribute in the PRM. 
    It implements a dictionary which stores a `conditional likelihood function` of type :class:`.CLF` for every parent attribute 
    of every attribute class key.
    
    Lets say we have an attribute `C` with two parent attributes `A`, `B`. The CPD is given by `P(C|A,B)`. In this case
    the `likelihood functions` of type :class:`.CLF` for attribute `C` are stored in double dictionary::
    
        self[C][A] = P(c|A,b) = L(A|c,b)
        self[C][B] = P(c|a,B) = L(B|c,a)
    
    See :class:`.CLF` for more details. 
    '''    
    def __init__(self, cpd):
        
        self.cpd = cpd
        """
        The :class:`.CPD` instance of the attribute class that the `likelihood functions` are computed for
        """
                        
        #compute conditional likelihood functions CLF for each parent attribute
        for ip, pa in enumerate(self.cpd.attr.parents):
            likAttr = pa
            condAttrs = [cpd.attr]
            condPaAttrs = self.cpd.attr.parents[:]
            condPaAttrs.pop(ip)            
            condAttrs.extend(condPaAttrs)
            #condAttrs.extend([ca for ca in self.cpd.attr.parents if ca!=pa])
            
            self[likAttr] = CLF(likAttr,condAttrs)
            
            #print 'likAttr: ',likAttr.name
            #print 'condAttrs: ', [ca.name for ca in condAttrs]

            
class CLF:
    '''
    `Conditional Likelihood Functions` are used to generate the full conditional sampling distributions
    for the Gibbs sampler implemented in :mod:`inference.mcmc`.
    A `conditional likelihood function` is an instance of the class :class:`.CLF`. Similar to a tabular CPD :class:`.CPDTabular`, :class:`.CLF` constists of a matrix,
    a method :meth:`~inference.likelihood.CLF.indexrow` that indexes a conditional variable assignment. The matrix is composed from values
    of the orginal CPD. 
    
    Lets say we have an attribute `C` with two parent attributes `A`, `B`. The CPD is given by `P(C|A,B)`. In this case
    there will be two `likelihood functions` for attribute `C`::
    
        self[A] = P(c|A,b) = L(A|c,b)
        self[B] = P(c|a,B) = L(B|c,a)

    We note that, as in the case of a normal CPD where the parents are ordered, the order of the conditional variabels
    are fixed in the `likelihood function`. The associated attribute is first, followed by the appropriate parents in the 
    orignial parents. By appropriate parents we mean all parents except the parent attribute for that the likelihood function, e.g.
    
        * For self[A], the order of the conditional parents is (c,b)
        * For self[B], the order of the conditional parents is (c,a)
    
    
    See the class :class:`.Likelihood` for more details.
    
    '''
    
    def __init__(self, likAttr, condAttrs):
        '''
        Initializes the datastrucutre for a Conditional Likelihood Function. The values
        for the likelihood matrices and for  self.likIndex are assignet during the
        configuration() of the gibbs sampler
        '''
        
        self.likAttr = likAttr
        """
        The likelihood attribute of type :class:`.Attribute`
        """
        
        # Index of the likelihood attribute in the list of parent attributes. This is used to efficiently compute the assignment of the conditional variables
        self.likIndex = None
        
        self.condAttrs = condAttrs
        '''The conditional attributes (see :class:`.CLF`)
        '''
        
        # the number of possible assigents to the conditional attributs = number of rows in likMatrix
        self.condAttrAssignments = 1
        self.indexingMultiplier = [1 for p in self.condAttrs] #a multiplier used to access the correct 
        self.initCLF()
        
        # initialize the likelihood matrix
        self.likMatrixDim = [self.condAttrAssignments,likAttr.cardinality]   
        '''Dimensions of the likelihood matrix
        '''
        self.likMatrix = N.zeros( self.likMatrixDim ) 
        '''Likelihood matrix of type :class:`numpy.array`
        '''
        self.likLogMatrix = N.zeros( self.likMatrixDim ) 
        '''The log of :attr:`.likMatrix`
        '''
            
        
    
    def conditionalAssignment(self,parentAssignment):
        '''
        The `parentAssignment` is a full assignmnet to the parent attributes to the 
        original attribute. We remove the entry that corresponds to the likelihood
        attribute. Note that we actually modify this list.
        
        :arg parentAssignment: List of values. Assignments to the parent attributes 
        '''
        parentAssignment.pop(self.likIndex)
        return parentAssignment
        
        
    
    def initCLF(self):
        '''
        Computes the number of possible conditional attribute assigments and the index multipliers needed
        to compute the row index of a given conditional assignment.
        ''' 
        
        ncondAttrsindex= len(self.condAttrs) #temp variable
        for i, ca in enumerate(self.condAttrs):
            #print "condAttr %s , cardinality %s"%(ca.name,ca.cardinality)
                        
            # we calculate the total number of all possible combinations of parent assignments
            self.condAttrAssignments *= ca.cardinality
            
            # the index serves to find the row that corresponds to a specific parents assignment
            for j in range(i+1,ncondAttrsindex):
                #print 'i=%s,j=%s'%(i,j)
                self.indexingMultiplier[i] *= self.condAttrs[j].cardinality

    def computeLikelihood(self,condValues):
        """
        :arg condValues: List of conditional values
        :returns: List of likelihood values for conditional assignment
        """
        ci = self.indexRow(condValues)
        return self.likMatrix[ci,:]


    #@time_analysis    
    def indexRow(self,condValues):
        '''
        Returns the index for the :attr:`.likMatrix` row that corresponds to the assignment of the 
        conditional attributes passed in condValues
        
        :condValues: List of conditional values
        :returns: Index of :attr:`.likMatrix` row
        '''
        index=0
        for i, mult, value in izip(count(),self.indexingMultiplier, condValues):
            index += mult * self.condAttrs[i].indexingValue(value)                    
        return int(index)
           
    def reverseIndexRow(self,index):
        '''
        Returns the list of values that correspond to the conditional assignment of a row of :attr:`.likMatrix`
        
        :arg index: Row of :attr:`.likMatrix`
        :returns: List of conditional values
        '''
        condAssignment = [None for p in self.condAttrs]
        for i,m in enumerate(self.indexingMultiplier):
            condAssignment[i] = self.condAttrs[i].domain[(index/m)] 
            index =  index % m
            
        return condAssignment
    
    def computeLogLik(self):
        '''
        Calculates the log probability distribution :attr:`.likLogMatrix`
        '''
        self.likLogMatrix = N.log(self.likMatrix)
        
        
    def __repr__(self):
                
        #return 'Likelihood Function, Attr=%s, CondAttrs=%s\n%s\n%s'%(self.likAttr.name,[ca.name for ca in self.condAttrs],self.likMatrix,self.likLogMatrix)
        return 'Likelihood Function, Attr=%s, CondAttrs=%s'%(self.likAttr.name,[ca.name for ca in self.condAttrs])        
       
    
