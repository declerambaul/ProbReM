'''
The ground Bayesian network implemented in :mod:`network.groundBN` consists of different kind of vertices implemented in :mod:`network.vertices`.

* Standard GBN vertex :class:`.GBNvertex`
* Reference Vertex :class:`.ReferenceVertex`

'''

import logging
from analytics.performance import time_analysis


def computeID(attr,obj):
    """A simple helper function that computes a unique ID from an `attr` and `obj`, the primary key of the attribute object which is part of the GBN.
    
    :arg attr: Subclass of :mod:`prm.attribute.Attribute`
    :arg obj: List of int values
    :returns: A unique string ID for the attribute object
    """
    return '%s.%s'%(attr.ID,'.'.join([str(i) for i in obj]))

def computeRefID(gbnV):
    """A simple helper function that computes a unique reference ID from an `gbnV` vertex

    :arg gbnV: Instance of :class:`.GBNvertex`
    :returns: A unique string ID for the reference vertex 
    """
    return 'RefV_%s'%gbnV.ID

def computeERID(er,obj):
    """A simple helper function that computes a unique ID from an object (e.g. a student). It allows to identify an object (e.g. `student.1`), rather than an attribute object (e.g. `student.success.1`) computed by :meth:`.computeID`.
    
    :arg er: Instance of :class:`.ERClass`
    :returns: A unique string ID for the object
    """
    return '%s.%s'%(er.name,'.'.join([str(i) for i in obj]))
        


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
    def __init__(self,attr,obj=None,ID=None,event=False,fixed=False,value=None,deterministic=False,aggregation=None): 
        
        
        self.attr = attr
        """
        The associated attribute class
        """
        self.obj = obj
        """
        List identifier for the vertex
        """        
        
        
        self.ID = None
        '''
        An identifier for the unrolled :class:`.Attribute` object, e.g. Student.success.1
        '''
        # It could be computed at the time of instantiation, but usually is already computed to check whether the vertex is already present in the graph
        if ID is None:
            self.ID = computeID(self.attr, self.obj)
        else:
            self.ID = ID 
        
        self.erID = None
        """
        An identifier for the unrolled :class:`.ERClass` object, e.g. Student.1
        """
        # self.erID is only possible if we have an object (i.e. not applicable for reference vertices)
        if self.obj is not None:
            self.erID = computeERID(self.attr.erClass,self.obj)
        

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
        self.parents = {}
        """
        The dictionary of parents attribute objects {key=`parent.attribute` : value= { key=`id` : value = `GBNvertex`}}. `parent.attribute` is of type :class:`~prm.attribute.Attribute` and the `gbnVertices` of type :class:`GBNvertex`
        """        
        self.parentAss = []
        """
        The parent assignment of the parents of this node. The order of the parent values is the same as the `self.attr.parents` list. It can be updated using :meth:`parentAssignments`
        """
        #init the parent dict 
        for dep in self.attr.dependenciesChild:
            self.parents[dep.parent] = {}                        
            self.parentAss.append(None)
            
        self.children = {}
        """
        The dictionary of children attribute objects {key=`child.attribute` :  value= { key=`id` : value = `GBNvertex`}}. `child.attribute` is of type :class:`~prm.attribute.Attribute` and the `gbnVertices` of type :class:`GBNvertex`
        """
        # init the children dict 
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
        if self.fixed:
            raise Exception('Why is a fixed GBN vertex being sampled?')
        self.parentAssignments();
        self.value = self.attr.CPD.sample(self.parentAss)
        
    
    def conditionalDist(self):
        '''
        Returns the conditional probability distribution of the `gbnV` given its parent values.

        .. todo::

            In this branch I bypass the :mod:`.aggregation` module and implement weighted expectation directly into this method. The `aggregation` needs to be adapted and improved, until then it is less messier to do the aggregation directly here.

        :arg gbnV: :class:`.GBN` instance
        :returns: A `1 x |attr.domain|` numpy.array probability distribution
        '''
        return self.attr.CPD.conditionalDist(self)


    def parentAssignments(self):
        '''
        Computes the values of the parents of that GBN vertex (using aggregation if necessary). Note that since there is an `GBNVertex` instance for every node in the GBN, the parent assignments are stored in the instance variable self.parentAss. In the case of the local distribution instance of an attribute, this is not the case as the distribution is shared among many attribute objects.
        '''
        for i,dep in enumerate(self.attr.dependenciesChild):
            if dep.aggregator is None:
                #there should be only one parent value in this case
                paVal = self.parents[dep.parent].values()   
                
                # Just for debugging, when the model is proper that should never happen: comment out for performance
                # if len(paVal) != 1:    
                #     raise Exception('ERROR, no aggregation for %s but %s has %s parents'%(dep.name,self,len(paVal)))
                  
                self.parentAss[i] = paVal[0].value           
            else:
                #we perform a runtime aggregation
                paVals = [gbnV.value for gbnV in self.parents[dep.parent].values()]
                agg_func = dep.aggregator('runtime')
                
                # logging.info('aggregation for %s'%self.ID)
                # logging.info( 'parents : %s'%([v.ID for v in self.parents[dep.parent].values()]))
                # logging.info( 'paVals : %s'%(paVals))
                                    
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




