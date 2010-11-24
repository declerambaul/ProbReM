'''
The parameters of a PRM model are the conditional probability distributions (CPDs or `local distributions`), they are learned using the module :mod:`!learners.cpdlearners`.

This module contains classes that are used to learn conditional probability distributions (CPDs) for attributes. 
The basic CPD class is :class:`prm.localdistributions.CPD` which can be implemented for different CPD representations.
:class:`prm.localdistributions.CPDTabular` stores the CPD as a matrix, whereas :class:`prm.localdistributions.CPDTree` 
stores the CPD in a decision tree (not implemented yet).

'''

from analytics.performance import time_analysis

from prm.localdistribution import CPDTabular

#from pylab import *
import numpy as N

class CPDLearner():
    '''
    Abstract class that is used to learn the conditional probability distributions for 
    a PRM using the data linked in the data interface.
    '''
    def __init__(self):        
        ''' 
        Creates CPDLearner. It now has to be configured using the self.configure() method.
        '''
        self.prmToLearn = None 
        self.di = None
    
    def __repr__(self):            
        return "%s - PRM %s - DI %s"%(self.__class__.__name__ ,self.prmToLearn.name,self.di.name)
        
    def configure(self,prmToLearn,di,learnCPDs=False,saveCPDs=False):
        '''
        Tells the CPD learner which PRM instance and which data interface it should use.
        '''
        self.prmToLearn = prmToLearn 
        self.di = di # data interface  
        
        if learnCPDs:
            #self.learnCPDsCount(saveDistributions=saveCPDs,forceLearning=True)
            self.learnCPDsFull(saveDistributions=saveCPDs,forceLearning=True)

    def learnCPDsFull(self):
        raise Exception("learnCPD not implemented in the CPDLearner instance")
    
    def learnCPDsCount(self):
        raise Exception("learnCPD not implemented in the CPDLearner instance")
    
    
