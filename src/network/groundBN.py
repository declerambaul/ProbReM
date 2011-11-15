"""
The Ground Bayes Network (GBN) in ProbReM is the smallest subset of data that is required to answer a specific query. While the PRM uses a first-order representation of the world, the inference process needs a propositional represenation of the data. The :mod:`network.groundBN` module implements an efficient data structure for that purpose.

"""
from analytics.performance import time_analysis
from network.vertices import GBNvertex,ReferenceVertex,computeRefID



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

        return ID

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

        return ID
            
            
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
            
            return ID
        return False
        '''
        else:
            ?Gather statistics about how many nodes were added reduntantly 
        '''    
       
       
    def addReferenceVertex(self,gbnV,dependency):
        '''Adds a :class:`.ReferenceVertex` to the ground Bayesian network. 

        For now, the reference attribute (all exist attributes) are assumed to be sampling nodes (i.e. not in the evidence nor in the event variables)

        '''        
        ID = computeRefID(gbnV)

        if ID not in self:

            self[ID] = ReferenceVertex(ID=ID, gbnV=gbnV,dep=dependency)

            attr = self[ID].attr
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
            


            # initialize reference

            # add initial edges



            return ID
        
        #nothing added
        return False
     
        
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

    def __repr__(self):
        ''' 
        String representation of the statistics of the current Graph
        '''
        rep = '-- Ground Bayesian Network --\n'

        def prettyStat(gbndict):
            '''Returns a string representation of the `gbndict` dictionary
            '''
            s = ''
            for attr,gbnvs in gbndict.items():
                s += '\t%s (%s)\n'%(attr.fullname,len(gbnvs))
            return s[:-1]

        
        rep += 'All      : %s vertices\n%s\n'%(len(self),prettyStat(self.allByAttribute))
        rep += 'Sampling : %s vertices\n%s\n'%(len(self.samplingVertices),prettyStat(self.samplingVerticesByAttribute))            


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
        This allows us to retrieve the required data in one call to the data interface.
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
    
