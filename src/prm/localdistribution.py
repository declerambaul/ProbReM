'''
The model parameters in a ProbReM project are the `conditional probability distributions` (CPDs) defined for each probabilistic attribute defined in the model. They are also refered to as `local distributions` interchangeably. 

.. inheritance-diagram:: prm.localdistribution
'''

import logging

#from pylab import * 
import numpy as N

from itertools import izip,count,product 

from analytics.performance import time_analysis



class CPD():
    '''
    A conditional probability distribution CPD is defined for an attribute. This is an abstract 
    version of a CPD that defines a set of methods all CPD implementations must provide.
    '''
    
    def __init__(self, attr):
        
        self.attr = attr
        """The :class:`.Attribute` that the CPD is associated with
        """
            
    
    def sample(self,paAssignment):
        """        
        :arg paAssignment: List of parent values
        :returns: Randomly drawn sample of the CPD given the `paAssignment` 
        """
        raise Exception('Sampling not implemented for %s'%(self.__class__.__name__))
        
    def logLikelihood(self,fullAssignment):
        """
        :arg fullAssignment: List of values order such that [attributeValue,ParentValue1,ParentValue2,....] 
        :returns: Loglikelihood of `fullAssignment`
        """
        raise Exception('logLikelihood not implemented for %s'%(self.__class__.__name__))
        
    def save(self):
        """Saves the CPD to disk
        """
        raise Exception('saving of CPD not supported for %s'%(self.__class__.__name__))

    def conditionalDist(self,gbnV):
        raise Exception('Conditional Distribution not implemented for %s'%(self.__class__.__name__))
    
    