class CPDTabularLearner(CPDLearner):
    '''
    The CPDTabularLearner learns the local distributions for all probabilistic attributes and stores them 
    in tabular form :class:`prm.localdistributions.CPDTabular`. It loads all the necessary data for each attribute 
    in one query using the data interface.
    '''
    def __init__(self):
        
        CPDLearner.__init__(self)                                                                         
        
        
    #@time_analysis
    def learnCPDsCount(self,saveDistributions=False,forceLearning=False):
        '''
        Learns the conditional probability distributions for all probabilistic attributes
        by counting the occurences on the data side. If the data interface connects
        to a SQL based database this can easily be done using the `COUNT` statement. 
        The data is retrieved by calling the data interface method :meth:`data.sqliteinterface.loadCountCPDdata`
        
        :arg saveDistributions: If `True`, saves the learned CPDs to disk and prints the XML line that needs to be added to the PRM specification to the standard output
        :arg forceLearning: If `True`, the CPDs are learned even if there are distributions that could be loaded from disk
        '''
        #iterate over all attributes
        for attr in self.prmToLearn.attributes.values():                        

            if attr.probabilistic: #only learn probabilistic attributes
            
                if attr.CPD != None and not forceLearning:
                    print "... CPD for attribute '%s' already loaded"%(attr.name)
                    
                else: #only learn attributes that don't have a CPD yet (it could also be specified in prm)

                    print "... Learning CPD for attribute '%s'"%(attr.fullname)
                
                    #create CPD instance for attribute
                    attr.CPD = CPDTabular(attr)
                    #we count all occurrences of the individual parent assignments
                    counter = N.zeros((attr.CPD.cpdMatrix.shape[0],1))
                
                
                    '''
                    We learn the distributions over all the trainig sets (no cross validation)
                    '''
                    for dsi in self.di.DSI:
                    
                
                        #load the full data for attribute
                        #dsi.loadFullCPDdata(attr)

                        #or load the aggregated data for attribute
                        dsi.loadCountCPDdata(attr)
                                                                            

                        for i,currentRow in enumerate(dsi.resultSet()):
                            
                            #keeping track of the index for the attribute
                            npa = attr.CPD.cpdMatrix.shape[0]
                            attrIndex = i / npa
                            parentIndex = i % npa
                            
                            '''                            
                            We handle the current row
                            '''
                            #count the attribute assignment
                            attr.CPD.cpdMatrix[parentIndex,attrIndex] = currentRow[0]
                            #count the parent assignment
                            counter[parentIndex] += currentRow[0]                            
    
                
                    #add fake counts
                    #TODO
            
                    #calculate probabilities
                    attr.CPD.cpdMatrix = attr.CPD.cpdMatrix / counter 
                
                    #compute the cumulative distribution
                    attr.CPD.computeCumulativeDist()
                    attr.CPD.computeLogDists()
                
                    #print attr.CPD.cpdMatrix                    
                    #print attr.CPD.cpdMatrix.sum(axis=1)
                
                
                if saveDistributions:
                    ''' Finally we can save the distributions to file if desired '''    
                    attr.CDP.save()
    
    #@time_analysis
    def learnCPDsFull(self,saveDistributions=False,forceLearning=False):
        '''
        Learns the conditional probability distributions for all probabilistic attributes
        by iterating over a big table counting the occurences on the way. If the data interface 
        connects to a SQL based database, the result set is a big table in the form
        [valAttr, valPa1, valPa2, etc.]. 
        The data is retrieved by calling the data interface method :meth:`data.sqliteinterface.loadFullCPDdata`
        
        :arg saveDistributions: If `True`, saves the learned CPDs to disk and prints the XML line that needs to be added to the PRM specification to the standard output        
        :arg forceLearning: If `True`, the CPDs are learned even if there are distributions that could be loaded from disk
        '''
        print "Learning CPD for attributes '%s'"%(','.join([attr.fullname for attr in self.prmToLearn.attributes.values() if attr.probabilistic]))
        #iterate over all attributes
        for attr in self.prmToLearn.attributes.values():                        

            if attr.probabilistic: #only learn probabilistic attributes
                
                if attr.CPD != None and not forceLearning:
                    print "... CPD for attribute '%s' already loaded"%(attr.name)
                else: #only learn attributes that don't have a CPD yet (it could also be specified in prm)
                    
                    #print "... Learning CPD for attribute '%s'"%(attr.fullname)
                    
                    #create CPD instance for attribute
                    attr.CPD = CPDTabular(attr)
                    #we count all occurrences of the individual parent assignments
                    counter = N.zeros((attr.CPD.cpdMatrix.shape[0],1))
                    
                    
                    '''
                    We learn the distributions over all the trainig sets (no cross validation)
                    '''
                    for dsi in self.di.DSI:
                        
                    
                        #load the full data for attribute
                        dsi.loadFullCPDdata(attr)

                        #or load the aggregated data for attribute
                        #dsi.loadFullAggCPDdata(attr)
                        
                                                                                
                       
                        for currentRow in dsi.resultSet():                                                                                                                                

                            '''                            
                            We handle the current row
                            '''                        
                            
                            #compute the matrix index for the attribute values
                            [indexRow,indexColumn] = attr.CPD.indexingCPD(currentRow)
                            #count the attribute assignment
                            attr.CPD.cpdMatrix[indexRow,indexColumn] += 1
                            #count the parent assignment
                            counter[indexRow] +=1
                        
                    
                         
                    
                    
                    #add fake counts
                    nF = 1
                    attr.CPD.cpdMatrix += nF
                    counter += attr.CPD.cpdMatrix.shape[1]*nF
                
                    #calculate probabilities
                    attr.CPD.cpdMatrix = attr.CPD.cpdMatrix / counter 
                    
                    #compute the cumulative distribution
                    attr.CPD.computeCumulativeDist()
                    attr.CPD.computeLogDists()
                    
                    #print attr.CPD.cpdMatrix                    
                    #print attr.CPD.cpdMatrix.sum(axis=1)
                    
                    
                if saveDistributions:
                    ''' Finally we can save the distributions to file if desired '''    
                    attr.CPD.save()
                    

    def loglikelihood(self):
        '''
        Computes the log likelihood for the learned CPDs. As aggregation is possibly required, it uses the method
        :meth:`data.sqliteinterface.loadFullAggCPDdata` to retrieve the data.
        
        '''
        
        loglik = 0
        
        for attr in self.prmToLearn.attributes.values():                        

            if attr.probabilistic: 
                
                for dsi in self.di.DSI:
                    
                
                    #load the full data for attribute
                    #dsi.loadFullCPDdata(attr)

                    #or load the aggregated data for attribute
                    dsi.loadFullAggCPDdata(attr)
                    
                    for currentRow in dsi.resultSet():  
                        '''                            
                        We handle the current row
                        '''
                        #compute the matrix index for the attribute values
                        [indexRow,indexColumn] = attr.CPD.indexingCPD(currentRow)
                        #update the loglik with the log prob of the instance that we have seen
                        loglik += attr.CPD.cpdLogMatrix[indexRow,indexColumn] 
                        
                    
        return loglik
    
    

class CPDTreeLearner(CPDLearner):    
    pass

