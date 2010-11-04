'''
.. |probremC| replace:: **P**\ rob\ **R**\ e\ **M**  

An instance of the class :class:`probrem.Probrem` is the basis of a |probremC| framework. :class:`probrem.Probrem` has to be instatiated by a separate script, it can't be executed.
'''

if __name__ == '__main__':
    raise Exception("You are running stand alone Probrem instance. You shouldn't be doing that. See README in root folder")
    


class Probrem:
    ''' 
    Main Class of the PRM package |probrem|
    '''
    def __init__(self ):        
		
		self.prmI = None
		"""The instance of the PRM model of type :class:`.PRM` 
		"""
		self.diI = None
		"""The data interface instance is an implementation of :class:`data.datainterface.DataInterface` 
		""" 
		self.inferenceI = None
		"""The inference engine instance :class:`inference.engine.Engine`, configured with a inference method
		"""
		self.learnersI = {}
		"""A dictionary of learners instances, e.g. { 'cpdLearnerName' : :class:`learners.cpdlearners.CPDTabularLearner` } 
		"""
		
