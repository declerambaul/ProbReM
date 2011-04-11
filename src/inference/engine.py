'''
The inference engine handles inference. 

* Unrolling the Ground Bayesian Network ('propositionalize' the the first-order representation)
* Run an inference algorithm (e.g. Gibbs sampling)

There are different algorithms that will need to perform inference:

* Simple query :math:`P(event|evidence)`
* Expectation Maximization (EM) for missing data / latent variables
* Structure learning
* Reference uncertainty
'''



import logging

from network.groundBN import GBNGraph,GBNqueue
from network.vertices import GBNvertex,ReferenceVertex,computeID,computeERID

from analytics.performance import time_analysis

import random



import prm.prm as PRM
''' :mod:`prm.prm` instance
'''
import data.datainterface as DI
''' :mod:`data.datainterface` instance
'''

GBNS = {}
'''
At this point, only one ground Bayesian network exists, :attr:`.GBN`. If posterior samples are collected from multiple chains,  e.g. in the case of MCMC inference, it would be ideal to run these chains in paralell. However this would require multiple instantiations of the ground Bayesian network. Not just the values of the vertices are required, since the network stucture changes with reference uncertainty, the whole network needs to be duplicated.

We could envision a dict() of ground Bayesian networks. Note that copy.deepcopy() doesn't work as it would also copy all other istances, e.g. :class:`.Attribute` objects.

Also, there would be problems with some datastructures that use an ID of a :class:`.GBNvertex` as a key. For example the :attr:`.ReferenceVertex.existParents` would break. 

For now, changes are run sequentially and the convergence diagnostics are run on the collected samples of the :mod:`.posterior`.
'''

GBN = GBNGraph()
'''Ground Bayesian Network used for inference of type :class:`.GBNGraph`. 
'''

gbnQ = GBNqueue()
''':class:`.GBNqueue` data structure used to unroll the GBN
'''


inferenceAlgo = None
'''
The algorithm used for the approximate inference (e.g. :mod:`.gibbs`,:mod:`.mh` ) 
'''

query = None
'''Current Query instance of type :class:`.Query` 
'''

    
def reset():
    """
    Resets the :class:`GBNGraph` and :class:`GBNqueue` instances.
    """
    global GBN,gbnQ
    
    for gbnV in GBN.values():
        del gbnV
    del GBN
    del gbnQ
    GBN = GBNGraph()
    gbnQ = GBNqueue()

    
@time_analysis
def infer(queryI):
    global query
    '''
    Runs inference for `query` by 
        
    * Resetting GBN
    * Unrolling GBN
    * Initialize inference algorithm
    * Run inference and collect posterior samples        
    
    :arg query: :class:`.Query` instance        
    '''
    query = queryI
    logging.info('Inference for: %s'%query)
        
    reset()
    #unrolling the ground bayes net
    unrollGBN()
    
    logging.info(GBN)
    
    inferenceAlgo.run()
    # logging.debug('inferenceAlgo.run() is commented')
    
            

