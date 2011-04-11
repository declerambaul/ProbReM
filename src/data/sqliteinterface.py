'''
The class :class:`~!.DataSetInterface` specifies a set of methods that are need to be implemented by a database specific data interface. Currently the framework supports only `SQLite <www.sqlite.org>`_ which is implemented in :class:`data.sqliteinterface.SQLiteDI`. Implementing support for other SQL based database systems, e.g. MySQL, should be straight forward. Support for other database systems would require more effort.
'''

import logging

import sqlite3 
from itertools import repeat

from analytics.performance import time_analysis


from data.datainterface import DataSetInterface



class SQLiteDI(DataSetInterface):
    '''
    A subclass of :class:`.DataSetInterface` that links a PRM to the SQLite database that it models. 
    '''
    def __init__(self,path):
        '''
        Connection to SQLite database is created         
        '''  
        
        DataSetInterface.__init__(self, 'SQLite')
        
        self.path = path
        """Path to SQLite DB file"""
        
             
        try:
            self.con = sqlite3.connect(self.path) # make connection
            self.con.isolation_level = None 
            
            #self.con.row_factory = sqlite3.Row # tuples in result set will be Row objects
            self.cur = self.con.cursor() 
            """SQLite cursor that will execute SQL commands and contain the result set
            """
            
        except sqlite3.Error, e:            
            logging.debug("An error occurred:", e.args[0])
     
     
    def loadCountCPDdata(self, attribute):
        '''
        We pass an `attribute`, and constructe a query such that the result set `self.cur` contains all the 
        data to learn the local distribution of that `attribute`. The `Count` in the name 
        indicates that the query is constructed such that the compuation is done on the SQL side, 
        e.g. the number of occurences for each possible parent assignment is counted using `COUNT`. This function 
        is used by :meth:`learners.cpdlearners.CPDTabularLearner.learnCPDsCount`.        
        
        :arg attribute: Subclass of :class:`prm.attribute.Attribute`
        '''
        sqlQuery = ''
        if len(attribute.parents)==0:
            sqlQuery = 'SELECT COUNT(*) FROM %s GROUP BY %s;'%(attribute.erClass.name,attribute.fullname)
            
        else:
            sqlAttributes = [attribute.fullname]
            sqlTables = [attribute.erClass.name]

            sqlWhere = []
        
            for dep in attribute.dependenciesChild:
                if dep.aggregator is None:
                    #attribute
                    sqlAttributes.append(dep.parent.fullname)
                    #tables
                    for er in dep.slotchain:
                        if er.name not in sqlTables:
                            sqlTables.append(er.name)
                
                    sqlWhere.extend(dep.slotchain_attr_string)
                
                else:
                    # We created a VIEW to aggregate the parent values
                    vName = dep.name   #'%s_%s'%(dep.parent.name,attribute.name)
                    sqlAttributes.append('AGG_%s'%(dep.parent.name))
                    sqlTables.append(vName)                
                    sqlWhere.extend(['%s.%s=%s'%(vName,pki.name,pki.fullname) for pki in attribute.erClass.pk])

            # string representation of the sql lists   
            sqlAttributes =  ",".join(sqlAttributes)
            sqlTables = ",".join(sqlTables)
            sqlWhere = " AND ".join(sqlWhere)
                
            sqlQuery = 'SELECT COUNT(*) FROM %s WHERE %s GROUP BY %s;'%(sqlTables,sqlWhere,sqlAttributes)
            
        '''
        We execute the query and return the result set with the ordering of the queried 
        attributes
        '''        
        #logging.debug(sqlQuery)
        self.cur.execute(sqlQuery)


            
    def loadFullAggCPDdata(self, attribute):
        '''
        We pass an `attribute`, and constructe a query such that the result set `self.cur` contains all the 
        data to learn the local distribution of that `attribute`. The `Full` in the name indicates that we don't 
        `COUNT` all occurences in the query but in the learner instead. The `Agg` indicates that if the `attribute` 
        has multiple parents for one attribute object, we use `VIEWS` to aggregate the data using SQL. 
        
        In practice this has proven to not be a good way to do things. First, it is much slower than the other methods.
        Second, by aggregating the values before counting them the number of occurences per parent assignment is much 
        smaller. On the other hand, by not aggregating them we introduce a bias in which attribute objects with many parent
        attribute objects for on parent attribute are weighted more. Thus this methods is currently not used.
        
        This method is currently only used to compute the log likelihood of the model given the data using :meth:`learners.cpdlearners.CPDTabularLearner.loglikelihood`.
        
        :arg attribute: Subclass of :class:`prm.attribute.Attribute`
        '''


        '''
        create a list of attributes that defines what variables to query
        and the order in which they will be returned
        '''
        attributes = []
        attributes.append(attribute.fullname)
        
        ''' 
        if the attribute has aggregation parents we aggregate
        '''
        for dep in attribute.dependenciesChild:
            if dep.aggregator is None:
                attributes.append(dep.parent.fullname)
            else: 
                attributes.append('ROUND(%s( %s))'%(dep.aggregator(self.dsiType),dep.parent.fullname))
        '''
        create a string representation for the sql query
        '''
        # string list of attributes   
        sqlAttributes =  ",".join(attributes)

        #Using the slotchain(s) for the dependency(ies) of the given the given attribute we can construct the string list of tables        
        merged = [attribute.erClass]
        for dep in attribute.dependenciesChild:
            for er in dep.slotchain:
                if er not in merged:
                    merged.append(er)

        sqlTables = ",".join([er.name for er in merged])

        # Again we use the slotchain information of the dependencies to create the string list of where clause
        scWhere = []
        for dep in attribute.dependenciesChild:

            scWhere.extend(dep.slotchain_attr_string)  

        sqlWhere = " AND ".join(scWhere)
        
        sqlGroupBy = ','.join(attribute.erClass.pk_string)

        if sqlWhere =='':
            sqlQuery = 'SELECT %s FROM %s GROUP BY %s;'%(sqlAttributes,sqlTables,sqlGroupBy)
        else:
            sqlQuery = 'SELECT %s FROM %s WHERE %s GROUP BY %s;'%(sqlAttributes,sqlTables,sqlWhere,sqlGroupBy)


        '''
        We execute the query and return the result set with the ordering of the queried 
        attributes
        '''        
        #logging.debug(sqlQuery)
        self.cur.execute(sqlQuery)


            
    def loadFullCPDdata(self, attribute):
        '''
        We pass an `attribute`, and constructe a query such that the result set `self.cur` contains all the 
        data to learn the local distribution of that `attribute`. The `Full` in the name indicates that we don't 
        `COUNT` all occurences in the query but in the learner instead. This method is used by :meth:`learners.cpdlearners.CPDTabularLearner.learnCPDsFull`.
        
        :arg attribute: Subclass of :class:`prm.attribute.Attribute`
        '''
        
                                
        '''
        create a list of attributes that defines what variables to query
        and the order in which they will be returned
        '''
        attributes = []
        attributes.append(attribute)
        attributes.extend(attribute.parents)
        
        '''
        create a string representation for the sql query
        '''
        # string list of attributes   
        #sqlAttributes =  ",".join([a.name for a in attr])
        sqlAttributes =  ",".join([a.fullname for a in attributes])
        
        #Using the slotchain(s) for the dependency(ies) of the given the given attribute we can construct the string list of tables        
        merged = [attribute.erClass]
        for dep in attribute.dependenciesChild:
            for er in dep.slotchain:
                if er not in merged:
                    merged.append(er)
        
        sqlTables = ",".join([er.name for er in merged])
         
        # Again we use the slotchain information of the dependencies to create the string list of where clause
        scWhere = []
        for dep in attribute.dependenciesChild:
            
            scWhere.extend(dep.slotchain_attr_string)  
            
        sqlWhere = " AND ".join(scWhere)
        
        sqlNull = ' AND '.join(['%s IS NOT NULL'%a.fullname for a in attributes])
        
        if sqlWhere =='':
            sqlQuery = 'SELECT %s FROM %s WHERE %s;'%(sqlAttributes,sqlTables,sqlNull)
        else:
            sqlQuery = 'SELECT %s FROM %s WHERE %s AND %s;'%(sqlAttributes,sqlTables,sqlNull,sqlWhere)
        

        '''
        We execute the query and return the result set with the ordering of the queried 
        attributes
        '''        
        #logging.debug(sqlQuery)
        self.cur.execute(sqlQuery)        
                
    #@time_analysis
    def loadObjects(self, qvar):
        '''
        When unrolling a Ground Bayes Net the inference engine :mod:`inference.engine` processes a set of 
        event and evidence variables that are of type :class:`inference.query.Qvariable`. 
        The method `self.loadObjects()` executes 
        a SQL query that returns the set of all attribute objects that satisfy the constraints of `qvar`
        
        The result set will have the following structure : [attribute, pk1 , pk2, ....], e.g.
        
            * If qvar.erClass is `User` : [User.gender, User.user_id]            
            * If qvar.erClass is `rates` : [rates.rating, rates.user_id,rates.item_id]
        
        :arg qvar: :class:`inference.query.Qvariable`
        '''
        
        sqlAttribute = '%s,%s'%(qvar.attr.fullname,",".join( [pk.fullname for pk in qvar.erClass.pk ] ))
        #sqlAttribute = qvar.attr.fullname
        
        # We are only loading data from one table
        sqlTable = qvar.erClass.name
                
        # The where clause is defined by the qvar.objs, the primary key(s) of of the erClass
        '''
        qbvar.objs.pkValues = [(pk1Val,pk2Val,..),(pk1Val,pk2Val,..),(pk1Val,pk2Val,..),.....]
        attr.erClass.pk = [pk1,pk2,...]
        
        sqlWhere = 
        
        
        
        '''
        query_where = [' AND '.join(['%s=%s'%(pk.fullname,pkVal) for (pk,pkVal) in zip(pks,pksValue)]) for (pks, pksValue) in zip(repeat(qvar.attr.erClass.pk), qvar.objs.pkValues)]
        query_where = ['(%s)'%pkStr for pkStr in query_where]
        
        sqlWhere = ' OR '.join(query_where)        
                                        
        '''
        sqlWhere = ''
        if qvar.erClass.isEntity():
            sqlWhere = " AND ".join(map( lambda (a,val): '%s=%s'%(a.fullname,val), qvar.obj.items() ))
        else:
            sqlWhere = " AND ".join(map( lambda (a,val): '%s=%s'%(a.fullname,val), qvar.obj.items() ))
        '''
                
                        
        if sqlWhere =='':
            sqlQuery = 'SELECT %s FROM %s;'%(sqlAttribute,sqlTable)
        else:
            sqlQuery = 'SELECT %s FROM %s WHERE %s;'%(sqlAttribute,sqlTable,sqlWhere)
        
        #logging.debug(sqlQuery)
        
        self.cur.execute(sqlQuery)
        
    
    def loadDependencyParentObjects(self, dep, gbnVertices):
        """
        Given a set of children attribute objects `gbnVertices` for a given dependency `dep`, we are loading the set of parents.
        
        The result set will consist of rows in the following format:
        
        |   dep_child.pk1,dep_child.pk2,..., dep_parent.obj,dep_parent.val
        |   <   child indentification      > <          parent         > 
        
        
        :arg dep: :class:`prm.dependency.Dependency`
        :arg gbnVertices: A list of :class:`network.groundBN.GBNvertex`
        """
        
        '''
        Aggregation on the data level doesn't work well, legacy comment:
        
        sqlAttr : dep_child.pk1,dep_child.pk2,..., dep_parent.obj,dep_parent.val
                  <   child indentification      > <          parent         > 
              
                  if dependency of type 1:1 or n:1 ( ==  no aggregation)
                        ->  dep_parent.obj = dep_parent.pk1,dep_parent.pk2,...
                            dep_parent.val = dep_parent.val
                  if dependency of type n:1 or m:n ( ==  aggregation)
                        ->  dep_parent.obj not necessary (ID of vertex will be dep_name.dep_child.obj
                        ->  dep_parent.val = AGGREGATION(dep_parent.values)
        
        '''                                  
        # attributes list
        query_attrs = []
        query_attrs.extend(dep.child.erClass.pk_string) # to identify the child vertex     
        # table list
        query_tables = []
        query_tables.extend(dep.slotchain_string)
        # where list
        query_where = []
        query_where.extend(dep.slotchain_attr_string)
        '''
        We are not using the views for aggregation:
        
        with view it is painfully slow
        SELECT User.user_id,AGG_rating FROM User,rating_gender WHERE User.user_id=rating_gender.user_id AND (User.user_id=900);
        
        this is much much faster
        SELECT User.user_id,AVG(rates.rating) FROM User,rates WHERE User.user_id=rates.user_id AND (User.user_id=900);
        
        '''
        
        '''
        TODO : CAN ONE EVEN USE AGGREGATED VERTICES? YOU WOULD HAVE TO GUARANTEE THAT NO OTHER VERTEX EVER NEEDS TO 
               SAMPLE FROM ONE OF THE COLLAPSED AGGREGATED VERTICES
               see engine.py  for same problem
               
        # add parent attributes to query_attrs list
        if dep.aggregator is None: # n:1 or 1:1 dependency type 
            #attributes
            query_attrs.extend(dep.parent.erClass.pk_string) #identify the parent obj
            query_attrs.append(dep.parent.fullname) # the parent value
                  
        else: # aggregation 1:n or m:n dependency type
            query_attrs.append('%s(%s)'%(dep.aggregator(self.dsiType),dep.parent.fullname)) #aggregated parent value                    
        '''
        # FOR NOW WE JUST ADD ALL VERTICES
        # add parent attributes to query_attrs list
        query_attrs.extend(dep.parent.erClass.pk_string) #identify the parent obj
        query_attrs.append(dep.parent.fullname) # the parent value
                
        '''
        Adding obj values to were clause. As an obj is identified by possibly multiple primary key values, the
        where clause looks like this:
            WHERE ..(slotchain_where)... AND ( (ob1_pk1=val AND ob1_pk2=val...) OR ((ob2_pk1=val AND ob2_pk2=val...)), .....)
        ''' 
        query_obj = []
        for v in gbnVertices:   
            temp_obj = []         
            for (pk_i,obj_i) in zip(v.attr.erClass.pk,v.obj): #and obj contains a index for every pk of the v.attr.erClass (=dep.child.erclass)
                temp_obj.append('%s=%s'%(pk_i.fullname,obj_i))
            query_obj.append('(%s)'%(' AND '.join(temp_obj)))
                
        sqlAttr = ','.join(query_attrs)
        sqlFrom = ','.join(query_tables)
        sqlWhere = ' AND '.join(query_where)
        sqlObj = ' OR '.join(query_obj)
        
        sqlQuery = ''
        if sqlWhere!='':
            #slotchain present
            sqlQuery = "SELECT %s FROM %s WHERE %s AND (%s);"%(sqlAttr,sqlFrom,sqlWhere,sqlObj) 
        else:
            #no slotchain
            sqlQuery = "SELECT %s FROM %s WHERE (%s);"%(sqlAttr,sqlFrom,sqlObj) 
        
                
        
        # #HACK HACK HACK : just remove objects where clause (also introduced hack in engine.py)
        # if len(query_obj)>900:
        #     if sqlWhere!='':
        #         sqlQuery = "SELECT %s FROM %s WHERE %s;"%(sqlAttr,sqlFrom,sqlWhere)                         
        #     else:
        #         sqlQuery = "SELECT %s FROM %s;"%(sqlAttr,sqlFrom)                         
        #     #print 'WARNING : QUERY TOO LONG'
            
        
        #print '\nLOAD parents for dep %s:\n%s\n'%(dep.name,sqlQuery)
        self.cur.execute(sqlQuery)

    
    def loadDependencyChildrenObjects(self, dep, gbnVertices):
        """
        Given a set of parent attribute objects `gbnVertices` for a given dependency dep, we are loading the set of children.
        
        The result set will consist of rows in the following format:
        
        |   dep_parent.pk1,dep_parent.pk2,..., dep_child.pk1,dep_child.pk2,...,dep_child.val
        |   <   parent indentification      > <               child                       > 
        
        :arg dep: :class:`prm.dependency.Dependency`
        :arg gbnVertices: A list of :class:`network.groundBN.GBNvertex`
        """
                                       
        # attributes list
        query_attrs = []
        query_attrs.extend(dep.parent.erClass.pk_string) # to identify the parent vertex     
        query_attrs.extend(dep.child.erClass.pk_string) # to identify the child vertex     
        query_attrs.append(dep.child.fullname) # the parent value
        
        # table list
        query_tables = []
        query_tables.extend(dep.slotchain_string)
        # where list
        query_where = []
        query_where.extend(dep.slotchain_attr_string)
        

        
        '''
        Adding obj values to were clause. As an obj is identified by possibly multiple primary key values, the
        where clause looks like this:
            WHERE ..(slotchain_where)... AND ( (ob1_pk1=val AND ob1_pk2=val...) OR ((ob2_pk1=val AND ob2_pk2=val...)), .....)
        ''' 
        query_obj = []
        
        #from IPython.Shell import IPShellEmbed
        #IPShellEmbed()()
        
        for v in gbnVertices: 
            temp_obj = []         
            for (pk_i,obj_i) in zip(v.attr.erClass.pk,v.obj): #and obj contains a index for every pk of the v.attr.erClass (=dep.child.erclass)
                temp_obj.append('%s=%s'%(pk_i.fullname,obj_i))
            query_obj.append('(%s)'%(' AND '.join(temp_obj)))


        sqlAttr = ','.join(query_attrs)
        sqlFrom = ','.join(query_tables)
        sqlWhere = ' AND '.join(query_where)
        sqlObj = ' OR '.join(query_obj)
        
        '''
        sqlGroupBy = ','.join(dep.parent.erClass.pk_string)
        sqlQuery = "SELECT %s FROM %s WHERE %s AND (%s) GROUP BY %s;"%(sqlAttr,sqlFrom,sqlWhere,sqlObj,sqlGroupBy) 
        '''
        
        sqlQuery = ''        
        if sqlWhere!='':
            #slotchain present
            sqlQuery = "SELECT %s FROM %s WHERE %s AND (%s);"%(sqlAttr,sqlFrom,sqlWhere,sqlObj) 
        else:
            #no slotchain
            sqlQuery = "SELECT %s FROM %s WHERE (%s);"%(sqlAttr,sqlFrom,sqlObj) 
        
        # #HACK HACK HACK : just remove objects where clause (also introduced hack in engine.py)
        # if len(query_obj)>900:
        #     if sqlWhere!='':
        #         sqlQuery = "SELECT %s FROM %s WHERE %s;"%(sqlAttr,sqlFrom,sqlWhere)                         
        #     else:
        #         sqlQuery = "SELECT %s FROM %s;"%(sqlAttr,sqlFrom)                         
        #     #print 'WARNING : QUERY TOO LONG'
        
        #print '\nLOAD children for dep %s:\n%s\n'%(dep.name,sqlQuery)
        self.cur.execute(sqlQuery)
    
    def loadAttributeParentObjects(self, attr, gbnVertices):
        """
        Given a set of children objects obj for a given attribute attr, we are loading the set of parents (for all depenencies that `attr` is a child of). This method is not used because it performs poor compared to :meth:`loadDependencyChildrenObjects` and :meth:`loadDependencyParentObjects`.
        """
                     
        #if there are no parents we can't do anything
        if len(attr.dependenciesChild) == 0:
            return None              
        # attributes list
        query_attrs = []
        query_attrs.extend(attr.erClass.pk_string) # to identify the child vertex     
        # table list
        query_tables = [attr.erClass.name]
        # where list
        query_where = []
        
        '''
        # TODO : ALL THIS INFORMATION CAN BE PRECOMPUTED EXCEPT THE gbnVertices PART OF THE WHERE CLAUSE   
        
        PROBLEM. VIEW'S MAKE IT RUN REALLY SLOW! THERE SHOULD BE AN EASY WAY TO BRING THE AGGREGATION 
        INTO THE QUERY WITHOUT USING THE VIEW (E.G. SPLITTING LOADPARENTOBJECTS() UP BY QUERYING THE DATA ONCE
        FOR EVERY PARENT)
        
        with view it is painfully slow
        SELECT User.user_id,AGG_rating FROM User,rating_gender WHERE User.user_id=rating_gender.user_id AND (User.user_id=900);
        
        this is much much faster
        SELECT User.user_id,AVG(rates.rating) FROM User,rates WHERE User.user_id=rates.user_id AND (User.user_id=900);
        
        '''
        for dep in attr.dependenciesChild:  
            # add parent attributes to query_attrs list
            # merge the table names in query_tables
            # merge where statements (e.g. User.user_id=rates.user_id)
            
            if dep.aggregator is None: # n:1 or 1:1 dependency type 
                #attributes
                query_attrs.extend(dep.parent.erClass.pk_string)
                query_attrs.append(dep.parent.fullname)
                #from
                for er in dep.slotchain_string:
                    if er not in query_tables:
                        query_tables.append(er)  
                #where
                for att_str in dep.slotchain_attr_string:
                    if att_str not in query_where:
                        query_where.append(att_str)
                              
            else: # aggregation 1:n or m:n dependency type
                query_attrs.append(('AGG_'+dep.parent.name))
                query_tables.append(dep.name)
                
                ## attr.erClass.pk[i] = dep_name.parent
                for pk_i in attr.erClass.pk:
                    query_where.append('%s=%s.%s'%(pk_i.fullname,dep.name,pk_i.name))
        
        # adding obj values to were clause
        query_obj = []
        for v in gbnVertices:            
            for (pk_i,obj_i) in zip(attr.erClass.pk,v.obj):
                query_obj.append('%s=%s'%(pk_i.fullname,obj_i))
            
        
        sqlAttr = ','.join(query_attrs)
        sqlFrom = ','.join(query_tables)
        sqlWhere = ' AND '.join(query_where)
        sqlObj = ' OR '.join(query_obj)
        
        sqlQuery = "SELECT %s FROM %s WHERE %s AND (%s);"%(sqlAttr,sqlFrom,sqlWhere,sqlObj) 
        #logging.debug(sqlQuery)
        self.cur.execute(sqlQuery)

    def loadAttributeObjects(self, attr ):
        '''
        All attribute objects of the attribute `attr` are queried.
        The result set will consist of rows in the following format:
        
        |   attr.pk1,attr.pk2,........,attr.val
        |   < attr indentification > < attr  > 

        :arg attr: :class:`.Attribute`
        '''

        sqlAttribute = '%s,%s'%(",".join( [pk.fullname for pk in attr.erClass.pk ] ),attr.fullname)
        
        
        # We are only loading data from one table
        sqlTable = attr.erClass.name
                
       
        sqlQuery = 'SELECT %s FROM %s;'%(sqlAttribute,sqlTable)
        
        # logging.debug(sqlQuery)
        
        self.cur.execute(sqlQuery)

    def loadExistParents(self, dep, existdep ):
        '''
        In the case of reference uncertainty, the exist attributes have a set of parents that need to be included in the ground Bayesian network. The SQL query needed is constructed in this method, the resultset will be of the following format. The `k-entity` references the entity on the `k` side of the `n:k` relationship (i.e. `Professor` in the student/prof example from Pasula). The primary key of the `k-entity` is used to identify 

        
        |   k_entity.pk1,  dep.parent.pk1,dep.parent.pk2,.....,dep.parent.val
        |   < k entity id >< parent indentification >         < parent value > 

        :arg dep: :class:`.UncertainDependency`
        :arg existdep: :class:`.Dependency` with the exist attribute as child
        '''


        k_attr_id = ",".join( [pk.fullname for pk in dep.kAttribute.erClass.pk ])
        parent_id = ",".join( [pk.fullname for pk in existdep.parent.erClass.pk ])
        parent_val = existdep.parent.fullname


        sqlAttribute = '%s,%s,%s'%(k_attr_id,parent_id,parent_val)
        
        tables = []
        for er in existdep.slotchain:
            if not er==dep.uncertainRelationship:
                # there are no entries in the database table of the uncertain relationship
                tables.append(er.name)
        sqlTable = ','.join(tables)


        if not len(existdep.slotchain_erclass_exclusive[dep.uncertainRelationship]) == 0:
            sqlWhere = ' AND '.join(existdep.slotchain_erclass_exclusive[dep.uncertainRelationship])

            sqlQuery = 'SELECT %s FROM %s WHERE %s;'%(sqlAttribute,sqlTable,sqlWhere)
                
        else:
            # no where statements
            sqlQuery = 'SELECT %s FROM %s;'%(sqlAttribute,sqlTable)
        
        logging.debug(sqlQuery)
        
        self.cur.execute(sqlQuery)

    
    def retrieveRow(self):
        '''
        After executing a `loadXXX()` method, the cursor `self.cur` contains the result set
        for a specific SQL query. This method returns the next row in the result set, which 
        allows a caller, e.g. :meth:`learners.cpdlearners.CPDTabularLearner.learnCPDsFull` or :meth:`inference.engine.unrollGBN`, to iterate over all rows without knowledge about the data interface.
        '''
        return self.cur.fetchone()

    def resultSet(self):
        '''
        We return the the cursor which is an iterable result set of the executed query (after executing a `loadXXX()` method).
        The result set can then be iterated like this in the caller method::

            for currentRow in dsi.resultSet():
                do something with `currentRow`

        '''
        return self.cur
    
    def createView(self,dep):                
        '''         
        If a probabilistic dependency between an attribute and a parent attribute is of type m:n or 1:n, 
        some sort of aggregation has to be performed. A VIEW is created that performs the necessary aggregation
        and enables the datainterface to query the already aggregated values in one query. The name of the view
        is `dep.name` and it can be used when learning local distributions or unrolling a ground bayes net.

        When there are multiple dependencies from and to the same erClass, then we could create only one view.
        Instead we create a view for each dependency independently which makes it easier but redundant  
        
        .. note:: `VIEWS` are implemented but not used. In practice their performance proved to be worse than working on the data directly.
        '''        
        #print "\tCreate View in SQLite for ",dep
        #string for set of primary keys (just one for an entity/multiple for a relationship)
        pk_string = ','.join(dep.child.erClass.pk_string)
        #aggregator keyword for SQLite (e.g. AVG)
        aggr_string = dep.aggregator(self.dsiType)
        aggr_attr_name = 'AGG_%s'%dep.parent.name
        sqlAttr = '%s, ROUND(%s(%s)) as %s'%(pk_string,aggr_string,dep.parent.fullname,aggr_attr_name)
        sqlFrom = ','.join(dep.slotchain_string)
        sqlWhere = ' AND '.join(dep.slotchain_attr_string)
        sqlGroup = pk_string
        sqlCreate = "CREATE VIEW IF NOT EXISTS %s AS SELECT %s FROM %s WHERE %s GROUP BY %s;"%(dep.name,sqlAttr,sqlFrom,sqlWhere,sqlGroup) 
        #print sqlCreate
        self.cur.execute(sqlCreate)
        
        
    def __repr__(self):
        ''' String representation for SQLite DI '''
        return '%s DataSet Interface connecting to %s'%(self.dsiType,self.path.split('/')[-1])