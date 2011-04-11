'''
.. |probremC| replace:: **P**\ rob\ **R**\ e\ **M**  

The module :mod:`probrem.Probrem` is the basis of a |probremC| framework. :mod:`probrem.Probrem` has to be initialised by a separate script, it can't be executed.
'''

if __name__ == '__main__':
    raise Exception("You are running stand alone Probrem instance. You shouldn't be doing that. See README in root folder")
    

import prm.prm as PRM
"""The instance of the PRM model of type :mod:`prm.prm` 
"""
import data.datainterface as DI
"""The data interface instance is implemented in :mod:`data.datainterface` 
"""
import inference.engine as engine
"""The inference engine is implemented in the :mod:`inference.engine`.
"""
learners = {}
"""A dictionary of learners instances, e.g. { 'cpdLearnerName' : :class:`learners.cpdlearners.CPDTabularLearner` } 
"""