# @time_analysis
def unrollGBN():
    '''
    The unrolled Ground Bayesian Network is a subgraph of the
    full graph that d-seperated the event variables `Y`
    from the query from the rest of the graph given the evidence
    variables. 
    
    .. note::
        Add proper description of algorithm
    
    
    
    '''
    
    

    # TODO : FIX THE CROSS VALIDATION. WE DON'T WANT TO QUERY K DIFFERENT FOLDS 
    # WHEN UNROLLING. JUST ONE, THE TRAINING SET FOLD
    dsi = DI.DSI[0]
    #print DI.trainingSets[di.DSI[0]]
    
    
    # add the inference (event) variables to the GBN 
    for qvar in query.event:
        #load all objects in qVariable
        dsi.loadObjects(qvar)
        # result set row : [attribute, pk1 , pk2, ....]
        
        
        #adding all inference vertices for that qVariable to the ground bayes net
        for row in dsi.resultSet():
            
            vertexID = computeID(qvar.attr,row[1:]) 
            #add Vertex
            GBN.addVertex(ID=vertexID,attr=qvar.attr,obj=row[1:],fixed=False,event=True)
            
            #add Vertex to the dictionary of event vertices
            GBN.eventVertices[vertexID] = GBN[vertexID]
            
            #add vertex to the queue of vertices to process
            gbnQ.push(GBN[vertexID])
            #logging.debug('pushed on queue: %s'%gbnVertex)

            
        
    # logging.info('All %s inference vertices have been added'%(len(GBN)))
    # logging.info('\t%s'%' '.join([gbnV.ID for gbnV in GBN.values()]))

    # add all the parents of the inference nodes
    while not gbnQ.isEmpty():
        (attr,gbnVertices) = gbnQ.pop()
        
        #logging.info('Handling attribute %s with %s gbn vertices'%(attr.fullname,len(gbnVertices)))
        
        #filtering the gbn vertices that are part of the evidence

        gbnVerticesNotInE = filter(lambda gbnV: not query.gbnVertexInEvidence(gbnV), gbnVertices)
        #logging.debug("gbnVerticesNotInE: %s"%gbnVerticesNotInE)
        
        #We load the parents. Note that the parents are also loaded for gbnVertices that are in 
        #the evidence to cover the V-structure effect (explaining away)
        #logging.info('Loading Parents for %s'%(attr.fullname))
        addParents(attr,gbnVertices)            
        
        #we only load the children if the gbnvertex is not in the evidence (if there are any)
        #logging.info('Loading Children for %s'%(attr.fullname))
        if gbnVerticesNotInE: 
            addChildren(attr,gbnVerticesNotInE)
        
        #logging.info('Done Handling %s'%(attr.fullname))

def validateGBN():
    """
    Validating the GBN is necessary as there might be missing data (either because there is no datapoint or the datapoint is missing from the dataset). The standard approach would be to use an `EM` algorithm to find the `MLE` for the missing data. 
    In order for the inference method to work we need to have valid probability distributions. In case there is a GBN vertex that has no parent vertex but a probability distribution conditional on that parent attribute, one way to avoid invalid GBN structures is to add a sampling vertex. This is only possible (and reasonable) in case this sampling vertex does not depend on parent values it
    """
    for attr, gbns in GBN.allByAttribute.items():
        if attr.hasParents:
            # in this case all gbn vertices of this attribute should have at least one parent
            for gbnV in gbns:
                for paAttr in gbnV.parents.keys():
                    if not gbnV.hasParents(paAttr):
                        # if there aren't any parents, a sampling vertex is added.
                        artificial_ID = '%s(%s)'%(paAttr.fullname,gbnV.ID)
                        GBN.addSamplingVertex(artificial_ID,paAttr,None)
                        GBN[gbnV.ID].addParent(GBN[artificial_ID])
                        logging.debug('adding artificial %s'%artificial_ID ) 
        

