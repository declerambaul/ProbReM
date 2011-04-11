"""
The :mod:`!xml_prm.parser` module contains the parsers that instatiate a :mod:`probrem` instance from the XML specifications. There is parser for

* Data Interface specification, :class:`DataInterfaceParser`
* PRM specifcation, :class:`PRMparser`
* Loading model parameters stored on disk, :class:`LocalDistributionParser`

"""

from prm.relationalschema import Entity, Relationship, UncertainRelationship    
from prm.attribute import * 
from prm.dependency import Dependency, UncertainDependency
from prm.localdistribution import * 
from prm import prm


import data.datainterface as DI
from data.datainterface import datasetinterfaceFactory
from data.datainterface import DataSetInterface
import data.aggregation



import xml.parsers.expat 

import logging

import numpy


'''
Elements defined for PRM specification
'''
prmEl = 'PRM'
prmEl_name = 'name'
prmEl_di = 'datainterface'
rsEl = 'RelationalSchema'
entsEl = 'Entities'
entiEl = 'Entity'
entiEl_name = 'name'
relsEl = 'Relationships'
relEl = 'Relationship'
relEl_name = 'name'
relEl_foreign = 'foreign'
relEl_k = 'k'
relEl_type = 'type'
relEl_description = 'description'
attrEl = 'Attribute'
attrEl_name = 'name'
attrEl_type = 'type'
attrEl_description = 'description'
attrEl_pk = 'pk'
attrEl_hidden = 'hidden'
depstEl = 'DependencyStructure'
depEl = 'Dependency'
depEl_name = 'name'
depEl_parent = 'parent'
depEl_child = 'child'
depEl_constraint = 'constraint'
depEl_agg = 'aggregator'
depEl_refun = 'refun'
locDistsEl = 'LocalDistributions'
locDistEl = 'LocalDistribution'
locDistEl_attr = 'attribute'
locDistEl_file = 'file'
locDistEl_parents = 'parents'

'''
Elements defined for a local distribution specification
'''
tabCPDEl = 'TabularCPD'
tabCPDEl_file = 'file'
treeCPDEl = 'TreeCPD'

'''
Elements defined for a data interface specification
'''
diEl = 'DataInterface'
diEl_name = 'name'
crossValEl = 'Crossvalidation'
dsEl = 'Dataset'
dsEl_type = 'type'
dsEl_path = 'path'

