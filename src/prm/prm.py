'''
The `PRM` module specifies `attributes`, `entities`, `relationships` and `dependencies`.
The information in the PRM is very interlinked since different methods
have to access the same data from different starting points.
e.g. access all the attributes from a given entity is easier from that
specific entity instance via entity.attributes, whereas when iterating
over all attributes in the prm it is easier to do using prm.attributes.
Naturally all attributes, entities, relationships, dependencies are instanciated
only once and then referenced. The method :meth:`xml_prm.parser.parsePRM` is 
initializing all instance variables.
'''
from relationalschema import Entity,Relationship
from attribute import topologicalSort


name = 'NoName'
"""Name of the Probabilistic Relational Model 
""" 

entities = None
"""Dictionary of all :class:`.Entity` instances 
"""

relationships = None
"""Dictionary of all :class:`.Relationship` instances 
"""

attributes = None
"""Dictionary of all :class:`.Attribute` instances 
"""    

dependencies = None
"""Dictionary of all :class:`.Dependency` instances 
"""

datainterface = 'NotSpecified'
"""Path to a compatible datainterface xml specifiaction
"""

topoSortAttributes = None
"""List of attributes that are topologically sorted using :meth:`prm.attribute.topologicalSort`
"""
    
def __repr__():
    '''
    Returns a string representation for the PRM for the console. 
    
    Unfortunately __repr__() is not invoked when 'print module' is called, so __repr__() has to be called directly.
    '''
    ws1 = len(name)/2
    ws2 = 5
    ws3 = 25
    textprm = name+'\n'

    for i, (ke,e) in enumerate(entities.items()):
        textprm += ' ' * ws1 + '-- ' + str(e) +'\n'            
        for j, (ka,a) in enumerate(e.attributes.items()):                
            textprm += ' ' * ws1 + '| ' + ' '*ws2 + str(a) +'\n'
        textprm += ' ' * ws2 +'---' * ws3 +'\n'                                
    for i, (kas,ass) in enumerate(relationships.items()):
        textprm += ' ' * ws1 + '-- ' + str(ass) +'\n'            
        for j, (ka,a) in enumerate(ass.attributes.items()):                
            textprm += ' ' * ws1 + '| ' + ' '*ws2+ str(a) +'\n'  
        textprm += ' ' * ws2 +'---' * ws3 +'\n'                
    for i, (kd,d) in enumerate(dependencies.items()):
        textprm += ' ' * ws1 + '-- ' + str(d) +'\n'            
#            for j, (ka,a) in enumerate(ass.attributes.items()):                
#                textprm += ' ' * ws2 + '| ' + str(a) +'\n'  
        textprm += ' ' * ws2 +'---' * ws3 +'\n'
                         
    return textprm
   



        