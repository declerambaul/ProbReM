
class ERClass():
    '''
    This abstract class serves as a container for the objects that contain
    attributes. These objects are either :class:`.Entity` classes or :class:`.Relationship` classes;
    each can contain :class:`.Attribute` classes which themselves have to know
    which container object they belong to. The :class:`Entity`/:class:`Relationship` classes inherit
    the :class:`ERClass` class. Therefore, an attribute can find the type of its container
    object by calling `self.erClass.type()`
    
    .. inheritance-diagram:: prm.relationalschema
    '''
    def __init__(self):
        raise Exception("Abstract class ERClass can't be instantiated")

    def isEntity(self):
        '''
        Returns `True` if the type is `Entity`
        '''
        return self.type() == 'Entity'
    
    def type(self):
        '''
        The type of an ERClass, either `Entity` or `Relationship`
        '''
        return self.__class__.__name__
    
    
class Entity(ERClass):
    '''
    Represents an entity class in the relational schema. 
    '''
    def __init__(self, name):
        '''
        Constructs an Entity class
        '''
        self.name=name
        """Unique name
        """
        self.pk = []
        """
        The primary key is a list of :class:`.Attribute` objects of the entity. The pk is created automatically as a
        :class:`.NotProbabilisticAttribute` if not specified otherwise. It is stored as a list with just one item.
        """
        
        self.pk_string = [] 
        """
        String representation of primary key
        """
        
        
        self.attributes = None
        """
        List that contains the :class:`.Attributes` references of the entity class
        """
        
        self.relationships = {}
        """
        List that contains the :class:`.Relationship` references that are connected to 
        the entity. 
        """
                           
    def __repr__(self):
        '''
        Returns a string representation of the instance 
        ''' 
        return "Entity (%s), pk=%s"%(self.name,self.pk[0].name)


class Relationship(ERClass):
    '''
    An relationship class relates two entity classes ( implicitly using their primary 
    keys as identifiers). Note the source of confusion, `Relationship` refers to the Entity-Relationship model;
    not to be confused with the probabilistic :class:`.Dependency` which is conceptually also a relationship    
    '''
    def __init__(self, name, type):
        '''
        Constructs an Relationship instance
        '''                
        self.name = name
        """Unique name
        """
        
        self.pk = []
        """
        The primary key of a relationship class is usually specified by the set of foreign keys of connected entities. 
        A relationship class has a primary key that consists of a list of :class:`ForeignAttribute` instances 
        whose `target`'s are attributes of the connecting entities (usually their primary key attributes). 
        """
        self.pk_string = []
        """List of string representation of `self.pk`
        """
        self.foreign = {}    
        """Dictionary represenation of `self.pk` where the key is an entity and the value a list of foreign 
        attributes that belong to that entity, e.g. {key= :class:`.Entity` : value=[ :class:`.ForeignAttribute` , .. ]}
        """
        
        self.entities = []
        """List of :class:`Entities` connected to the relationship
        """
        
        self.relationType = type  
        """
        The type of an relationship indicates is `1:1`, `1:n` or `m:n`.
        """      
        
        self.attributes = None
        """
        A dictionary that contains the attributes references of the relationship class
        {key : Attribute name, value: :class:`.Attribute`}
        """   
        
    def __repr__(self):
        '''
        Returns a string representation of the instance 
        ''' 
        return "Relationship (%s , pk=[%s], type=%s)"%(self.name,",".join(['%s->%s'%(fa.fullname,fa.target.fullname) for fa in self.pk]), self.relationType)  
        
        
        