class Dependency():
    '''
    A dependency represents a probabilistic dependency between two :class:`.Attribute` classes, the `child` and the `parent` attribute.
    '''


    def __init__(self, name, parent, child, constraint, aggregator):
        '''
        Constructs a dependency between two attributes. 
        '''
        
        self.name=name
        """Unique name of the dependency
        """
        self.parent = parent
        """The `parent` is an :class:`.Attribute` instance 
        """
        self.child = child
        """The `child` :class:`.Attribute` instance is the dependent variable.
        """
        self.constraint = constraint
        """The `constraint` of a dependency defines how the attribute objects in the relational skeleton
        are connected. Introduced by Heckerman et al. in the `DAPER` model, the concept of a constraint is a generalized 
        version of the `slotchain` introduced by Getoor et al.
        """
        self.aggregator = aggregator
        """
        Aggregation is necessary when a dependency is of type `1:n` or `m:n` as there will be multiple
        parent objects mapping to a child object's CPD that has only one parameter for this parent attribute.
        Aggregation can be any function :math:`f(pa1,pa2,...) = pa_{aggr}` , see :mod:`data.aggregation`
        """
        self.slotchain = []
        """
        Even though the probabilistic dependency uses the `constraint` when specifying a PRM model,
        often the `constraint` results in the traditional slotchain, the 'path' through the relational 
        schema that links the parent and child attribute via a list of entities and relationships, connected
        by foreign keys.
        The elements in the list `slotchain` are interchangeably [..., :class:`.Entity`, :class:`.Relationship`, :class:`.Entity`,... ]                
        """        
        self.slotchain_string = []
        """
        List containing the string representation (e.g. `name`) of the slotchain entities/relationships
        """
        self.slotchain_attr_string = []        
        """
        List of the string represenation of the attributes that define the slotchain
        """
        
    def configureConstraint(self,attributes):
        """
        If a constraint has been defined in the specification, e.g. in the following form::
        
            self.constraint = "...,e1.a1=r1.a2,r1.a3,e2.a4,..."
            
        where `e1`, `e2` are of type :class:`.Entity`, `r1` of type :class:`.Relationship` 
        and `a1`, `a2`, `a3`, `a4` are of type :class:`.Attribute`.
        From this string `slotchain`, `slotchain_string` and `slotchain_attr_string` can be extracted. In case no constraint has been specified, :meth:`.computeSlotChain` is called to compute a traditional `slotchain`.
        
        :arg attributes: All :class:`.Attribute` instances in the model        
        """    
        if self.constraint is None:
            raise Exception('Constraint for %s is None'%self.name)
        
        def addToSlotchain(er):
            if er not in self.slotchain:
                self.slotchain.append(er)
        
        slotchain_attr_temp = [t.strip() for t in self.constraint.split(',')]
        
        for sl_attr in slotchain_attr_temp:
            #extract from attribute and to attribute            
            (fromA_str,toA_str) = sl_attr.split('=')
            formA = attributes[fromA_str]
            toA = attributes[toA_str]
            addToSlotchain(formA.erClass)
            addToSlotchain(toA.erClass)
            
            self.slotchain_attr_string.append('%s=%s'%(formA.fullname,toA.fullname))
        
        
        #print self.slotchain_attr_string
        self.slotchain_string = [er.name for er in self.slotchain]    
        
    def computeSlotChain(self):
        '''
        The SlotChain is computed via a depth first search algorithm.
        As there can't be loops in the relational schema, we can return the
        first path that we encounter.       
               
        Note that when the model doesn't load, it is usually because of the infinite loop
        that only quits when a slot chain was found. So far that always resulted from an 
        error in the specification and not in the code...
        
        Another disadvantage is that there could be multiple paths in the same schema.
        In fact you could define a different dependency for each different path. This method 
        uses the first path that is found as the slotchain.
        '''                
        
        pathFound = False
        tempSCs = [[self.child.erClass]]        
        
        #inner object dependency
        if self.child.erClass == self.parent.erClass:            
            pathFound = True
            self.slotchain = [self.child.erClass]
        
        #slot chain over multiple erClasses
        while not pathFound:
                    
            tempCSsCopy = tempSCs[:]
            tempSCs = []
            for sc in tempCSsCopy:
                if sc[-1].type() == 'Entity':
                    for ass in sc[-1].relationships.values():
                        if ass not in sc:                            
                            newSC = sc[:]
                            newSC.append(ass)
                            tempSCs.append(newSC)   
                else: #Relationship
                    for ent in sc[-1].entities:
                        if ent not in sc:
                            newSC = sc[:]
                            newSC.append(ent)
                            tempSCs.append(newSC)    
                                  
            
            for sc in tempSCs:
                if self.parent.erClass in sc:                    
                    pathFound = True
                    self.slotchain = sc
                
        
        #The slotchain is now stored in self.slotchain  
        self.slotchain_string = [er.name for er in self.slotchain]
        #print 'self.slotchain: ', self.slotchain
        #print 'self.slotchain_string: ',self.slotchain_string                
        
        
        # In a slotchain, an Entity is always followed by a Relationship and vice versa
        for i in range(0,len(self.slotchain)-1):
            currentER = self.slotchain[i]
            nextER = self.slotchain[i+1]
            attrs = None
            if currentER.isEntity():
                attrs = nextER.foreign[currentER]
            else: #currentER is a relationship
                attrs = currentER.foreign[nextER]
            
            #attrs is a list (in case an relatioship has two foreign keys from the same entity)
            tempKey = []
            for attr in attrs:                
                targetAttr = attr.target     
                tempKey.append('%s=%s'%(attr.fullname,targetAttr.fullname))
            
            tempKey_string = tempKey[0]
            if len(tempKey) != 1:
                tempKey_string = '(%s)'%' OR '.join(tempKey)
                                            
            self.slotchain_attr_string.append(tempKey_string)
        
        
        
        
        #print 'self.slotchain_attr_string: ',self.slotchain_attr_string
                  
        #print "SlotChain for %s from %s to %s"%(self.name,self.child.fullname,self.parent.fullname)
        #print self.slotchainToString()

    def slotchainToString(self):
        """
        :returns: String representation of `slotchain`
        """
        st = ''
        for er in self.slotchain:
            st +=  '<-'+str(er.name)
                            
        return st[2:]    
            
        
    def __repr__(self):
        '''
        Returns a string representation of a dependency 
        ''' 
        return "Dependency (%s, Parent=%s, Child=%s SlotChain:%s)"%(self.name, self.parent.fullname,self.child.fullname,self.slotchainToString())        
        
        