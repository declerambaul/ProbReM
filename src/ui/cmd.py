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

import logging


def ipythonRunning():
	'''
	Returns `True` if the method is executed in an active IPython shell
	'''
	try:
		__IPYTHON__active
		return True
	except NameError:
		return False 


def ipythonShell():
	'''
	Starts an interactive ipython session if the session is not already started
	'''
	global ipythonRunning
	if not ipythonRunning():

		
		import IPython
		

		try:
			# This code does only work with IPython version < 0.11. 
			# interactive iPython console
			from IPython.Shell import IPShellEmbed
			ipshell = IPShellEmbed()
			# ion() is hack that allows to run a threaded ipython session with pylab. Thus it is possible to plot() without the show() command and without blocking the input
			ipshell.IP.runlines('from pylab import ion; ion()')
			ipshell()
			ipythonRunning = True
			

		except:
			
			# This code should work with IPython version > 0.11. 
			try: 				
				
				IPython.embed(exit_msg='')
				ipythonRunning = True

			
			except:			
				logging.warning('Unable to intialize an embedded IPython shell. Try to run the model from within IPython itself.')

				logging.info('Instead, pylab.show() is called to display any matplotlib figures plotted run time')
				from pylab import show
				show()

				

					
def displayCPDs():
	'''Prints the conditional probability distributions (CPDs) for all probabilistic attributes '''		
	
	for a in probrem.PRM.attributes.values():
	    logging.info(a)
	    if a.CPD is not None:
	        logging.info(a.CPD.cpdMatrix)


if __name__ == '__main__' :
    ''' 
    Not allowed to execute :mod:`ui.config` directly.
    '''         
    raise Exception("You are running stand alone instance. You shouldn't be doing that.")    