class CPDTabular(CPD):
    """
    The tabular representation of a CPD for discrete variables. A matrix of dimensions `m x n`, where
    
    * `m` is the number of possible parent assignments :math:`\prod_{pa \in Parents} |V(pa)|`
    * `n` is the cardinalitiy of the attribute domain :math:`|V(attr)|`
    
    This matrix grows exponentially with the number of parents, thus not suited for large V-Structures.

    .. todo::

        The rows of the `CPDTabular.cpdMatrix` are the possible parent assignments. Naturally the ordering of indexing matters, and it depends on the order of the attributes in the `attr.parents` list (it is set in :meth:`.PRMparser.start_element`). The order in which the dependencies in the model specification are defined sets the order of the `attr.parents`. The problem is that when the CPDs are loaded from file, but the specification of the dependencies changed, it is possible that the CPD is incorrect.

    """
    
    def __init__(self, attr):
        '''
        The CPD will be stored, inefficiently, in a matrix of dimension [  product of domain size of all parents  ,  size of domain of attribute]
        '''
        CPD.__init__(self,attr)
        
        self.parentAssignments = 1
        self.indexingMultiplier = [1 for p in self.attr.parents] #a multiplier used to access the correct 
        self.initCPD()
                            
        # initialize the probability matrix
        self.cpdMatrixDim = [self.parentAssignments,attr.cardinality]   
        """Dimension of `cpdMatrix`
        """
        self.cpdMatrix = N.zeros( self.cpdMatrixDim ) 
        """The CPD matrix of type `numpy.array`. The rows represent different parent assignments, the columns of a row define the distribution over the attribute.
        """
        self.cpdLogMatrix = None
        """Log values of `cpdMatrix`
        """
        
        #the cumulative distribution for sampling
        self.cumMatrix = N.zeros( self.cpdMatrixDim ) 
        """Cumulativ `cpdMatrix`. Computed by :meth:`.computeCumulativeDist`
        """
        self.cumLogMatrix = None
        """Log values of `cumMatrix`
        """
        
              
        
    
    def sample(self,paAssignment):
        ''' 
        Samples a random value using `cumMatrix`
        
        :arg paAssignment: List of parent values
        :returns: Randomly drawn sample of the CPD given the `paAssignment`
        '''
        #print 'paAssignment ',paAssignment
        
        ri = self.indexRow(paAssignment)
        #print 'rowIndex ',rowIndex
        
        
        u = N.random.uniform()
        
        # If the attribute doesn't have any parents, the CPD is a 1 x n vector and 
        # thus can't be indexed 
        cumRow = self.cumMatrix[ri,:]
        # cumRow = N.atleast_2d(self.cumMatrix)[ri,:]
        for i,cumprop in enumerate(cumRow):
            if u <= cumprop:
                return self.attr.domain[i]
    
    
    def logLikelihood(self,fullAssignment):
        '''
        :arg fullAssignment: List of values order such that [`attributeValue`,`parentValue1`,`parentValue2`,....] 
        :returns: Loglikelihood of `fullAssignment` using `cpdLogMatrix`
        ''' 
        #compute the matrix index for the attribute values
        [indexRow,indexColumn] = self.attr.CPD.indexingCPD(fullAssignment)
        #update the loglik with the log prob of the instance that we have seen
        return self.attr.CPD.cpdLogMatrix[indexRow,indexColumn]
         
    def indexingCPD(self,currentRow):
        '''
        Returns the row and column indices for a full assignment to the attribute `attr`. `indexRow` is the
        index of the row of the cpd matrix that corresponds to the assignment of the 
        parent attributes. The parents attribute values are ordered the same way as in `attr.parents`.
        `indexColumn` is the index of the column that corresponds to the assignment of the attribute value
        itself.
        
        :arg currentRow: List containing a full assignment, [`attributeValue`,`parentValue1`,`parentValue2`,....]
        :returns: Tuple [`indexRow`,`indexColumn`]
        '''
        return [self.indexRow(currentRow[1:]),self.indexColumn(currentRow[0]) ]
     
    #@time_analysis    
    def indexRow(self,parentAssignment):
        '''
        See :meth:`.indexingCPD`
        '''
        
        index=0
        for i, mult, value in izip(count(),self.indexingMultiplier, parentAssignment):
            index += mult * self.attr.parents[i].indexingValue(value)                    
            
        return int(index)

    


    def conditionalDist(self,gbnV):
        '''
        Returns the conditional probability distribution of the `gbnV` given its parent values.

        .. todo::

            In this branch I bypass the :mod:`.aggregation` module and implement weighted expectation directly into this method. The `aggregation` needs to be adapted and improved, until then it is less messier to do the aggregation directly here.

        :arg gbnV: :class:`.GBN` instance
        :returns: A `1 x |attr.domain|` numpy.array probability distribution
        '''

        condProp = N.zeros( [1, gbnV.attr.cardinality] ) 

        

        #  a list of lists
        #  every sublist contains all gbnVs of a parent attribute.
        #  the list is in the correct order (according to gbnV.attr.parents)
        sparse_exist =  [ [gbnPa.value for gbnPa in gbnV.parents[dep.parent].values()]  for dep in gbnV.attr.dependenciesChild ]
        

        spase_iter = product(*sparse_exist)


        # logging.info([ ['%s = %s'%(gbnPa.ID,gbnPa.value) for gbnPa in gbnV.parents[dep.parent].values()]  for dep in gbnV.attr.dependenciesChild ])

        for paAss in spase_iter:

            i = self.indexRow(paAss)
            
            condProp += self.cpdMatrix[i,:] 

            # logging.info('paAss : %s\ndist : %s\nupdated condDist: %s'%(paAss,self.cpdMatrix[i,:] ,(condProp / condProp.sum())))

        
        return condProp / condProp.sum()
        

    
    def reverseIndexRow(self,index):
        '''
        Computes the parent assignment given an row index of `cpdMatrix`
        
        :arg index: Row index of `cpdMatrix`
        :returns: Parent assignment associated with `index`
        '''
        parentAssignment = [None for p in self.attr.parents]
        for i,m in enumerate(self.indexingMultiplier):
            parentAssignment[i] = self.attr.parents[i].domain[(index/m)] 
            index =  index % m
            
        return parentAssignment   
        
    
    def indexColumn(self,attrValue):
        '''
        See :meth:`.indexingCPD`
        '''
        return self.attr.indexingValue(attrValue)
        
    
    
    def computeLogDists(self):
        '''
        Calculates the log probability distribution `cpdLogMatrix` and cumulative log probability distribution `cumLogMatrix`
        '''
        self.cpdLogMatrix = N.log(self.cpdMatrix)
        self.computeCumulativeDist()
        self.cumLogMatrix = N.log(self.cumMatrix)        
        
    def computeCumulativeDist(self):
        '''
        Calculates the cumulative distribution of the tabular CPD
        by incrementally summing the columns
        '''
        
        # self.cumMatrix = self.cpdMatrix.copy()
        # 
        # for i in range(0,(self.cumMatrix.shape[1]-1)):
        #     self.cumMatrix[:,(i+1)] = self.cumMatrix[:,(i+1)] + self.cumMatrix[:,i]
        
        
        self.cumMatrix = N.atleast_2d(self.cpdMatrix).cumsum(axis=1)
        
        
    def __repr__(self):
                
        return 'TabularCPD, Dim=%s'%(self.cpdMatrixDim)
        
    def initCPD(self):
        '''
        Computes the number of possible parent assigments and the index multipliers needed
        to compute the row index of a given parent assignment, see :meth:`.indexingCPD`.            
        ''' 
        
        nparentsindex= len(self.attr.parents) #temp variable
        for i, pa in enumerate(self.attr.parents):
            #print "parent %s , cardinality %s"%(pa.name,pa.cardinality)
                        
            # we calculate the total number of all possible combinations of parent assignments
            self.parentAssignments *= pa.cardinality
            
            # the index serves to find the row that corresponds to a specific parents assignment
            for j in range(i+1,nparentsindex):
                #print 'i=%s,j=%s'%(i,j)
                self.indexingMultiplier[i] *= self.attr.parents[j].cardinality
                
        
    def save(self,relPath='./localdistributions'):
        """
        Saves `cpdMatrix` to disk using `numpy.save` and outputs the XML specification that can be added to the PRM specification.
        
        :arg relPath: Relative path to the local distribution files, starting from the directory where the model is instantiated from.
        """        
        fname = self.attr.name  
        if len(self.attr.parents)!=0:
            fname = '%s_%s'%(fname,''.join([pa.name for pa in self.attr.parents]))
        locDistPath = '%s/%s'%(relPath,fname)
        # logging.info('Saving CPDmatrix.npy and attrname.xml for %s to %s -> include reference in PRM xml'%(self.attr.name,locDistPath))
        N.save(locDistPath,self.cpdMatrix)
        locDistXML = "<?xml version='1.0' standalone='no' ?><LocalDistribution attribute='%s'><TabularCPD file='%s.npy'/></LocalDistribution>"%(self.attr.fullname,locDistPath)
        xmlFile = open('%s.xml'%(locDistPath), 'w')
        xmlFile.write(locDistXML)
        xmlFile.close()
        #print 'Tag for cpd in prm xml specification:\n%s'%("<LocalDistribution attribute='%s' file='%s.xml'/>"%(self.attr.name,locDistPath))
        logging.info("<LocalDistribution attribute='%s' file='%s.xml'/>"%(self.attr.fullname,locDistPath))
        
        
class CPDTree(CPD):
    """Future implementation for a CPD based on a decision tree. No need so far.
    """
    
    def __init__(self):
        pass        
    
