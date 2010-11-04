
from relationalschema import Entity,Relationship
from attribute import topologicalSort


class PRM:
    '''
    An `PRM` instance is defined by `attributes`, `entities`, `relationships` and `dependencies`.
    The information in the PRM is very interlinked since different methods
    have to access the same data from different starting points.
    e.g. access all the attributes from a given entity is easier from that
    specific entity instance via entity.attributes, whereas when iterating
    over all attributes in the prm it is easier to do using prm.attributes.
    Naturally all attributes,entities,relationships,dependencies are instanciated
    only once and then referenced.
    '''
    
    def __init__(self, name, entities, relationships, attributes, dependencies, diPath):
        '''
        Constructs a PRM. To define a PRM, use the method 
        constructPRM() in the xml parser.
        
        
                    
        '''
        self.name = name   
        """Name of the Probabilistic Relational Model """ 
        self.entities = dict(entities)
        """Dictionary of all :class:`.Entity` instances """
        self.relationships = dict(relationships)
        """Dictionary of all :class:`.Relationship` instances """
        self.attributes = dict(attributes)
        """Dictionary of all :class:`.Attribute` instances """
        self.dependencies = dict(dependencies)
        """Dictionary of all :class:`.Dependency` instances """
        
        self.datainterface = diPath
        """Path to a compatible datainterface xml specifiaction"""
        
        self.topoSortAttributes = topologicalSort([a for a in self.attributes.values() if a.probabilistic])
        """List of attributes that are topologically sorted using :meth:`prm.attribute.topologicalSort`"""
        
    def __repr__(self):
        '''
        Returns a string representation for the PRM for the console
        '''
        ws1 = len(self.name)/2
        ws2 = 5
        ws3 = 25
        textprm = self.name+'\n'

        for i, (ke,e) in enumerate(self.entities.items()):
            textprm += ' ' * ws1 + '-- ' + str(e) +'\n'            
            for j, (ka,a) in enumerate(e.attributes.items()):                
                textprm += ' ' * ws1 + '| ' + ' '*ws2 + str(a) +'\n'
            textprm += ' ' * ws2 +'---' * ws3 +'\n'                                
        for i, (kas,ass) in enumerate(self.relationships.items()):
            textprm += ' ' * ws1 + '-- ' + str(ass) +'\n'            
            for j, (ka,a) in enumerate(ass.attributes.items()):                
                textprm += ' ' * ws1 + '| ' + ' '*ws2+ str(a) +'\n'  
            textprm += ' ' * ws2 +'---' * ws3 +'\n'                
        for i, (kd,d) in enumerate(self.dependencies.items()):
            textprm += ' ' * ws1 + '-- ' + str(d) +'\n'            
#            for j, (ka,a) in enumerate(ass.attributes.items()):                
#                textprm += ' ' * ws2 + '| ' + str(a) +'\n'  
            textprm += ' ' * ws2 +'---' * ws3 +'\n'
                             
        return textprm
   



        