class ReferenceVertex(GBNvertex):
    '''
    The class :class:`.ReferenceVertex` is a compact representation of the probabilitic variables required to represent reference uncertainty for one connection. A relationship `r` connects two entities `e1`, `e2` with a certain type of connection; either a `n:1` or a `m:n` connection. In case of a `n:1` connection, like in the student professor example, each object in `e1` is associated with exactly one object in `e2`, whereas an object in `e2` can be associated with multiple objects in `e1`. 


    For example, when infering the success of a student `s1.s`. There will be one :class:`.ReferenceVertex` instance that contains a datastructure representing the shaded nodes in the network displayed below.

    .. figure:: figures/ref_unc_ex.png
        :width: 60 %

    .. note::

        For now this works, but there is a problem.

        If there are multiple dependencies leading through the uncertain dependency dep, they all must use
        the same mapping of course (i.e. the same exist attributes)

        Student/Prof Example: 
        If the 
            student.success depends on Professor.fame  

        and a

            student.phd also depends on Professor.fame

        Assuming that we do inference for student1 on student.success and student.phd, then of course all exist attributes with student1 should be identical. This means that if we sample the exist attributes, then the edges for student.success and student.phd should be changed!

        At this point, a GBN reference vertex is associated with only 1 GBN vertex (e.g. student1.success) of the n-Entity. In reality it should be associated with 1 object (e.g. student1) of the n-Entity. 

        This is not hard to do::

            `self.refGBNvertex` should be a dictionary holding all attribute objects (e.g. student.success.1 student.iq.1 and student) of a certain object (e.g. student.1)

            `self.dependency = dep` should be a dictionary holding all uncertain dependencies 

        
    '''

    

    def __init__(self, ID, gbnV ,dep):
                       
        GBNvertex.__init__(self, attr = dep.uncertainRelationship.existAttribute,ID=ID, event=False, fixed = False)   
        # For now, the 'event = False' is hardcoded -> the exist attributes are always latent (i.e. sampling) variables

        self.dependency = dep
        '''The uncertain :class:`.Dependency` instance
        '''

        self.relationship = self.dependency.uncertainRelationship
        '''The uncertain :class:`.Relationship `instance
        '''

        self.refGBNvertex = gbnV
        '''
        The referenced :class:`.GBNvertex` (which is on the n-side of the `n:k` relationship)
        '''
        self.k = self.relationship.k
        '''
        The relationship is assumed to be of type `n:k`, where `k` serves as a fixed-parameter to limit the size of the state space of the Markov chain for inference. Assuming that relationship `R` of type `n:k` is connecting entities (`E1`,`E2`). Thus every object in `E1` is connected with at most `k` objects in `E2`. By definition, the `E1` and `E2` refer to the first and second entry in the `relationship.pk` list, respectively. 
        '''

        self.references = {}
        '''
        The theoretical `exist` attributes don't have to stored explicitly. The deterministic constraint (`k`) limits the number of non-zero `exist` variables to `k`. :attr:`.ReferenceVertex.references` is a compact represenation of all exist attributes for one `n-side` attribute object (i.e. a students success). The dictionary of length :attr:`.ReferenceVertex.k` stores all links that exist (i.e. the exist attribute is `1`) in the format {key = k_entity_ID : value =  gbnV_E2 }.  

        The methods :meth:`.addReference`, :meth:`.removeReference` and :meth:`.replaceReference` can be used to manipulate this datastructure. 
        '''  

        self.existParents = {}
        '''
        { key = k_entity_ID (e.g. Professor.2) : value = { key = parent.attr (e.g. prof.funding) : value = { key = parent.ID (e.g. 'prof.funding.2') : value = parent.Vertex (e.g. prof.funding.2.vertex)} }  }
        '''   

        
           
    
    def removeReference(self,gbnV_old):
        '''
        Removes one reference in `self.references` and updates the parent/children information of the involved vertices.
        
        :arg gbnV_old: :class:`.GBNvertex` to be removed.
        '''

        k_ent_ID = gbnV_old.erID

        if k_ent_ID not in self.references:
            return
        
        #remove child/parent information from the GBN
        if self.dependency.nIsParent:
            # A `n:k` relationship means the n objets (students) be associated with exactly k objects (profs)
            # This means a reference attribute is associated with one n object and the references point to k
            # objects. If `nIsParent()` is `True` for involved dependency, the added reference k attribute is
            # the child and we can add the edges in the GBN accordingly

            del self.refGBNvertex.children[gbnV_old.attr][gbnV_old.ID] 
            del gbnV_old.parents[self.refGBNvertex.attr][self.refGBNvertex.ID]

        else:
            del self.refGBNvertex.parents[gbnV_old.attr][gbnV_old.ID] 
            del gbnV_old.children[self.refGBNvertex.attr][self.refGBNvertex.ID]
            

        del self.references[k_ent_ID]


    def addReference(self,gbnV_new):
        '''
        Adds one reference in `self.references` and updates the parent/children information of the involved vertices.

        :arg gbnV_new: :class:`.GBNvertex` to be added.
        '''        
        k_ent_ID = gbnV_new.erID

        if k_ent_ID in self.references:
            return
        
        #otherwise, add the reference to the dictionary
        self.references[k_ent_ID] = gbnV_new
        #add the parent/child information to the GBN vertices
        if self.dependency.nIsParent:
            # A `n:k` relationship means the n objets (students) be associated with exactly k objects (profs)
            # This means a reference attribute is associated with one n object and the references point to k
            # objects. If `nIsParent()` is `True` for involved dependency, the added reference k attribute is
            # the child and we can add the edges in the GBN accordingly
            

            logging.info('adding %s as parent of %s'%(self.refGBNvertex.ID,gbnV_new.ID))


            self.refGBNvertex.children[gbnV_new.attr][gbnV_new.ID] = gbnV_new
            gbnV_new.parents[self.refGBNvertex.attr][self.refGBNvertex.ID] = self.refGBNvertex

        else:
            
            # logging.info( 'self.refGBNvertex',self.refGBNvertex)
            # logging.info( 'self.refGBNvertex',self.refGBNvertex.parents)
            # logging.info( 'gbnV_new', gbnV_new)

            # import pdb; pdb.set_trace()

            # logging.info( 'parents of %s : %s'%(self.refGBNvertex.ID,[v.ID for pas in self.refGBNvertex.parents.values() for v in pas.values()]))
            # logging.info( 'adding %s as parent of %s'%(gbnV_new.ID,self.refGBNvertex.ID))

            self.refGBNvertex.parents[gbnV_new.attr][gbnV_new.ID] = gbnV_new
            gbnV_new.children[self.refGBNvertex.attr][self.refGBNvertex.ID] = self.refGBNvertex



    def replaceReference(self,gbnV_new,gbnV_old):
        '''
        Replaces one reference in `self.references` by another.

        :arg gbnV_new: :class:`.GBNvertex` to be added.
        :arg gbnV_old: :class:`.GBNvertex` to be removed.
        '''
        self.removeReference(gbnV_old)
        self.addReference(gbnV_new)

    def removeAllReferences(self):
        '''
        Removes all references from `self.references`. 
        '''
        for gbnV in self.references.values():
            self.removeReference(gbnV)


    # @time_analysis
    def parentAssignments(self,k_gbnV):
        '''
        Note, this method is overwritten from :class:`.GBNvertex`. As a reference vertex is a represenation of multiple (i.e. `self.k`) exist attributes, there are also multiple parent assignment. The methods takes a `k_gbnV_erID` of the k-entity as argument and returns the parent assignments list of the exist attribute object associated with `k_gbnV_erID`.
        This is probably neither fast nor pretty, another way would be to also overwrite :attr:`.GBNVertex.parentAss` to use a dictionary for all entries in :attr:`ReferenceVertex.references`. As is, a new list is returned at each execution.
        
        :arg k_gbnV_erID: `erID` of :class:`GBNVertex` instance
        :return: List of parents assignments
        '''
        
        k_gbnV_erID = k_gbnV.erID
        parentAss = []


        for i,dep in enumerate(self.attr.dependenciesChild):
            if dep.aggregator is None:
                #there should be only one parent value in this case

                paVal = self.existParents[k_gbnV_erID][dep.parent].values()   
                
                # Just for debugging, when the model is proper that should never happen: comment out for performance
                # if len(paVal) != 1:    
                #     raise Exception('ERROR, no aggregation for %s but %s has %s parents'%(dep.name,self,len(paVal)))
                  
                parentAss.append(paVal[0].value)
            else:
                #we perform a runtime aggregation
                paVals = [gbnV.value for gbnV in self.existparents[k_gbnV_erID][dep.parent].values()]
                agg_func = dep.aggregator('runtime')
                                    
                paAgg = agg_func(paVals)                
                
                parentAss.append(paAgg)

        return parentAss

    def __repr__(self):
    
        r = '%s (Rel:%s , exist:%s)'%(self.ID, self.relationship.name,self.relationship.existAttribute.fullname)
        return r



