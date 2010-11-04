'''
All attributes need to implement the class :class:`.Attribute` that defines a set of methods that need to implemented. Currently ProbReM supports a set of discrete variables, some attribute types are not probablistic and serve another purpose, e.g. as a foreign key.

* Binary attributes :class:`.BinaryAttribute`
* Integer attributes :class:`.IntegerAttribute`
* Enumerated attributes :class:`.EnumeratedAttribute`
* Not probabilistic attributes :class:`.NotProbabilisticAttribute`
* Foreign attributes :class:`.ForeignAttribute`

All attributes are instantiated by calling the :meth:`~prm.attribute.attributeFactory`.

.. inheritance-diagram:: prm.attribute

'''

 
def attributeFactory(name, er, type, attrDef, probabilistic=True, hidden=False ):
    
      
    '''
    can't put functions in the value
    attribute = {'Binary' : BinaryAttribute( name, er, hidden=False) ,
                'Enumerated' : EnumeratedAttribute( name, er, attrValues=attrDef, hidden=False),
                'Integer' : IntegerAttribute( name, er, attrRange=attrDef, hidden=False)}
    return attribute[type]
    '''
    #print "attributeFactory():", name, er, type, attrDef, hidden, probabilistic  
    
    if type == 'Binary':
        return BinaryAttribute( name, er, hidden=False)
    elif type == 'Enumerated':
        return EnumeratedAttribute( name, er, attrValues=attrDef, hidden=False)
    elif type == 'Integer':    
        return IntegerAttribute( name, er, attrRange=attrDef, hidden=False)
    elif type == 'NotProbabilistic':   
        return NotProbabilisticAttribute( name, er )
    else:
        raise Exception("unknown Attribute type")



class Attribute():
    '''
    An 'abstract' class that defines an attribute (variable) of an entity or relationship class.
    '''
    def __init__(self, name, erClass, hidden=False):
        '''
        Constructs an Attribute class
        '''
        self.name = name
        """The name of the attribute has to be unique among the attributes of the same class, e.g. two attributes in different entities could have the same `name`.
        """
    
        self.erClass = erClass
        """
        Every attribute is attached to an entity or relationship class.
        `erClass` = Entity or Relationship Object
        """
        
        self.ID = self.fullname
        """
        Every attribute has a unique identifier that can be used when hashing.
        At this point the fullname is used. We could also think of some numerical
        value derived form the name for performance.
        """
        
        self.cardinality = None
        """ 
        The cardinality is the size of the domain.
        This value has to be assigned by the specific attribute class which
        is being instantiated.
        """     
           
        self.domain = None
        """
        The domain is a list of all possible values the attribute can take.
        This value has to be assigned by the specific attribute class which
        is being instantiated. 
        """
                
        self.indexing = {}
        """
        The dictionary `indexing` serves to access the index of the domain values. `indexing` 
        stores { key= domain value : value= index of domain value}. 
        
        * `domain` = [4,5,6] -> `indexing` = {4:0,5:1,6:2}
        * `domain` = ['A','B','0'] -> `indexing` = {'A':0,'B':1,'C':2}        
        """
        
        self.CPD = None
        """
        The Conditional Probability Distribution of an attribute of type :class:'.CPD'
        """
        
        
        self.parents = []
        """
        A list of the parents, all of type :class:`.Attribute`
        """
        
        self.dependenciesChild = []
        """
        A list of the :class:`.Dependency` instances that the given attribute is a child of
        """
        
        self.dependenciesParent = []
        """
        A list of the :class:`.Dependency` that the given attribute is a parent of
        """
        
        self.hidden=hidden
        """
        Boolean. If `True` then there is not a corresponding data field (latent variable)
        """
    
    def indexingValue(self,value):
        '''
        Returns the index of the `domain` list given an attribute `value`.
        This is a function because different
        attribute classes can compute this index differently. 
        
        :arg value: Value that is in the `domain`
        '''
        raise Exception("indexing not implemented for attribute class")  
    
    @property    
    def type(self):
        '''
        The type of an attribute, e.g. `BinaryAttribute`, `IntegerAttribute`, 
        `EnumeratedAttribute`, `NotProbabilisticAttribute`
        '''
        return self.__class__.__name__  
        
    @property    
    def probabilistic(self):
        '''
        Returns True if the attribute is probabilstic. Overwrite this function 
        in all non probabilistic attributes, e.g. :class:`!.NotProbabilisticAttribute` or :class:`!.ForeignAttribute`
        '''
        return True

    @property    
    def fullname(self):
        '''
        The full name an attribute is either 'Entity_name.Attribute_name' 
        or 'Relationship_name.Attribute_name'
        '''
        return '%s.%s'%(self.erClass.name,self.name)  

    @property    
    def hasParents(self):
        '''
        Returns True if the number of parents is not zero
        '''
        if len(self.parents)>0:
            return True
        else:
            return False
        

class BinaryAttribute(Attribute):
    '''
    A Binary Attribute can only take on two different values
    '''
    def __init__(self, name, er, hidden=False):
        '''
        Constructs an BinaryVariable class that can take the value True or False
        '''        
        Attribute.__init__(self, name, er)     
        
        # set domain and cardinality
        self.domain = (0,1)
        self.cardinality = len(self.domain)

        # compute the indexing dictionary
        for i,v in enumerate(self.domain):
            self.indexing[v] = i
            
    def indexingValue(self,value):
        '''
        Returns the index of the `domain` list given an attribute `value`.
        For a binary value it is faster to just return the value since it corresponds
        to the index.
        
        :arg value: `0` or `1`
        '''
        return value
        #return self.indexing[value]
        
    def __repr__(self):
        '''
        Returns a string representation of the instance 
        ''' 
        return "Binary Attribute (%s , Hidden=%s, CPD=%s)"%(self.name,self.hidden,self.CPD)        
        

