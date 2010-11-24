'''
.. |probrem| replace:: **P**\ rob\ **R**\ e\ **M**  

The module :mod:`probrem.Probrem` is the basis of a |probrem| framework. :mod:`probrem.Probrem` has to be initialised by a separate script, it can't be executed.
'''

if __name__ == '__main__':
    raise Exception("You are running stand alone Probrem instance. You shouldn't be doing that. See README in root folder")
    

prmI = None
"""The instance of the PRM model of type :class:`.PRM` 
"""
diI = None
"""The data interface instance is an implementation of :class:`data.datainterface.DataInterface` 
"""
inferenceI = None
"""The inference engine instance :class:`inference.engine.Engine`, configured with a inference method
"""
learnersI = {}
"""A dictionary of learners instances, e.g. { 'cpdLearnerName' : :class:`learners.cpdlearners.CPDTabularLearner` } 
"""