class PRMparser:
    """
    The PRM model is also specified in XML and saved in for example *./PRMexample.xml*::
    
        <?xml version="1.0" ?>
        <PRM name="PRMexample"  datainterface="./DIexample.xml" >
        	<RelationalSchema>
        		<Entities>
        			<Entity name="A">
        				<Attribute name="Aa" type="Binary"/>
        			</Entity>			
        			<Entity name="B">
        				<Attribute name="Ba" type="Integer" description="1,20"/>
        			</Entity>		
                    [......]
        		</Entities>
        		<Relationships>
        			<Relationship name="AB" foreign="A.pk,B.pk" type="1:n">
        				<Attribute name="ABa" type="Binary"/> 
        			</Relationship>				
        			[......]
        		</Relationships>
        	</RelationalSchema>	
        	<DependencyStructure>			
        		<Dependency name="Aa_Ba" child="A.Aa" parent="B.Ba" constraints="A.pk=B.pk"  aggregator='AVG'/>
        		[......]
        	</DependencyStructure>	
        	<LocalDistributions>
        		<LocalDistribution attribute='A.Aa' file='./localdistributions/Da_Aa.xml'/>
        		<LocalDistribution attribute='B.Ba' file='./localdistributions/Ba_Aa.xml'/>
        		<LocalDistribution attribute='AB.ABa' file='./localdistributions/Ca_Aa.xml'/>
        	</LocalDistributions>	
        </PRM>
    
    A list of all imporant xml tags and xml attributes. Note the somewhat confusing double use of the word attributes, on one hand xml attributes and on the other hand the probabilistic PRM :mod:`prm.attribute`.
    
    **PRM**
        
        * `name` : Freely chosen name for PRM model
        * `datainterface` : relative path to the data interface specification, optional
    
    **Entity**
        
        * `name` : The name has to correspond with the corresponding table name in the relational database
    
    **Relationship**
        
        * `name` : The name has to correspond with the corresponding table name in the relational database
        * `foreign` : A list, separated by a coma, of the foreign keys of the relationship. The foreign attributes can be probabilistic, but usually the primary key of an entity serves as foreign key. The primary key of an entity can be defined as probilistic attribute, but this entails that the domain is all the entries in one database table. This doesn't scale well at all, but sometimes this can be desired behavior. In case the foreign key is not probabilistic and thus most likely a primary key, the special keyword `pk` can be used to refer to a primary key of an entity. The `pk` keyword defaults to `entityname_id` as the name of the primary key. Thus if there is a table `Professor`, `Professor.pk' would refer `Professor.professor_id`.
        * `type` :  This is only used in the context of reference uncertainty. A relationship can be of type `k:n`,`n:k`. 
        * `k` : A fixed parameter indicating an uncertain relationship (i.e. reference uncertainty) of type `n:k`.
    
    **Attribute**
        
        * `name` : The name has to be correspond to the data field in the relational database. Also, it has to be unique among the attributes of the entity/relationship it is part of. 
        * `type` : The type must be either 
            
            * `Binary`, instantiates an attribute of type :class:`~!.prm.attribute.BinaryAttribute`
            * `Integer`, instantiates an attribute of type :class:`~!.prm.attribute.IntegerAttribute`
            * `Enumerated`, instantiates an attribute of type :class:`~!.prm.attribute.EnumeratedAttribute`
            * `NotProbabilisticAttribute`, instantiates an attribute of type :class:`~!.prm.attribute.NotProbabilisticAttribute`
            
        * `description` : Specifies the domain of the attribute
        
            * For `Binary` not required
            * For `Integer`, e.g. "1,5" results in [1,2,3,4,5] (including 5)
            * For `Enumerated`, coma separated list of domain, e.g. "1,4,78" results in [1,4,78]
            * For `NotProbabilisticAttribute` not required
            
        * `pk` : Optional. If you choose to use the primary key, set pk="1". Note the remark in the `Relationship` tag for more information
    
    **Dependency**
        
        * `name` : Freely chosen name for probabilistic dependency
        * `parent` : Parent attribute, referenced by its full name. e.g. `Professor.fame`
        * `child` : Child attribute, referenced by its full name. e.g. `Student.success`
        * `constraint` : Optional. A coma separated list of constraints that can be applied to the data interface. Most commonly used are normal slotchains, e.g. "Professor.pk=Advisor.professor_id,Advisor.student_id=Student.pk". If no constraint is given, ProbReM will apply a depth-first-search to find a slot chain from child to parent using :meth:`.computeSlotChain`
        * `aggregator` : If the constraint on the dependency leads to one child attribute object having multiple parent attribute objects, the values of the parent attribute objects have to be aggregated as the CPD for the child allows only one value for that parent. The module :mod:`.aggregation` implements different such methods, e.g. `AVG`, `MAX`, `MIN`, `MODE`
        * `refun` : Indicator if the dependency has an uncertain relationship in the slotchain ('1','True' or 'T')
    
    **LocalDistribution**
        See :class:`LocalDistributionParser`
    """
    
    def __init__(self):
        '''
        See the documentation for the prm class
        '''        
        self.entities = {}
        self.relationships = {}
        self.attributes_temp = {}
        self.dependencies = {}
        self.attributes = {} 
        
        #temp variables
        self.currentER = None # we keep track of the currently handled entity/relationship because we attach the attributes (attributes_temp) at the end 
        self.names = [] #we only allow unique names (makes things easier and is not unreasonable given that a person designs the prm specification for now)
        self.foreign = []
        
        
        ''' We need a different parser for parsing local distributions which have been specified '''
        self.localDistParser = LocalDistributionParser()   
        
        
        
                  
    
    def start_element(self,name, attrs):
        ''' 
        Encountered a starting tag of an element. Instances of entities, relationships, attributes
        and dependencies are created.
        '''
        
        ''' Avoid duplicate names for all elements  (Specifications should not become too big for now)'''
        if 'name' in attrs:
            if attrs['name'] in self.names:
                raise Exception('Error in PRM spec (duplicate name):%s'%attrs['name'])
            else:
                self.names.append(attrs['name'])
                
        ''' Set PRM name '''
        if name==prmEl:
            self.prmName = attrs[prmEl_name]
            self.di = None
            if prmEl_di in attrs: 
                self.di = attrs[prmEl_di]
            
        ''' Create Entity class '''
        if name==entiEl:
            self.currentER = Entity(attrs[entiEl_name])
            self.entities[attrs[entiEl_name]] = self.currentER 
        
        ''' Create Relationship class '''
        if name==relEl:
            # see comment in end_element handler for a relationship.
            self.foreign = attrs[relEl_foreign]

            # Reference Uncertainty introduces uncertain relationships
            if relEl_type in attrs: 

                nTok = None
                reltype = attrs[relEl_type]
                if reltype == 'n:k':
                    nTok = True
                elif reltype == 'k:n':
                    nTok = False
                else:
                    raise Exception('Relationship type (`k:n` or `n:k`)')

                # k in `n:k`                
                k = 1
                if relEl_k in attrs:
                    k = attrs[relEl_k]


                self.currentER = UncertainRelationship(name = attrs[relEl_name], nTok = nTok, k = k )
            else:                            
                self.currentER = Relationship( name = attrs[relEl_name] )

            self.relationships[attrs[relEl_name]] = self.currentER 
        
        ''' Create Attribute class '''
        if name==attrEl: 
            name = attrs[attrEl_name]
            er = self.currentER
            atype = attrs[attrEl_type]
                                    
            attrDef = None       
            if attrEl_description in attrs: 
                attrDef = attrs[attrEl_description]      
                          
            attribute = attributeFactory(name, er , atype, attrDef )            
            
            # Adding the new attribute object to data structures
            self.attributes_temp[attribute.fullname] = attribute
            self.attributes[attribute.fullname] = attribute
            
            #primary key if defined in xml specification
            if attrEl_pk in attrs: 
                pk = attrs[attrEl_pk]
                if pk=="1" or pk=="T" or pk=="True":
                    self.currentER.pk.append(attribute)      
                    
            
        ''' Create a dependency class '''
        if name==depEl:
            #parent must either be an entity or relationship attribute
            
            name = attrs[depEl_name]
            parent = self.attributes[attrs[depEl_parent]]
            child = self.attributes[attrs[depEl_child]]
            aggr = None 
            if depEl_agg in attrs:                
                aggr = data.aggregation.aggregators[attrs[depEl_agg]]
            constraint = None
            if depEl_constraint in attrs:
                constraint=attrs[depEl_constraint]

            refun = False
            if depEl_refun in attrs:
                refunS = attrs[depEl_refun]
                if refunS=="1" or refunS=="T" or refunS=="True":
                    refun = True
                
            
                  
            if refun:
                self.dependencies[name] = UncertainDependency(name=name, parent=parent, child=child, constraint=constraint,aggregator=aggr,attributes=self.attributes)

                # The slotchain has been defined, we can now determine wheter there is reference uncertainty in
                # that dependency. If the dependency starts or ends with an uncertain relationship it is not 
                # reference uncertainty             

                # Find what direction the slotchain points
                childFirst = False
                if self.dependencies[name].child.erClass == self.dependencies[name].slotchain[0]:
                    childFirst = True

                
                
                # logging.debug(self.dependencies[name].slotchain)


                
                for er in self.dependencies[name].slotchain[1:-1]:
                    if er.isUncertainRelationship():                
                        # extracting uncertain relationship
                        self.dependencies[name].uncertainRelationship = er

                # determining the direction of the uncertain relationship                        
                if self.dependencies[name].uncertainRelationship.nTok:
                    self.dependencies[name].nAttribute = self.dependencies[name].child
                    self.dependencies[name].kAttribute = self.dependencies[name].parent
                    self.dependencies[name].nIsParent = False

                else: # = k:n
                    self.dependencies[name].nAttribute = self.dependencies[name].parent
                    self.dependencies[name].kAttribute = self.dependencies[name].child
                    self.dependencies[name].nIsParent = True

                        

            else:
                self.dependencies[name] = Dependency(name=name, parent=parent, child=child, constraint=constraint,aggregator=aggr, attributes=self.attributes)
                                    
            

            #we add information about the dependencies to the child/parent attributes            
            child.dependenciesChild.append(self.dependencies[name])            
            parent.dependenciesParent.append(self.dependencies[name])          
                      
            #we update the attribute.parents list of all of the child attribute for the given dependency
            child.parents.append(parent)


        
        ''' Loading the local distributions where they are available '''        
        if name==locDistEl:
            attribute = self.attributes[attrs[locDistEl_attr]]
            distFile = attrs[locDistEl_file]
            #Parsing the local distribution for attribute from the file distFile
            self.localDistParser.parseLocalDistribution(attribute, distFile)
            
            
            
            
            
    def end_element(self,name):
        ''' 
        This method is a handler that is called if the parser encounters an tag that ends 
        an element block.  When we encounter a entity or relationship block, we attach the 
        attributes to the entity or relationship and reset attributes_temp for the next block
        '''                                            
        
        if name==entiEl:
            '''
            The primary key of an entity or relationship class can be implicit. It's name is 
            'entityname_id' and it is non-probabilistic. At this point, when 
            all the attributes have been instantiated, we check whether the implicit integer primary 
            key has been overwritten (for example to make a probabilistic id attribute). The attribute
            is overwritten by specifying an attribute with  pk='1' in the the xml representation.   
            '''
            
            if self.currentER.pk == []:
                
                attr_name = self.currentER.name.lower()+'_id'
                attribute = attributeFactory( name=attr_name, er=self.currentER , type='NotProbabilistic', attrDef=None)
                self.attributes_temp[attribute.fullname] = attribute
                self.attributes[attribute.fullname] = attribute
                self.currentER.pk.append(attribute)
            
            self.currentER.pk_string = [self.currentER.pk[0].fullname]    
            # assigning all attributes and resetting the temp dict for the attributes
            self.currentER.attributes = self.attributes_temp
            self.attributes_temp = {}
        
        if name==relEl:
            '''
            A relationship class has a primary key stored in self.pk that can consist of a set of foreign keys that are attributes of the connecting entities (usually their primary key attributes). The primary key can also be a simple attribute. It is very important that the primary key is unique as it will be used to identify individual nodes of the ground Bayesian network. 
            The foreignkeys are defined in the xml-attribute 'foreign="E1.a1,E2.a2,.."' where Ex.ax can also be Ex.pk in which case the primary key of Ex is chosen. The fk set is are instances of Foreign Attribute stored
                -as a list of fa in self.pk
                -as a list of fa.fullname in self.pk_string
                -as a dict {key=Entity: foreignattribute}
            
            At this point all names must be unique, therefore the attribute name contains all information. We can only configure this after we instantiated all attributes (= when closing the relationship tag).            
            '''
            
            # Is there an attribute defined to be the primary key we don't take the set of foreign keys as primary key
            pk_defined = False
            if len(self.currentER.pk) > 0:
                pk_defined = True
            
            # e.g. 'User.user_id:buyer_id,User.user_id:seller_id' where the first part identifies the attribute and the second is an optional alias name
            self.foreign = [fk.split(':') for fk in self.foreign.split(',')]            
            
            for rpk in self.foreign:
                #add foreign key for the relationship primary key is always defined
                fk = rpk[0]
                #an alias is only defined if the relationship primary key name is different from the foreign key name
                # (entity,attribute) , e.g. User.item_id or User.pk
                (ent,a) = fk.split('.')
                #Entity instance
                entI = self.entities[ent]
                #Foreign Attribute to be instanciated
                fa = None
                #Target Attribute (=Foreign Key)
                ta = None
                if a == attrEl_pk: #use primary key of ent                                                                                
                    ta = entI.pk[0]
                                        
                else:  #a is the name of the attribute in entity ent                    
                    ta = entI.attributes[fk]
                    #create Foreign Attribute                    
                                
                #an alias is only defined if the relationship primary key name is different from the foreign key name
                alias = ta.name
                if len(rpk)==2:
                    alias = rpk[1]
                     
                #create Foreign Attribute
                fa = ForeignAttribute(name=alias,target=ta,er=self.currentER) 
                #adding fa to dict of attributes
                self.attributes[fa.fullname] = fa
                #adding fa to self.pk of relationship instance not already defined
                if not pk_defined:   
                    self.currentER.pk.append(fa)    
                    
                #adding fa to foreign dict (entity:[foreignattribute])
                if entI not in self.currentER.foreign:
                    self.currentER.foreign[entI] = [fa]
                else:
                    self.currentER.foreign[entI].append(fa)
                
                #adding relationship reference to the dict of the connected entities
                entI.relationships[self.currentER.name] = self.currentER
            
            #list of the names of the foreign keys of the relationship
            self.currentER.pk_string = ['%s'%(pk_i.fullname) for pk_i in self.currentER.pk]
            #list of entities associated with the current relationship    
            self.currentER.entities = self.currentER.foreign.keys()
            
            # Reference Uncertainty
            if self.currentER.isUncertainRelationship():
                logging.debug("TODO: UPDATE DOCUMENTATION FOR REFERENCE UNCERTAINTY")
                # Creating the exist attribute for the uncertain relationship
                ex = ExistAttribute(name='exist',er=self.currentER)
                # Adding ex to dict of attributes
                self.attributes[ex.fullname] = ex                
                self.attributes_temp[ex.fullname] = ex
                self.currentER.existAttribute = ex

                # self.foreign is the list of foreign attributes has 2 entries in this case,
                # if the relationship is of type `n:k`, the first one refers to the 
                # n attribute, the second to the k attribute

                foreignEntities = [None, None]
                for i,rpk in enumerate(self.foreign):
                    # rpk = [ pk_name , alias_name ]
                    fk = rpk[0]                    
                    # (entity,attribute) , e.g. User.item_id or User.pk
                    (ent,a) = fk.split('.')
                    entI = self.entities[ent]
                                                                                     
                    foreignEntities[i] = entI


                if self.currentER.nTok:
                    self.currentER.nEnitity = foreignEntities[0]
                    self.currentER.kEnitity = foreignEntities[1]
                else: # = k:n
                    self.currentER.nEnitity = foreignEntities[1]
                    self.currentER.kEnitity = foreignEntities[0]        
                        
                    
                
            
                                                    
            # assigning all attributes and resetting the temp dict for the attributes
            self.currentER.attributes = self.attributes_temp
            self.attributes_temp = {}
  
    
    def parsePRM(self,xmlfile):
        ''' 
        Parse given PRM specification passed as 'xmlfile'. The parser will create all Entity, 
        Relationship,Attribute and Dependency instances. Finally it will return a fully defined PRM
        instance
        '''
        
        ''' 
        The expat parser which will be used. We create a new expat parser for every file that we
        handle because ParseFile(f) can't be called more than once apparently        
        '''        
        prmParser = xml.parsers.expat.ParserCreate()        
        prmParser.StartElementHandler = self.start_element
        prmParser.EndElementHandler = self.end_element
                
        ''' Parse given PRM specification '''
        prmParser.ParseFile(open(xmlfile)) 
        
                
        ''' We display a list of attributes that have no CPD after parsin. These distributions will have to be learned from data'''
        noCPD = [attr.fullname for attr in self.attributes.values() if attr.CPD is None and attr.probabilistic]
        if noCPD != []:            
            logging.info('Local Distribution(s) missing for:'," ".join(noCPD))
        
            
        ''' Finally we instantiate the Probabilistic Relational Model and return it '''
        prm.name = self.prmName
        prm.entities = self.entities

        prm.relationships = self.relationships

        prm.attributes = self.attributes

        prm.dependencies = self.dependencies

        prm.datainterface = self.di

        prm.topoSortAttributes = topologicalSort([a for a in self.attributes.values() if a.probabilistic])
        
                
        
    


    