# @time_analysis
def addParents(attr,gbnVertices):
    '''
    Loads the set of parent attribute objects for all dependencies for the given GBN vertices of the same attribute class. The BGN is updated and potential new latent variables are added to the queue.
    
    :arg attr: :class:`.Attribute` instance
    :arg gbnVertices: List of :class:`.GBNvertex` instances of type `attr`                
    '''
    
    # NOTE ON EVIDENCE LOOKUP:
    #         when looking up evidence based on attribute (=all objects of an attribute are either in
    #         the evidence or not), then we check attrEvidenceLookUp() only once:
    #             dep.parent in Evidence?
    #                 yes -> for row in resultset do this
    #                 no -> for row in resultset do this instead
    #         
    #         In case the evidence is object based (=one object of a certain attribute can be in the evidence 
    #         while another object of the same attribute is not), then this is not possible and we have to do
    #         the objEvidenceLookUp() for every object over which we iterate:
    #             for row in resultset:
    #                 if obj in evidence?
    #                     yes -> do this
    #                     no -> do that
    
    
    # TODO : FIX THE CROSS VALIDATION. WE DON'T WANT TO QUERY K DIFFERENT FOLDS 
    # WHEN UNROLLING. JUST ONE, THE TRAINING SET FOLD, AT THIS POINT WE ARE ONLY WORKING WITH ONE FOLD.
    dsi = DI.DSI[0]
    #print DI.trainingSets[di.DSI[0]]
    
    
    # parents for each dependency that the attribute is a child of
    for dep in attr.dependenciesChild: 
                                        
        if dep.uncertain:
            # Reference Uncertainty

            
            
            # If there are no exist attributes in the GBN, all required attribute need to be added to the GBN first
            if dep.uncertainRelationship.existAttribute not in GBN.allByAttribute: 
                initReferenceUncertainty(dep)

            
            # Note that 'gbnVertices' is a SET of gbnVertices 
            for gbnV in gbnVertices:
            
                logging.debug('Adding Reference vertex for %s'%gbnV.ID)
                
                refVID = GBN.addReferenceVertex(gbnV,dep)

                # Initialize the edges for all k connections
                for i in range(GBN[refVID].k):
                    

                    # choose one k-entity object
                    # TODO sample it from proposal distribution.... 
                    # choose uniformly for now (i.e. = Pasula paper)
                    kGBNv = random.choice(GBN.allByAttribute[dep.kAttribute])                    

                    GBN[refVID].addReference(kGBNv)


        else:
            #  No Reference Uncertainty

            # variables used to access the result sets redefined for code readability    
            child_pk = dep.child.erClass.pk
            n_child_pk = len(child_pk)
            parent_pk = dep.parent.erClass.pk
            n_parent_pk = len(parent_pk)
            end_parent_pk = n_child_pk+n_parent_pk
            
            
            # load all parent obj
            dsi.loadDependencyParentObjects(dep,gbnVertices)
            
            
            for row in dsi.resultSet():
                
                
                #extract child id
                child_ID = computeID(dep.child,row[0:n_child_pk]) 
                #extract parent information
                parent_obj = row[n_child_pk:end_parent_pk]
                parent_val = row[-1]
                parent_ID = computeID(dep.parent,parent_obj) 
                

                                            
                #only add if not already in GBN
                if parent_ID not in GBN:   
                
                    #logging.debug('%s : adding parent %s (val=%s)'%(child_ID,parent_ID,parent_val))
                
                
                        
                    if not query.objInEvidence(dep.parent,parent_ID) : #parent obj not in evidence -> add the queue  
                    
                        GBN.addSamplingVertex(parent_ID,dep.parent,parent_obj)
                        gbnQ.push(GBN[parent_ID])                    
                        #Having added the vertex just before, we can for efficiency reasons add the edge to the GBN as we know that it hasn't been there before
                        #adds parent information to child node                    
                        GBN[child_ID].parents[GBN[parent_ID].attr][parent_ID] =GBN[parent_ID] 
                        #adds child information to parent node
                        GBN[parent_ID].children[GBN[child_ID].attr][child_ID] = GBN[child_ID]
                    
                    elif parent_val is not None:   #parent obj is in evidence -> d-seperates -> not pushed onto queue 

                        #add parent vertex to GBN
                        GBN.addEvidenceVertex(parent_ID,dep.parent,parent_obj,parent_val)  
                        #Having added the vertex just before, we can for efficiency reasons add the edge to the GBN as we know that it hasn't been there before
                        #adds parent information to child node                    
                        GBN[child_ID].parents[GBN[parent_ID].attr][parent_ID] = GBN[parent_ID] 
                        #adds child information to parent node
                        GBN[parent_ID].children[GBN[child_ID].attr][child_ID] = GBN[child_ID]
                    
                #parent vertex already in GBN
                else:    
                    #add parent information to child node
                    GBN[child_ID].addParent(GBN[parent_ID])  
        
