'''
When making inference in a PRM, specifying a query is not as straight forward as in Bayesian Networks.
A :class:`.Query` instance consists of event and evidence variables, the inference goal being to
find a posterior distribution over the event variables given the evidence variables.

Two auxiliary data structures are used to specify event and evidence variables, 

* :class:`.Qvariable` for specifying attribute classes
* :class:`.ObjsVariable` for specifying attribute objects

'''

from network.groundBN import computeID

from analytics.performance import time_analysis

class Qvariable():
    '''
    A :class:`Qvariable` instance induces a set of attribute objects (:class:`.GBNvertex` instances) that are used for specifying event 
    and evidence variables when making inference.    
    '''
    def __init__(self, erClass, objs, attr, values=None):
        
        self.erClass = erClass


        self.objs = objs
        ''' 
        :class:`.ObjsVariable` instance.
        '''

        self.attr = attr
        ''' 
        :class:`.Attribute` instance
        '''

        self.values = values
        # Possibility to specify the set of attribute objects of with a certain value, not implemented yet
        
    
    
    def __repr__(self):
        return 'Qvar = %s, %s, %s'%(self.attr.fullname,self.objs,self.values)
        


def createQvar(fullname,objsV):
    '''
    Creats a :class:`Qvariable` from the string name of an :class:`.Attribute` instance, e.g. `Professor.fame`
    
    :arg fullname: Full name of an :class:`.Attribute`
    :arg objsV: :class:`.ObjsVariable` instance
    :returns: :class:`Qvariable` instance
    '''     
    attr = prmI.attributes[fullname]
    erClass = attr.erClass 

    return Qvariable(erClass, objsV, attr)



class ObjsVariable():
    '''
    Data structure that is used to define a set of attribute objects that are associated with a specific
    :class:`Qvariable` instance.
    
    :attr:`.pkValues` is a list of primary keys of the attribute class that the :class:`.Qvariable` instance is associated with. The `constraint` allows to specify a subset of all attribute objects in an expressive manner
        
        * inclusive 'incl' : only these attribute objects
        * exclusive 'excl' : all but these attribute objects
                
    '''
    
    exclusive = 'excl'
    inclusive = 'incl'
    
    def __init__(self,constraint,pkValues,complete=True):
        '''
        constraint - ALL BUT THESE (excl) or ONLY THESE (incl)
        objs - list of objs     [ (pk),(pk),(pk),(pk),...] if erClass is a Entity
                                [(pk1,pk2),(pk1,pk2),(pk1,pk2),(pk1,pk2),....] if erClass is a Relationship
        '''
        self.constraint = constraint
        """
        Constraint is either 'excl' or 'incl'
        """
        self.pkValues = None
        """
        List of primary keys, e.g.
        
        * [ (pk),(pk),(pk),(pk),...] in case of an :class:`Entity`
        * [(pk1,pk2),(pk1,pk2),(pk1,pk2),(pk1,pk2),....] in case of a :class:`Relationship`
        """
        
        if complete: 
            #pkValues contains a full specification, e.g. a value for all primary keys in qvar.attr.erClass.pk
            self.pkValues = pkValues
        else:
            #pkValues is defined in from of a dictionary and the remaining pkValues have to be loaded from the data
            pass
             
    def __repr__(self):
        return '%s, %s'%(self.constraint,self.pkValues)