class LocalDistributionParser:
    '''    
    The local distribution parser loads a the model parameters that have been saved to disk. Naturally this can only be done if the probabilistic structure and also the data itself have not changed. :meth:`learners.cpdlearners.CPDTabularLearner.learnCPDsFull` can be called with the `saveDistributions=True`. The required XML specification along with the .nlp (numpy.array format) is saved in `./localdistributions/xxx.xml` and the required XML will be printed to the standard output, e.g. ::
        
        <LocalDistribution attribute='A.Aa' file='./localdistributions/Da_Aa.xml'/>
        
    After adding that output to the `<LocalDistributions>` tag in the PRM specification, the next time the model is loaded - granted that the structure is the same - the local distribution will be loaded from disk.
    '''
    def __init__(self):
        
        ''' The attribute that we parse the distribution for '''
        self.attribute = None
        
        ''' Dictionary that maps the xml elements to the method that handles them'''
        self.elementsMappings = {locDistEl:self.localDist, 
                                 tabCPDEl : self.tabCPD, 
                                 treeCPDEl : self.treeCPD}
        
        
        '''
        Temporary storage for attributes that are passed with an element
        Note the possible confusion with the word attribute: The prm defines
        attributes (self.attribute) that we learn distribtions for, and the arguments
        passed with an xml starting tag are also called attributes (self.attrs)        
        '''
        self.attrs = None
        
    def start_element(self,name, attrs):
        
        # store the attributes of the element so that all methods can access them
        self.attrs = attrs
        
        self.elementsMappings[name]()
    
    def localDist(self):
        ''' Create CPD for '''
        #raise exception if the name of attribute specified in the file doesn't match the one passed by the parser
        if self.attribute.fullname != self.attrs[locDistEl_attr]:
            raise Exception("Local Distribution attribute names don't match: %s!=%s"%(self.attribute.name,self.attrs[locDistEl_attr]))
        
        
    def tabCPD(self):
        
        cpdfile = self.attrs[tabCPDEl_file]
        
        self.attribute.CPD = CPDTabular(self.attribute)
        
        '''
        Note: the cpdMatrix is overwritten. The only thing that is 
        checked is whether the dimensions of the matrices match.
        
        If the order of the parent assignments is different in the
        prm than in the file, the cpd will be false. Note that if 
        you load a prm, the parent ordering in the attribute.parents
        list will always be the same as long as the xml specification
        of the prm is not changed.         
        
        '''
        cpdM = numpy.load(cpdfile)    
                
        
        if cpdM.shape == self.attribute.CPD.cpdMatrix.shape:                   
            self.attribute.CPD.cpdMatrix = cpdM
        else:
            logging.debug("WARNING: Matrix dimensions of loaded CPD  %s don't match (%s vs %s)"%(cpdfile,cpdM.shape,self.attribute.CPD.cpdMatrix.shape))
            raise Exception("Matrix dimensions of loaded CPD  %s don't match"%cpdfile)
        
        #calculating the cumulative distribution
        self.attribute.CPD.computeCumulativeDist()
        self.attribute.CPD.computeLogDists()
        
             
        
        
    def treeCPD(self):
        raise Exception('TreeCPDs are not implemented yet') 
    
    def end_element(self,name):
        ''' Nothing needs to be done when we encounter an end tag of an element'''
        pass
    
    def parseLocalDistribution(self,attr,distFile):
        
        
        self.attribute = attr
        
        # we create a new expat parser for every file that we handle because ParseFile(f) can't be called more than once apparently
        localDistParser = xml.parsers.expat.ParserCreate()
        localDistParser.StartElementHandler = self.start_element
        localDistParser.EndElementHandler = self.end_element
        
        
        try:
            localDistParser.ParseFile(open(distFile)) 
        except:            
            logging.debug('ERROR: Local distribution %s could not be loaded.'%distFile)
            #raise Exception('ERROR: Local distribution %s could not be loaded.'%distFile)
        
