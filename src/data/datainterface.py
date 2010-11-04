"""
The core idea of the data interface is to separate the PRM model from the relational data soucre. An instance of :class:`.DataInterface` contains a collection of methods that are used by different algorithms (e.g. CPD learners, inference methods, EM algorithm). Another advantage of this approach is that the data is not required to be in a fixed database format. 
"""

'''
The singular DataInterface instance contains a collection of methods that are used
by different algorithms (e.g. CPD learners, EM algorithm, Inference). The description
of a function should give examples of algorithms that use that method. 

-At this point there is no error testing, e.g. the statements that will query 
the data are derived from the names of the entities/relationships etc in the
prm. In the future one could envision some sort of mapping that is also passed 
on as part of the specification of a prm


There will be different ways a prm (e.g. a learner or inference class), can
access the data. For large datasets that have to be queried multiple times
, there will be an MySQL interface. A similar interface for SQLite will be 
implemented first. SQLite allows the data to be loaded into the memory.
Then it can be accessed faster in the usual way. Of course both MySQL and
SQLite use the SQL language interchangeably.
  
'''





''' 
Analytics
    by adding the decorator @time_analysis before any 
    function we collect runtime information
'''
from analytics.performance import time_analysis

    
    
def datasetinterfaceFactory(path,ditype):
    '''
    Creates a connection to a database. There are possibly multiple dataset connections to do crossvalidation.
    
    :arg path: The path to the database
    :arg ditype: Type of database, e.g. `SQLite`
    :returns: A :class:`.DataSetInterface` instance
    '''
    print '\tDataSetInterface Factory: create %s connection to %s'%(ditype,path.split('/')[-1])
    
    
    if ditype == 'SQLite':
        from data.sqliteinterface import SQLiteDI
        return SQLiteDI( path)
    elif ditype == 'MySQL':
        raise Exception("MySQL not yet implemented")
    elif ditype == 'XML':
        raise Exception("XML not yet implemented")
    else:
        raise Exception("unknown data interface type")
    


class DataSetInterface:
    '''
    An instance of the class connects a PRM with the relational data base that it models. This is an abstract class, sublclasses have to implement the required methdos for different database systems. E.g. :class:`data.sqliteinterface.SQLiteDI` is for SQLite.
    
    There data is queried by the parameter learning algorithm, e.g. :class:`learners.cpdlearners`, as well as by the inference methods; the inference :class:`Engine` is unrolling the Ground Bayesian Network.
    '''
    
    def __init__(self,dsiType):
        '''
        Shouldn't be executed since the class is abstract.
        '''  
        self.dsiType = dsiType
        
    
    def __repr__(self):
        ''' String representation of the data interface'''
        raise Exception("method __repr__() is not implemented in the DataSetInterface")
    
        
    

        
        
class DataInterface():
    '''
    A `DataInterface` instance connects a ProbRem instance to a relational data source.
    '''
    def __init__(self,name,diType,DSI):
        '''
        The DataSet instance will be instantiated by the :class:`.DataInterfaceParser`
        '''
        self.name = name
        
        #Type of Dataset (crossvalidation or testtraining)
        self.diType = diType
        
        
        self.DSI = DSI
        """List that contains all :class:`~data.datainterface.DataSetInterface` instances that connect to the data
        """
        
        self.trainingSets = {}
        """Dictionary that maps a crossvalidation test set (one `DataSetInterface` in `self.DSI`) with the corresponding training set (all other `DataSetInterfaces` in `self.DSI`)"""
        
        self.computeTrainingSets()
        
    
    def configure(self,prm):
        '''
        A method that allows us to configure a dataset interface based on information from the instantiated PRM. 
        '''
        
        # When dealing with aggregation, we want to create VIEWS to facilitate the sql queries.
        # If a dependency has a 1:n or m:n relationship, then aggregation is required.

        # print "\tConfiguring DataInterface '%s' with PRM '%s'"%(self.name,prm.name)
        

        # View currently disabled as we don't use them
        # 
        # for dep in prm.dependencies.values():
        #     if dep.aggregator is not None:
        #         for dsi in self.DSI:
        #             print '\t Creating VIEW for %s'%dep.name
        #             dsi.createView(dep)
        
        
    def computeTrainingSets(self):
        ''' 
        Returns a dictionary mapping a crossvalidation test set with the corresponding training set { datasetinstance : [datasetinstance1,datasetinstance2,....]}. Every :class:`!DataSetInterface` in `self.DSI` is a key in `self.trainingSets`, the value is a list of all other :class:`!DataSetInterface` instances in `self.DSI`
        '''
        
        #filter(def f(x):return x in self.DSI , )
        
        for dsi in self.DSI:
            ts = []
            for tdsi in self.DSI:
                if tdsi!=dsi:
                    ts.append(tdsi)            
            self.trainingSets[dsi]=ts
                            