# @time_analysis
def addChildren(attr,gbnVertices):
    '''
    
    Loads the set of children attribute objects for all dependencies for the given GBN vertices of the same attribute class. The BGN is updated and potential new latent variables are added to the queue.
    
    :arg attr: :class:`.Attribute` instance
    :arg gbnVertices: List of :class:`.GBNvertex` instances of type `attr`                
    '''
    
    # TODO : FIX THE CROSS VALIDATION. WE DON'T WANT TO QUERY K DIFFERENT FOLDS 
    # WHEN UNROLLING. JUST ONE, THE TRAINING SET FOLD
    dsi = DI.DSI[0]
    #print DI.trainingSets[di.DSI[0]]
    
    
    # parents for each dependency that the attribute is a child of
    for dep in attr.dependenciesParent: 


        if dep.uncertain:
            # Reference Uncertainty

            raise Exception('We are adding children of an uncertain depependcy. Not implemented yet.')


        else:
            # No Reference Uncertainty
        
            # variables for code readability 
            parent_pk = dep.parent.erClass.pk
            n_parent_pk = len(parent_pk)
            child_pk = dep.child.erClass.pk
            n_child_pk = len(child_pk)
            end_child_pk = n_child_pk+n_parent_pk
            
            # load all parent obj
            dsi.loadDependencyChildrenObjects(dep,gbnVertices)            
            
            for row in dsi.resultSet():
                #extract parent id
                parent_ID = computeID(dep.parent,row[0:n_parent_pk]) 
                #extract child information
                child_obj = row[n_parent_pk:end_child_pk]
                child_val = row[-1]
                child_ID = computeID(dep.child,child_obj) 
                
                
                #only add if not already in GBN                
                if child_ID not in GBN:   
                
                    #logging.debug('%s : adding child %s (val=%s)'%(parent_ID,child_ID,child_val))
                
                    if not query.objInEvidence(dep.child,child_ID):   #children obj is not in evidence                     
                        #add child vertex to the GBN
                        GBN.addSamplingVertex(child_ID,dep.child,child_obj)
                    
                        #Having added the vertex just before, we can for efficiency reasons add the edge to the GBN as we know that it hasn't been there before
                        #adds parent information to child node                    
                        GBN[child_ID].parents[GBN[parent_ID].attr][parent_ID] =GBN[parent_ID] 
                        #adds child information to parent node
                        GBN[parent_ID].children[GBN[child_ID].attr][child_ID] = GBN[child_ID]
                    
                        # pushing gbnVertex onto queue (also push vertices that are in the evidence because of possible V-structures)
                        gbnQ.push(GBN[child_ID])
                    
                    elif child_val is not None:    #children obj is in evidence 

                    
                        #add child vertex to the GBN
                        GBN.addEvidenceVertex(child_ID,dep.child,child_obj,child_val)  

                        #Having added the vertex just before, we can for efficiency reasons add the edge to the GBN as we know that it hasn't been there before
                        #adds parent information to child node                    
                        GBN[child_ID].parents[GBN[parent_ID].attr][parent_ID] =GBN[parent_ID] 
                        #adds child information to parent node
                        GBN[parent_ID].children[GBN[child_ID].attr][child_ID] = GBN[child_ID]
                    
                        # pushing gbnVertex onto queue (also push vertices that are in the evidence because of possible V-structures)
                        gbnQ.push(GBN[child_ID])
                
            
                #child vertex already in GBN                    
                else:    
                    #add parent information to child node
                    GBN[child_ID].addParent(GBN[parent_ID]) 
                     
                    # TODO is this correct? or do we need to push to vertex even if it is already in the gbn? What happens if a vertex is reached from two 'sides' one of which opens a V structre - this means that the vertex is already in the gbn and therefore only the edge is added, even though the V-structure should be loaded
                    #gbnQ.push(GBN[child_ID])
                         
                       
        
