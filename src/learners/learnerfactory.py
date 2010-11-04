"""
Learning algorithms are initialized using a learner factory:
"""

import learners as L

def learnerFactory(lType,prmI=None,diI=None):
	"""The `learnerFactory` returns in instance of the desired learner passed in the string `lType`.
	
	:arg lType: String name of the desired learner, e.g. `CPDTabularLearner` for :class:`~learners.cpdlearners.CPDTabularLearner`
	"""
	
	#print learners.cpdlearners
	#print getattr(l,'CPDTabularLearner' )
	
	
	print 'Learner Factory: create %s'%(lType)  
	return getattr(L,lType )()	