class Query():
    '''    
    When performing inference on the PRM, we are given a set :math:`\mathbb{Y}` (`event` variables) and a set :math:`\mathbb{E}` (`evidence` variables), the 
    inference goal being to find 
    
    :math:`P(\mathbb{Y} \mid \mathbb{E})`
    
    '''
    def __init__(self,event,evidence=None):
        
        self.event = event
        ''' List of :class:`.Qvariable` instances representing event variables '''
        
        self.evidence = evidence
        ''' List of :class:`.Qvariable` instances representing evidence variables '''
        
        
        # Attribute Evidence Lookup Not Used anymore
        self.attrEvidenceLookup = None        
        self.computeAttrEvidenceLookup()
        
        
        self.objEvidenceLookup = None
        '''
        Dictionary used to check whether attribute objects are part of the evidence. Format:
        
            { key = :class:`.Attribute` instance : value = ( :attr:`.ObjsVariable.constraint` , [ List of  :attr:`.GBNvertex.ID` ] ) }
        
        When unrolling a GBN we are creating a d-separated BN for the query :math:`P(\mathbb{Y} \mid \mathbb{E})`. We need an efficient way
        to look up wheter a certain GBN node is in the evidence because this influences the structure of the 
        induced  graph, e.g.
        
        * If a loaded child is in :math:`\mathbb{E}` -> common cause -> load parents of node and don't load children'
        * If a loaded child is not in :math:`\mathbb{E}` -> load children of node
        
        The dictionary is computed by :meth:`.computeObjEvidenceLookup`
        '''
        
        self.computeObjEvidenceLookup()
        
        
    def __computeAttrEvidenceLookup(self):
        # not used anymore
        ''' 
        A very simple and not very expressive evidence lookup method that just allows to specify if object
        of a certain attribute are in the evidence or not.
        '''
        self.attrEvidenceLookup = []
        if self.evidence is not None:
            for qvar in self.evidence:
                self.attrEvidenceLookup.append(qvar.attr)
    
    def __attrInEvidence(self,attr):
        # not used anymore
        return attr in self.attrEvidenceLookup
    
    
    def computeObjEvidenceLookup(self):
        """
        Computes the :attr:`.objEvidenceLookup` dictionary
        """
        self.objEvidenceLookup = {}
        if self.evidence is not None:
            for qvar in self.evidence:
                self.objEvidenceLookup[qvar.attr] = (qvar.objs.constraint ,[computeID(qvar.attr,pkVal) for pkVal in qvar.objs.pkValues])
    

    
    def gbnVertexInEvidence(self,gbnVertex):
        """Calls :meth:`.objInEvidence` with parameters `gbnVertex.attr` and `gbnVertex.ID`
        
        :arg gbnVertex: :class:`.GBNvertex` instance
        """
        
        return self.objInEvidence(gbnVertex.attr,gbnVertex.ID)
        

    def objInEvidence(self,attr,gbnID):
        '''
        Returns `True` if attribute object passed as argument is part of the evidence.
        One would think that the a dictionary wouldn't be necessary and that a simple list containing all 
        gbnvertexIDs would suffice. But this is not the case since a :class:`.Qvariable` (e.g. evidence for one attibute)
        can either be 'inclusive' or exclusive, so the dictionary is needed to check the :attr:`ObjsVariable.constraint`.
        
        :arg attr: :class:`.Attribute instance`
        :arg gbnID: Attribute object ID
        
        :returns: `True` if attribute object is in evidence
        '''
        
        # **args = {attr:a,pkVal:pk,vertex:gbnV}
        #print gbnID
        if attr in self.objEvidenceLookup:
            (constraint,gbnVs) = self.objEvidenceLookup[attr]
            if constraint==ObjsVariable.inclusive:
                # ONLY THESE
                #print constraint, ' gbnID in gbnVs=',gbnID in gbnVs
                return gbnID in gbnVs
            else:
                # ALL BUT THESE
                #print constraint, ' gbnID not in gbnVs=',gbnID not in gbnVs
                return gbnID not in gbnVs
        else:
            #print attr,' not in evidence'
            return False
        

    
    def __repr__(self):
        #r = [qvar.attr for qvar in self.event]
        #print r
        eventS = " ".join([qvar.attr.fullname for qvar in self.event])
        if self.evidence != None:
            evidenceS = " ".join([qvar.attr.fullname for qvar in self.evidence])
            return 'P(%s | %s)'%(eventS,evidenceS)                        
        return 'P(%s)'%(eventS)
            