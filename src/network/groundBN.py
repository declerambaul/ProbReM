
from analytics.performance import time_analysis



def computeID(attr,obj):
    """A simple helper function that computes a unique ID from an `attr` and `obj`, the primary key of the attribute object which is part of the GBN.
    
    :arg attr: Subclass of :mod:`prm.attribute.Attribute`
    :arg obj: List of int values
    :returns: A unique string ID for the attribute object
    """
    return '%s.%s'%(attr.ID,'.'.join([str(i) for i in obj]))


class GBNvertex():
    '''
    A `GBNvertex` represents a vertex in the Ground Bayes net. It is a variable in the GBN representing an attribute object whose CPD is distributed according to the CPD of the attribute class. E.g. all attribute objects of the same attribute class share the same CPD.     
    A `GBNvertex` instance can take on a value from the domain of the associated attribute.
    
    A node is associated with a specific attribute object :math:`x \in \sigma_{ER}`. 
    We use sets to identify an obj, where the set contains a value
    of for each primary key in `self.pk` of `attr.erClass`
    
    * a GBNvertex for `rating` would have self.obj = (x,y) where x=`User.user_id` and y=`Item.item_id`
    * a GBNvertex for `gender` would have self.obj = (x) where x=`User.user_id`
    '''
    def __init__(self,attr,obj,ID=None,event=False,fixed=False,value=None,deterministic=False,aggregation=None): 
        
        #
        self.attr = attr
        """
        The associated attribute class
        """
        self.obj = obj
        """
        An identifier for the vertex
        """
        # It could be computed at the time of instantiation, but usually is already computed to check whether the vertex is already present in the graph
        if ID is None:
            self.ID = self.attr.ID+'.'+'.'.join([str(i) for i in self.obj])
        else:
            self.ID = ID 
        
        self.value = value
        """
        Current value, must be in the domain of `attr`
        """
        self.fixed = fixed
        """
        Boolean. If the value is fixed the vertex is part of the evidence
        """
        self.event = event
        """
        Boolean. If True, we are interested in the posterior distribution of the vertex.
        """
        self.parentAss = []
        """
        The parent assignment of the parents of this node. It can be updated using :meth:`parentAssignments`
        """        
        self.parents = {}
        """
        The dictionary of parents attribute objects {key=`parent.attribute` : val=[`list of gbnVertices`]}. `parent.attribute` is of type :class:`~prm.attribute.Attribute` and the `gbnVertices` of type :class:`GBNvertex`
        """
        #init the parent dict and the parentAss
        for dep in self.attr.dependenciesChild:
            self.parents[dep.parent] = {}
            self.parentAss.append(None)
            
        self.children = {}
        """
        The dictionary of children attribute objects {key=`child.attribute` : val=[`list of gbnVertices`]}. `child.attribute` is of type :class:`~prm.attribute.Attribute` and the `gbnVertices` of type :class:`GBNvertex`
        """
        # init the children dict and the parentAss
        for dep in self.attr.dependenciesParent:
            self.children[dep.child] = {}
        


    def addParent(self,parentVertex):
        ''' 
        Adds the `parentVertex` to the list of parent vertices associated with the parent 
        vertex attribute. It adds the corresponding information to the children dictionary 
        of the parent node.
        
        :arg parentVertex: :class:`GBNvertex`
        '''
        if parentVertex.ID not in self.parents[parentVertex.attr]:
            self.parents[parentVertex.attr][parentVertex.ID] = parentVertex
        
        #adds child information to parent node
        if self not in parentVertex.children[self.attr]:
            parentVertex.children[self.attr][self.ID] = self
            

      
    def hasParents(self,paAttr):
        '''
        Returns True if the number of parents for the attribute `paAttr` is not zero.
        If paAttr is not the parent of self.attr, a key exception will be raised.
        
        :arg paAttr: :class:`~prm.attribute.Attribute`
        '''        
        if len(self.parents[paAttr])>0:
            return True
        else:
            return False
       
    
    def logLikelihood(self):
        '''
        Returns the loglikelihood of the value of the GBN vertex
        '''
        fullAssignment = [self.value]
        #compute parent assignments
        self.parentAssignments()
        
        fullAssignment.extend(self.parentAss)

        return self.attr.CPD.logLikelihood(fullAssignment)
    
           
    def sample(self):
        '''
        Samples a new value for that gbn vertex. Warning: `self.value` will be overwritten even if `self.fixed=True`. We opt of performance and trust our implementation.
        '''
        self.parentAssignments()
        self.value = self.attr.CPD.sample(self.parentAss)
        
    

    def parentAssignments(self):
        '''
        Computes the values of the parents of that GBN vertex (using aggregation if necessary). Note that since there 
        is an `GBNVertex` instance for every node in the GBN, the parent assignments are
        stored in the instance variable self.parentAss. In the case of the local distribution
        instance of an attribute, this is not the case as the distribution is shared among 
        many attribute objects.
        '''
        for i,dep in enumerate(self.attr.dependenciesChild):
            if dep.aggregator is None:
                #there should be only one parent value in this case
                paVal = self.parents[dep.parent].values()   
                
                # Just for debugging, when the model is proper that should never happen: comment out for performance
                # if len(paVal) != 1:    
                #     raise Exception('ERROR, no aggregation for %s but %s has %s parents'%(dep,self,len(paVal)))
                  
                self.parentAss[i] = paVal[0].value           
            else:
                #we perform a runtime aggregation
                paVals = [gbnV.value for gbnV in self.parents[dep.parent].values()]
                agg_func = dep.aggregator('runtime')
                                    
                paAgg = agg_func(paVals)                
                
                self.parentAss[i] = paAgg
                
            
    def outdegree(self,attr=None):
        ''' 
        Returns the number of parents for attr.
        If `attr==None` the total number of parents is returned.
        
        :arg attr: :class:`~prm.attribute.Attribute`
        '''
        if attr is None:
            return sum([len(vs) for (a,vs) in self.parents.items()])
        else:
            return len(self.parents[attr])

    def indegree(self,attr=None):
        ''' 
        Returns the number of parents for attr.
        If `attr==None` the total number of parents is returned.
        
        :arg attr: :class:`~prm.attribute.Attribute`
        '''
        if attr is None:
            return sum([len(vs) for (a,vs) in self.children.items()])
        else:
            return len(self.children[attr])


    def __repr__(self):
        painfo = 'None'
        if len(self.parents)>0:
            painfo = ' | '.join(['%s(%s)'%(a.name,len(vs)) for (a,vs) in self.parents.items()]) 
                       
        if self.fixed:   #['%s'%(v.ID) for v in self.parents]
            r = '%s (Evidence,Value=%s,#Pa=[%s])'%(self.ID,self.value,painfo)
        elif self.event:
            r = '%s (Event,Value=%s,#Pa:[%s])'%(self.ID,self.value,painfo)
        else:
            r = '%s (Value=%s,#Pa=[%s])'%(self.ID,self.value,painfo)
        return r
        
        
