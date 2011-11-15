"""
Config Module :mod:`ui.config`
---------------------------------------------------------------

:mod:`!ui.config` is used to create instances of the different building blocks for a ProbReM project, e.g. the PRM model, the data interface, the learner and the inference methods. The methods are accessed by importing the `config` module ::

    from ui import config
    import probrem
    config.loadPRM(prmSpec)

Then code above for example would initialize the PRM module :mod:`~!prm.prm`::

    print probrem.PRM
    <module 'prm.prm' from './../../src/prm/prm.pyc'> 

The config module can't be executed directly.
"""
    
import sys

from ui import log
import logging


from xml_prm.parser import DataInterfaceParser
from xml_prm.parser import PRMparser

import learners  

from inference import engine



def fromFile(probremI, config):
	'''Using a config file to load PRM. Not implemented yet. '''		
		
	raise Exception("Config file support not implemented yet")

	

	
def loadPRM(prmSpec):
	"""
	Loads a :class:`~!prm.prm.PRM` instance using the :class:`.PRMparser`
	
	:arg prmSpec: File name of PRM XML specification
	:returns: :class:`prm.prm.PRM` instance
    
	"""
		
	logging.info("PRM Factory: create PRM from %s"%(prmSpec.split('/')[-1]))
	return PRMparser().parsePRM(prmSpec)

def loadDI(diSpec):
	"""
	Loads a :class:`~!data.datainterface.DataInterface` instance
	
	:arg diSpec: File name of Data Interface XML specification
	:returns: :class:`data.datainterface.DataInterface` instance, e.g. :class:`~data.sqliteinterface.SQLiteDI`
    
	"""
	logging.info("DataInterface Factory: create DataInterface from %s"%(diSpec.split('/')[-1]))
	return DataInterfaceParser().parseDataInterface(diSpec)		

def loadLearner(learnerType):
    """
	Loads a learner instance, e.g. a :class:`~!learners.cpdlearners.CPDLearner` instance for learning 
	the conditional probability distributions (CPDs). 
	
	:arg learnerType: Name of a learner class (e.g. `CPDTabularLearner`)
	:returns: A learner instance, e.g. :class:`~learners.cpdlearners.CPDTabularLearner`
    
	"""
    
    logging.info('Learner Factory: create %s'%(learnerType))
    return getattr(learners,learnerType )()


def loadInferenceAlgorithm(inferenceType):
	"""
	Loads the specified inference algorithm for the engine :mod:`~!.engine` and configures it to use `inferenceType` (e.g. MCMC,LW).
	
	Usually an inference algorithm implements a `configure()` method that can be used to precompute data structures needed for inference.
    In the case of the Gibbs sampler, :mod:`.gibbs.configure` will precompute all the conditional likelihood functions of the attributes with parents. Note that at the time a inference method is configured, the PRM should be initialized with proper local distributions (either learned or loaded).
	
	:arg inferenceType: The name of the inference method (e.g. `GIBBS` or `MH`)	
	"""
	
	if inferenceType == 'GIBBS':
	    from inference.mcmc import gibbs 
	    engine.inferenceAlgo = gibbs
	    gibbs.configure()
	
	elif inferenceType == 'MH':
	    from inference.mcmc import mh 
	    engine.inferenceAlgo = mh
	    mh.configure()
	


