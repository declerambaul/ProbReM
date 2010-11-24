"""
Command Line Module :mod:`ui.cmd`
---------------------------------------------------------------

:mod:`!ui.cmd` contains useful methods to display information about the ProbReM model on the command line using `ipython`. The methods are accessed by importing the `cmd` module ::

    from ui import cmd
 

Then one can for example diplay all :class:`~!prm.localdistribution.CPD` instances::

    cmd.displayCPDs() 

The `cmd` module can't be executed directly.
"""

import probrem

if __name__ == '__main__' :
    ''' 
    Not allowed to execute :mod:`ui.config` directly.
    '''         
    raise Exception("You are running stand alone Probrem instance. You shouldn't be doing that. See README in root folder")
    
 

def displayCPDs():
	'''Prints the conditional probability distributions (CPDs) for all probabilistic attributes '''		
	
	for a in probrem.prmI.attributes.values():
	    print a
	    if a.CPD is not None:
	        print a.CPD.cpdMatrix