class GBNGraph(dict):
    '''
    A `GBNGraph` is a dictionary that contains a set of vertices of type :class:`GBNvertex`.
    
    The `GBNGraph` instance  itself is a dictionary which is used to store vertices {key=vertex_id : value= :class:`GBNvertex`}. There are also various different dictionaries of all `GBNvertex` objects that allow fast retrieval of sets of GBN vertices.
    '''
    def __init__(self):
        '''
        init
        '''
        self.allByAttribute = {}
        """
        A dicitonary that groups all `GBNvertex` instances according to their attribute class, e.g.  {key=:class:`Attribute` : value=[ list of :class:`!GBNvertex` ]}
        """
        self.samplingVertices = {}
        """
        A dicitonary that groups all sampling `GBNvertex` instances (event & latent vertices), e.g.  {key=vertex_id : value= :class:`!GBNvertex`}
        """
        self.eventVertices = {}
        """
        A dicitonary that groups all event `GBNvertex` instances according to their attribute class, e.g.  {key=vertex_id : value= :class:`!GBNvertex`}
        """
        self.samplingVerticesByAttribute = {}
        """
        A dicitonary that groups all sampling `GBNvertex` instances (event & latent vertices) according to their attribute class, e.g.  {key=:class:`Attribute` : value=[ list of :class:`!GBNvertex` ]}
        """
                
    
    def addEvidenceVertex(self,ID,attr,obj,value):
        """
        Instantiates a new evidence :class:`!GBNvertex` and updates the corresponding GBN data structures.
        
        :arg ID: Unique ID
        :arg attr: :class:`Attribute`
        :arg obj: Primary Key of attribute object
        :arg value: Value of vertex
        """

        self[ID] = GBNvertex(ID=ID,attr=attr,obj=obj,fixed=True,value=value)          
        
        if attr in self.allByAttribute:
            self.allByAttribute[attr].append(self[ID])                
        else:
            self.allByAttribute[attr] = []
            self.allByAttribute[attr].append(self[ID])

    def addSamplingVertex(self,ID,attr,obj):
        """
        Instantiates a new sampling :class:`!GBNvertex` and updates the corresponding GBN data structures.
        
        :arg ID: Unique ID
        :arg attr: :class:`Attribute`
        :arg obj: Primary Key of attribute object
        """
        
    
        self[ID] = GBNvertex(ID=ID,attr=attr,obj=obj,fixed=False)     
        
        self.samplingVertices[ID] = self[ID]
        
        if attr in self.samplingVerticesByAttribute:
            self.samplingVerticesByAttribute[attr].append(self[ID])                
        else:
            self.samplingVerticesByAttribute[attr] = []
            self.samplingVerticesByAttribute[attr].append(self[ID])     
        
        if attr in self.allByAttribute:
            self.allByAttribute[attr].append(self[ID])                
        else:
            self.allByAttribute[attr] = []
            self.allByAttribute[attr].append(self[ID])
            
            
    def addVertex(self,ID,attr,obj, **args):
        '''
        General method to add a vertex to the graph. 
        
        '''
        """
        General method to add a vertex to the graph. Note that the node is only instantiated (and added) if `ID` is not in the graph already.
        If not, instantiates a new :class:`!GBNvertex` and updates the corresponding GBN data structures.
        
        :arg ID: Unique ID
        :arg attr: :class:`Attribute`
        :arg obj: Primary Key of attribute object
        :arg **args: Dictionary of other parameters
        """
                
        if ID not in self:            
            self[ID] = GBNvertex(ID=ID,attr=attr,obj=obj,**args)
            #print 'Added %s(E=%s) to GBN'%(ID,self[ID].fixed)
            
            #also add references to the helper data structures
            if not self[ID].fixed:
                self.samplingVertices[ID] = self[ID]
                if attr in self.samplingVerticesByAttribute:
                    self.samplingVerticesByAttribute[attr].append(self[ID])                
                else:
                    self.samplingVerticesByAttribute[attr] = []
                    self.samplingVerticesByAttribute[attr].append(self[ID])    
                
                            
            if attr in self.allByAttribute:
                self.allByAttribute[attr].append(self[ID])                
            else:
                self.allByAttribute[attr] = []
                self.allByAttribute[attr].append(self[ID])    
            
            return True
        return False
        '''
        else:
            ?Gather statistics about how many nodes were added reduntantly 
        '''    
        
        
    def __missing__(self,key):
        '''
        Called if we try to access a vertex that isn't in the graph.
        '''
        return None
        

    def logLikelihood(self):
        '''
        Returns the loglikelihood of the `GBNGraph`
        '''
        loglik = 0
        for gbnV in self.values():
            
            loglik += gbnV.logLikelihood()
            
        return loglik
    
    def statistics(self):    
        ''' 
        Calculates a number statistics of the graph.
        
        * Number of vertices in graph
        * Number of sampling vertices
        * Average In-degree
        * Average Out-degree
        '''
        stats={}

        #stats['Size of Inference Set'] = len(self.eventNodes)
        if len(self) == 0:
            stats['Number of vertices in graph'] = len(self)
            return stats

        indegree = 0
        outdegree = 0
        samplingVs = 0
        for vertex in self.values():
            indegree += vertex.indegree()
            outdegree += vertex.outdegree()  
            if not vertex.fixed:
                samplingVs = samplingVs + 1

        stats['Number of vertices in graph'] = len(self)
        stats['Number of sampling vertices'] = samplingVs
        stats['Average In-degree'] = 1.0*indegree/len(self)
        stats['Average Out-degree'] = 1.0*outdegree/len(self)

        return stats

    def __repr__(self):
        ''' 
        String representation of the statistics of the current Graph
        '''
        stats = self.statistics()
        rep = 'Graph Statistics:\n'
        for (stat,val) in stats.items():
            rep += '\t%s = %s\n'%(stat,val)            
        return rep[:-1] #don't return last '\n'
        
        