class DataInterfaceParser: 
    '''    
    The data interface is specified in XML and saved in for example *./DIexample.xml*::
    
        <?xml version="1.0" ?>
        <DataInterface name="DIexample">
            <Crossvalidation folds='1'>
                    <Dataset type='SQLite' path='./data/database.sqlite'/>
            </Crossvalidation>
        </DataInterface>
    
    A list of all imporant xml tags and xml attributes. Note the somewhat confusing double use of the word attributes, on one hand xml attributes and on the other hand the probabilistic PRM :mod:`prm.attribute`.
    
    **DataInterface**
        
        * `name` : Freely chosen name for PRM model
    
    **Crossvalidation**
        
        * `folds` : Number of folds used for cross validation. The data has to be split up on the database level, otherwise the different folds would have to be accessed by querying one database which decreases the performance. This feature has not been tested, if no cross validation is desired, just use `folds="1"`
    
    **Dataset**
        
        * `type` : Type of database the interface is connecting to. Currently only `SQLite` is supported, :class:`SQLiteDI`.
        * `path` : The path to the database file
    
    '''
    def __init__(self):
        
        ''' Dictionary that maps the xml elements to the method that handles them'''
        self.elementsMappings = {diEl:self.datainterface, 
                                 crossValEl : self.crossvalidation, 
                                 diEl+'_end': self.createDI,
                                 dsEl : self.dataset                                 
                                 }
        
        ''' global variables
        diEl = 'DataInterface'
        diEl_name = 'name'
        crossValEl = 'Crossvalidation'
        dsEl = 'Dataset'
        dsEl_type = 'type'
        dsEl_path = 'path'
        '''
        
        # the instance of the datainterface
        self.diI = None
        self.name = 'Unamed_DI'
        self.ditype = 'Unamed_Type'
        # the datasets associated with the datainterface
        self.DSI = []
        
        
        '''
        Temporary storage for attributes that are passed with an element
        Note the possible confusion with the word attribute: The prm defines
        attributes that we learn distribtions for, and the arguments
        passed with an xml starting tag are also called attributes (self.attrs)        
        '''
        self.attrs = None
        
    def start_element(self,name, attrs):
        '''Excecuted if the parser encounters an start tag for an element'''
        # store the attributes of the element so that all methods can access them
        self.attrs = attrs
        if name in self.elementsMappings:
            self.elementsMappings[name]()
    
        
    def datainterface(self):
        if diEl_name in self.attrs:
            self.name = self.attrs[diEl_name]
            
    def crossvalidation(self):
        self.ditype = 'CrossValidation'                
        
    def dataset(self):
        path = self.attrs[dsEl_path]
        ditype = self.attrs[dsEl_type]
        dsi = datasetinterfaceFactory(path,ditype)
        
        self.DSI.append(dsi)
            
    def createDI(self):
        '''All information about the datasets has been collected and stored in self.DSI (datasetinterface), 
        the module :mod:`.datainterface` can now be initializded'''
        
        DI.name = self.name
        DI.ditype = self.ditype
        DI.DSI = self.DSI
        DI.computeTrainingSets()
        
    
    def end_element(self,name):
        '''Excecuted if the parser encounters an end tag for an element'''
        com = name+'_end' 
        if com in self.elementsMappings:
            self.elementsMappings[com]()
    
    def parseDataInterface(self,diFile):
        
        # we create a new expat parser for every file that we handle because ParseFile(f) can't be called more than once apparently
        diParser = xml.parsers.expat.ParserCreate()
        diParser.StartElementHandler = self.start_element
        diParser.EndElementHandler = self.end_element
        
        diParser.ParseFile(open(diFile)) 
        
        return self.diI
        
       