class IntegerAttribute(Attribute):
    '''
    A Integer Attribute can take values in a certain interval
    '''
    def __init__(self, name, er, attrRange, hidden=False):
        '''
        Constructs an BinaryVariable class that can take the value True or False
        '''        
        Attribute.__init__(self, name, er)     
        
        
        self.attrRange = [int(v.strip()) for v in attrRange.strip('[]').split(',')]
        
        self.domain = tuple(range(self.attrRange[0],self.attrRange[1]+1))
        """List of integer values
        """
        self.cardinality = len(self.domain)
        """Size of `domain`
        """
        
        # compute the indexing dictionary
        for i,v in enumerate(self.domain):
            self.indexing[v] = i
        
    def indexingValue(self,value):
        '''
        Returns the index of the `domain` list given an attribute `value`.
        
        Since the domain of an Integer Attribute is an interval, it is faster to 
        just subtract. 
        
        :arg value: Int value that is in the `domain`
        '''
        #return value-self.domain[0]        
        return self.indexing[int(value)]

              
    def __repr__(self):
        '''
        Returns a string representation of the instance 
        ''' 
        return "Integer Attribute (%s, [%s,%s] , Hidden=%s, CPD=%s)"%(self.name,self.attrRange[0],self.attrRange[1],self.hidden,self.CPD)        
       
   
class EnumeratedAttribute(Attribute):
    '''
    A Enumerated Attribute can take values stored in `domain`. Note that there are no
    constraints on what is passed in attrValues. In case of working with strings, the 
    performance will be lower because a lot of string operations will have to be executed.
    '''
    def __init__(self, name, er, attrValues, hidden=False):
        '''
        Constructs an BinaryVariable class that can take the value True or False
        '''        
        Attribute.__init__(self, name, er)     
        
        
        self.domain = tuple(int(v.strip()) for v in attrValues.strip('[]').split(','))
        """List of domain values
        """
        self.cardinality = len(self.domain)
        """Size of `domain`
        """
        
        ''' compute the indexing dictionary '''
        for i,v in enumerate(self.domain):
            self.indexing[v] = i 
    
    def indexingValue(self,value):
        '''
        Returns the index of the `domain` list given an attribute `value`.
                
        :arg value: Value that is in the `domain`
        '''        
        return self.indexing[int(value)]
    
                
    def __repr__(self):
        '''
        Returns a string representation of the instance 
        ''' 
        return "Enumerated Attribute (%s, %s , Hidden=%s, CPD=%s)"%(self.name, self.domain,self.hidden,self.CPD)        
 
 
class NotProbabilisticAttribute(Attribute):
    '''
    An Attribute that is not probabilistic, which means that it will not have a local distribution 
    and that it can't be part of any probabilistic dependency. It is required for `slotchains` that use the
    non probabilistic primary keys.
    '''
    def __init__(self, name, er, hidden=False):
        '''
        Constructs an Not Probabilistic Attribute
        '''        
        Attribute.__init__(self, name, er)              
    
    @property
    def probabilistic(self):
        ''' Overwritten from Attribute class, always return `False` 
        '''
        return False
        
    def __repr__(self):
        '''
        Returns a string representation of the instance 
        ''' 
        return "Not Probabilistic Attribute (%s)"%(self.name)   

class ForeignAttribute(Attribute):
    '''
    An Foreign Attribute figures as part of the primary key of a relationship class.
    The foreign attribute points to the primary key of an entity class which is stored
    in `target`. 
    '''
    def __init__(self, name, target, er, hidden=False):
        '''
        Constructs an Foreign Attribute
        '''        
        self.target = target
        """The `target` is an attribute of an entity class that the
        relationship class the forgein attribute is part of. Often this is the 
        primary key. 
        """
        Attribute.__init__(self, name, er)   
        
        self.CPD = self.target.CPD
        """The CPD is shared with the `target` attribute. As the `target` is often the primary key,
        the `CPD` would be `None`.
        """
        
        

    @property
    def probabilistic(self):
        ''' The foreign attribute itself can't be probabilistic' '''
        #return self.target.probabilistic
        return False

    def __repr__(self):
        '''
        Returns a string representation of the instance 
        ''' 
        return "Foreign Attribute (%s -> %s)"%(self.fullname,self.target.fullname)

    @property    
    def fullname(self):
        '''
        Overwritten from class Attribute.
        The full name a foreign attribute is 'Relationship_name.Target_name'.
        '''
        return '%s.%s'%(self.erClass.name,self.name)     
        
        
def topologicalSort(attributes):
    '''
    Returns a list of attributes that are lexically sorted. A topological sort or topological 
    ordering of a directed acyclic graph (DAG) is a linear ordering of its nodes in which each
    node comes before all nodes to which it has outbound edges. Every DAG has one or more `topological 
    sort <http://en.wikipedia.org/wiki/Topological_sorting>`. 
    '''
    topoAttr = []
    visited = []
    
    def visit(attr):
        if attr not in visited:
            visited.append(attr)
            for dep in attr.dependenciesParent:
                visit(dep.child)
            topoAttr.append(attr)
            
    for attr in attributes:
        visit(attr)
    
    topoAttr.reverse()  
    #print topoAttr
    return topoAttr

    
    
    