"""
Logging Module :mod:`ui.log`
---------------------------------------------------------------

The module :mod:`!ui.log` allows the logging of warning/errors/debugging messages. It is configured display logging messages to the console as well as a log file. This module configures the python logging module accordingly. Instead of `print` statements in the code, one can simply::

    import logging
 

Then one can for example diplay a debug message by invoking::

    logging.debug('What is happening here?')


"""

import probrem
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='\t<%(levelname)-6s - %(module)s.%(funcName)s():%(lineno)d>\n%(message)s',
                    # format='%(name)-12s %(levelname)-8s - %(funcName)s %(lineno)d : %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='probrem.log',
                    filemode='w')


# If there is a syntaxt error in the logging code during runtime, the exception doesn't specify the file/linenumber of the problem. This error handler can be used to see the details.
# def handleError(self, record):
#   raise
# logging.Handler.handleError = handleError


# printing to ipython console
console = logging.StreamHandler()
# don't print debug messages in console, only to file
console.setLevel(logging.INFO)

# set a format which is simpler for console use 
# formatter = logging.Formatter('%(funcName)s %(lineno)d : %(message)s')
formatter = logging.Formatter('%(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

