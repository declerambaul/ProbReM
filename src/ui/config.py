"""
Config Module :mod:`ui.config`
---------------------------------------------------------------

:mod:`!ui.config` is used to create instances of the different building blocks for a ProbReM project, e.g. the PRM model, the data interface, the learner and the inference methods. The methods are accessed by importing the `config` module ::

    from ui import config
    from probrem import Probrem
    probremI = Probrem()

Then one can for example create a :class:`~!prm.prm.PRM` instance::

    probremI.prmI = config.loadPRM(prmSpec)

The config module can't be executed directly
"""

import sys

if __name__ == '__main__' :
    ''' 
    Not allowed to execute :mod:`ui.config` directly.
    '''         
    raise Exception("You are running stand alone Probrem instance. You shouldn't be doing that. See README in root folder")
    

from xml_prm.parser import DataInterfaceParser
from xml_prm.parser import PRMparser

from learners.learnerfactory import learnerFactory
from inference.engine import Engine


def fromFile(probremI, config):
	'''Using a config file to load PRM. Not implemented yet. '''		
		
	raise Exception("Config file support not implemented yet")

	

	
def loadPRM(prmSpec):
	"""
	Loads a :class:`~!prm.prm.PRM` instance using the :class:`.PRMparser`
	
	:arg prmSpec: File name of PRM XML specification
	:returns: :class:`prm.prm.PRM` instance
    
	"""
	
	print "PRM Factory: create PRM from %s"%(prmSpec.split('/')[-1])	
	return PRMparser().parsePRM(prmSpec)

def loadDI(diSpec):
	"""
	Loads a :class:`~!data.datainterface.DataInterface` instance
	
	:arg diSpec: File name of Data Interface XML specification
	:returns: :class:`data.datainterface.DataInterface` instance, e.g. :class:`~data.sqliteinterface.SQLiteDI`
    
	"""
	print "DataInterface Factory: create DataInterface from %s"%(diSpec.split('/')[-1])
	return DataInterfaceParser().parseDataInterface(diSpec)		
	#return datainterfaceFactory(diSpec)

def loadLearner(learnerType):
    """
	Loads a :class:`~!learners.cpdlearners.CPDLearner` instance using :meth:`learners.learnerfactory`
	
	:arg diSpec: File name of Data Interface XML specification
	:returns: :class:`learners.cpdlearners.CPDLearner` instance, e.g. :class:`~learners.cpdlearners.CPDTabularLearner`
    
	"""
    return learnerFactory(learnerType)

def loadInference(inferenceType):
	"""
	Loads the specified inference engine :class:`~!.Engine` and configures it to use inferenceType (e.g. MCMC,LW)  
	
	:arg inferenceType: The name of the inference method class (MCMC,LW)
	:returns: :class:`.Engine` instance
    
	"""
	return Engine(inferenceType)