class GBNqueue(dict):
    '''
    A queue that keeps track of vertices that need to be processed when
    constructing the Ground Bayesian network.
    
    This class is also a dictionary as the information is stored in groups
    that correspond to sets of vertices that share the same local distribution
    (= the same attribute). 
    
    { key=:class:`Attribute` : value=[ list of :class:`!GBNvertex` ] }
    '''
    def __init__(self):
        '''
        Init
        '''
        
    def isEmpty(self):
        if len(self)==0:
            return True
        else:
            return False
        
    def pop(self):
        ''' 
        Return a set of GBNvertex instances of the same attribute :math:`A \in A(X)`. 
        This allows us to retrieve the required data in one call to the DataInterface.
        We choose an attribute, remove the
        key from the dictionary and return the associated list.
        
        :returns: List of :class:`!GBNvertex`
        '''
        return self.popitem()
        
    

    def push(self, gbnVertex):
        ''' 
        If another :class:`!GBNvertex` is pushed onto the stack, it is added to the list
        associated with the `gbnVertex.attr`
        
        :arg gbnVertex: :class:`GBNvertex`
        '''
        #print 'Adding %s to Queue'%(gbnVertex.ID)
        self[gbnVertex.attr].append(gbnVertex)
    
    def __missing__(self,key):
        '''
        In case the key - an attribute instance - is not in the dictionary we add it
        with an empty list of vertices.
        '''
        self[key] = []
        return self[key]
    