# @time_analysis
def initReferenceUncertainty(dep):
    '''
    When a uncertain relationship is first encountered, all the attribute objects that could be associated with the object that initiated the reference have to be loaded. Additionally, all the parent attributes of the exist attributes need to be loaded as well.

    :arg dep: :class:`.UncertainDependency` instance
    '''
    # TODO : FIX THE CROSS VALIDATION. WE DON'T WANT TO QUERY K DIFFERENT FOLDS 
    # WHEN UNROLLING. JUST ONE, THE TRAINING SET FOLD, AT THIS POINT WE ARE ONLY WORKING WITH ONE FOLD.
    dsi = DI.DSI[0]  
            
    # logging.debug('Add all attribute objects of type %s'%dep.kAttribute.fullname)
    
    # variables used to access the result sets redefined for code readability                    
    n_pk = len(dep.kAttribute.erClass.pk)
    
    
    # load all attribute obj
    dsi.loadAttributeObjects(dep.kAttribute)
                    
    for row in dsi.resultSet():
        
        #extract id information
        attr_obj = row[0:n_pk]
        attr_ID = computeID(dep.kAttribute,attr_obj)
        attr_val = row[-1]
        
        # Add the vertex to the GBN
        # Note that we don't add parent/child information as the reference attribute needs to be instantiated first
        if attr_ID not in GBN:

            if not query.objInEvidence(dep.kAttribute,attr_ID) : #attr obj not in evidence -> add the queue
                
                GBN.addSamplingVertex(attr_ID,dep.kAttribute,attr_obj)
                gbnQ.push(GBN[attr_ID])

            elif attr_val is not None:   #attr obj is in evidence -> d-seperates -> not pushed onto queue 

                GBN.addEvidenceVertex(attr_ID,dep.kAttribute,attr_obj,attr_val)  
            
    # Next, all the potential parents of the exist attributes need to be added to `dep.uncertainRelationship.existParents'        
    
    
    for existdep in dep.uncertainRelationship.existAttribute.dependenciesChild:

        dsi.loadExistParents(dep,existdep)

        # variables for code readability 
        k_entity_pk = dep.kAttribute.erClass.pk
        len_k_entity_pk = len(k_entity_pk)

        parent_pk = existdep.parent.erClass.pk
        len_parent_pk = len(parent_pk)
        end_parent_pk = len_k_entity_pk+len_parent_pk
        
        #  Add initial empty data structure the static ReferenceVertex.existParents


        for row in dsi.resultSet():
            
            #extract object 
            k_entity_obj = row[0:len_k_entity_pk]

            # object id (eg. student.1), note this is not a attribute object id (e.g. student.success.1)
            k_entity_id = computeERID(dep.kAttribute.erClass,k_entity_obj) 

            #extract parent information
            parent_obj = row[len_k_entity_pk:end_parent_pk]
            parent_val = row[-1]
            parent_ID = computeID(existdep.parent,parent_obj) 
                                

            # Add the vertex to the GBN            
            if parent_ID not in GBN:

                if not query.objInEvidence(existdep.parent,parent_ID) : #attr obj not in evidence -> add the queue
                    
                    GBN.addSamplingVertex(parent_ID,existdep.parent,parent_obj)
                    gbnQ.push(GBN[parent_ID])

                elif parent_val is not None:   #attr obj is in evidence -> d-seperates -> not pushed onto queue 

                    GBN.addEvidenceVertex(parent_ID,existdep.parent,parent_obj,parent_val)  
        


            # adding the exist parent information to a static dictionary accessible by all reference vertices

            if k_entity_obj not in ReferenceVertex.existParents:
                ReferenceVertex.existParents[k_entity_id] = {}
            
            if existdep.parent not in ReferenceVertex.existParents[k_entity_id]:
                ReferenceVertex.existParents[k_entity_id][existdep.parent] = {}

            ReferenceVertex.existParents[k_entity_id][existdep.parent][parent_ID] = GBN[parent_ID]






