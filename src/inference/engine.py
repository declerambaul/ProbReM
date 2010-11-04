import inference.mcmc as mcmc

from network.groundBN import GBNGraph,GBNvertex,GBNqueue,computeID

from analytics.performance import time_analysis



class Engine():
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
    def __init__(self,inferenceType):
        
        
        self.GBN = GBNGraph()
        '''Ground Bayesian Network used for inference of type :class:`.GBNGraph`. 
        '''        
                
        
        self.GBNcache = None
        ''' 
        Not implemented. A cache used to reduce redundant computation when unrolling a partial Ground Bayes net 
        '''
        
        
        
        #TODO: ADD OPTION TO SPECIFY A DIFFERENT INFERENCE TYPE
        self.inferenceAlgo = mcmc
        ''' The algorithm used for the approximate inference (e.g. :class:`.MCMC` ) '''
        
        
        self.prm = None
        ''' :class:`.PRM` instance
        '''
        self.di = None
        ''' :class:`.DataInterface` instance
        '''
        
        self.query = None
        ''' Current Query instance of type :class:`.Query` '''

        self.gbnQ = GBNqueue()
        ''' :class:`.GBNqueue` data structure used to unroll the GBN'''
        
    def reset(self):
        """
        Resets the :class:`GBNGraph` and :class:`GBNqueue` instances.
        """
        
        for gbnV in self.GBN.values():
            del gbnV
        del self.GBN
        del self.gbnQ
        self.GBN = GBNGraph()
        self.gbnQ = GBNqueue()
        
    def configure(self,prm,di):
        '''
        Tells the Inference engine which PRM instance and which data interface it should use.
        
        Also, every inference algorithm has to implement a configure() method which takes the PRM
        as an argument. This method can be used to precompute data structures needed for inference.
        
        In the case of the Gibbs sampler, :class:`.MCMC.configure` will precompute all the conditional likelihood
        functions of the attributes with parents. Note that at the time a inference method is configured,
        the PRM should be initialized with proper local distributions (either learned or loaded).
        
        :arg prm: :class:`.PRM` instance
        :arg di: :class:`.DataInterface` instance
        '''
        self.prm = prm #prm 
        self.di = di # data interface   
        
        self.inferenceAlgo.configure(self.prm)    


    def infer(self,query):
        '''
        Runs inference for `query` by 
            
        * Resetting GBN
        * Unrolling GBN
        * Initialize inference algorithm
        * Run inference and collect posterior samples        
        
        :arg query: :class:`.Query` instance        
        '''
        self.query = query
        print 'Inference for: ', self.query
        
        self.reset()
        #unrolling the ground bayes net
        self.unrollGBN()
        print self.GBN
                
        self.inferenceAlgo.init(self.GBN)
        
        self.inferenceAlgo.run()

                
    
    @time_analysis
    def unrollGBN(self):
        '''
        The unrolled Ground Bayesian Network is a subgraph of the
        full graph that d-seperated the event variables `Y`
        from the query from the rest of the graph given the evidence
        variables. 
        
        .. note::
            Add proper description of algorithm
        
        :math:`(GBN_{{\text{d-sep}}} \ci GBN_{{\text{full}}}) \mid \mathbb{E}`
        
        '''
        
        

        # TODO : FIX THE CROSS VALIDATION. WE DON'T WANT TO QUERY K DIFFERENT FOLDS 
        # WHEN UNROLLING. JUST ONE, THE TRAINING SET FOLD
        dsi = self.di.DSI[0]
        #print self.di.trainingSets[self.di.DSI[0]]
        
        #print self.query.event
        # add the inference (event) variables to the GBN 
        for qvar in self.query.event:

            #load all objects in qVariable
            dsi.loadObjects(qvar)
            # result set row : [attribute, pk1 , pk2, ....]
            
            
            #adding all inference vertices for that qVariable to the ground bayes net
            for row in dsi.resultSet():
                
                vertexID = computeID(qvar.attr,row[1:]) 
                #add Vertex
                self.GBN.addVertex(ID=vertexID,attr=qvar.attr,obj=row[1:],fixed=False,event=True)
                
                #add Vertex to the dictionary of event vertices
                self.GBN.eventVertices[vertexID] = self.GBN[vertexID]
                
                #add vertex to the queue of vertices to process
                self.gbnQ.push(self.GBN[vertexID])
                #print 'pushed on queue: ',gbnVertex

                
            
        print 'All %s inference vertices have been added'%(len(self.GBN))
        print self.GBN.values()
  
        # add all the parents of the inference nodes
        while not self.gbnQ.isEmpty():
            (attr,gbnVertices) = self.gbnQ.pop()
            
            #print 'Handling attribute %s with %s gbn vertices'%(attr.fullname,len(gbnVertices))
            
            #filtering the gbn vertices that are part of the evidence

            gbnVerticesNotInE = filter(lambda gbnV: not self.query.gbnVertexInEvidence(gbnV), gbnVertices)
            #print "gbnVerticesNotInE: ",gbnVerticesNotInE
            
            #We load the parents. Note that the parents are also loaded for gbnVertices that are in 
            #the evidence to cover the V-structure effect (explaining away)
            #print 'Loading Parents for %s'%(attr.fullname)
            self.addParents(attr,gbnVertices)            
            
            #we only load the children if the gbnvertex is not in the evidence (if there are any)
            #print 'Loading Children for %s'%(attr.fullname)
            if gbnVerticesNotInE: 
                self.addChildren(attr,gbnVerticesNotInE)
            
            #print 'Done Handling %s'%(attr.fullname)

    def validateGBN(self):
        """
        Validating the GBN is necessary as there might be missing data (either because there is no datapoint or the datapoint is missing from the dataset). The standard approach would be to use an `EM` algorithm to find the `MLE` for the missing data. 
        In order for the inference method to work we need to have valid probability distributions. In case there is a GBN vertex that has no parent vertex but a probability distribution conditional on that parent attribute, one way to avoid invalid GBN structures is to add a sampling vertex. This is only possible (and reasonable) in case this sampling vertex does not depend on parent values itself.
        """
        for attr, gbns in self.GBN.allByAttribute.items():
            if attr.hasParents:
                # in this case all gbn vertices of this attribute should have at least one parent
                for gbnV in gbns:
                    for paAttr in gbnV.parents.keys():
                        if not gbnV.hasParents(paAttr):
                            # if there aren't any parents, a sampling vertex is added.
                            artificial_ID = '%s(%s)'%(paAttr.fullname,gbnV.ID)
                            self.GBN.addSamplingVertex(artificial_ID,paAttr,None)
                            self.GBN[gbnV.ID].addParent(self.GBN[artificial_ID])
                            # print 'adding artificial %s'%artificial_ID  
            
    
    @time_analysis
    def addParents(self,attr,gbnVertices):
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
        dsi = self.di.DSI[0]
        #print self.di.trainingSets[self.di.DSI[0]]
        
        
        # parents for each dependency that the attribute is a child of
        for dep in attr.dependenciesChild: 
                                    
            
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
                
                #HACK HACK HACK
                #only add if the children ID is actually in the GBN. Added this hack because of the limit of 1000 terms in a sqlite statement
                if child_ID in self.GBN:
                                            
                    #only add if not already in GBN
                    if parent_ID not in self.GBN:   
                    
                        #print '%s : adding parent %s (val=%s)'%(child_ID,parent_ID,parent_val)
                    
                    
                            
                        if not self.query.objInEvidence(dep.parent,parent_ID) : #parent obj not in evidence -> add the queue  
                        
                            self.GBN.addSamplingVertex(parent_ID,dep.parent,parent_obj)
                            self.gbnQ.push(self.GBN[parent_ID])                    
                            #Having added the vertex just before, we can for efficiency reasons add the edge to the GBN as we know that it hasn't been there before
                            #adds parent information to child node                    
                            self.GBN[child_ID].parents[self.GBN[parent_ID].attr][parent_ID] =self.GBN[parent_ID] 
                            #adds child information to parent node
                            self.GBN[parent_ID].children[self.GBN[child_ID].attr][child_ID] = self.GBN[child_ID]
                        
                        elif parent_val is not None:   #parent obj is in evidence -> d-seperates -> not pushed onto queue 

                            #add parent vertex to GBN
                            self.GBN.addEvidenceVertex(parent_ID,dep.parent,parent_obj,parent_val)  
                            #Having added the vertex just before, we can for efficiency reasons add the edge to the GBN as we know that it hasn't been there before
                            #adds parent information to child node                    
                            self.GBN[child_ID].parents[self.GBN[parent_ID].attr][parent_ID] =self.GBN[parent_ID] 
                            #adds child information to parent node
                            self.GBN[parent_ID].children[self.GBN[child_ID].attr][child_ID] = self.GBN[child_ID]
                        
                    #parent vertex already in GBN
                    else:    
                        #add parent information to child node
                        self.GBN[child_ID].addParent(self.GBN[parent_ID])  
            
    @time_analysis
    def addChildren(self,attr,gbnVertices):
        '''
        
        Loads the set of children attribute objects for all dependencies for the given GBN vertices of the same attribute class. The BGN is updated and potential new latent variables are added to the queue.
        
        :arg attr: :class:`.Attribute` instance
        :arg gbnVertices: List of :class:`.GBNvertex` instances of type `attr`                
        '''
        
        # TODO : FIX THE CROSS VALIDATION. WE DON'T WANT TO QUERY K DIFFERENT FOLDS 
        # WHEN UNROLLING. JUST ONE, THE TRAINING SET FOLD
        dsi = self.di.DSI[0]
        #print self.di.trainingSets[self.di.DSI[0]]
        
        
        # parents for each dependency that the attribute is a child of
        for dep in attr.dependenciesParent: 
            
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
                
                #HACK HACK HACK
                #only add if the parent ID is actually in the GBN. I add this hack because of the 1000 limit for sqlite
                if parent_ID in self.GBN:
                
                    #only add if not already in GBN                
                    if child_ID not in self.GBN:   
                    
                        #print '%s : adding child %s (val=%s)'%(parent_ID,child_ID,child_val)
                    
                        if not self.query.objInEvidence(dep.child,child_ID):   #children obj is not in evidence                     
                            #add child vertex to the GBN
                            self.GBN.addSamplingVertex(child_ID,dep.child,child_obj)
                        
                            #Having added the vertex just before, we can for efficiency reasons add the edge to the GBN as we know that it hasn't been there before
                            #adds parent information to child node                    
                            self.GBN[child_ID].parents[self.GBN[parent_ID].attr][parent_ID] =self.GBN[parent_ID] 
                            #adds child information to parent node
                            self.GBN[parent_ID].children[self.GBN[child_ID].attr][child_ID] = self.GBN[child_ID]
                        
                            # pushing gbnVertex onto queue (also push vertices that are in the evidence because of possible V-structures)
                            self.gbnQ.push(self.GBN[child_ID])
                        
                        elif child_val is not None:    #children obj is in evidence 

                        
                            #add child vertex to the GBN
                            self.GBN.addEvidenceVertex(child_ID,dep.child,child_obj,child_val)  

                            #Having added the vertex just before, we can for efficiency reasons add the edge to the GBN as we know that it hasn't been there before
                            #adds parent information to child node                    
                            self.GBN[child_ID].parents[self.GBN[parent_ID].attr][parent_ID] =self.GBN[parent_ID] 
                            #adds child information to parent node
                            self.GBN[parent_ID].children[self.GBN[child_ID].attr][child_ID] = self.GBN[child_ID]
                        
                            # pushing gbnVertex onto queue (also push vertices that are in the evidence because of possible V-structures)
                            self.gbnQ.push(self.GBN[child_ID])
                    
                
                    #child vertex already in GBN                    
                    else:    
                        #add parent information to child node
                        self.GBN[child_ID].addParent(self.GBN[parent_ID])  
                        # TODO is this correct? or do we need to push to vertex even if it is already in the gbn? What happens if a vertex is reached from two 'sides' one of which opens a V structre - this means that the vertex is already in the gbn and therefore only the edge is added, even though the V-structure should be loaded
                        #self.gbnQ.push(self.GBN[child_ID])
                                 
                           
            
 
            
