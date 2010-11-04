"""
Performance Module :mod:`analytics.performance`
------------------------------------------------

Main module for performance analyis of the Probrem package
"""

import time
import numpy as N


measurments = {}
''' A dictionary to keep track of execution times for methods {key=function.__name__ : value=execution time } '''

def time_analysis(caller):
    '''
    A decorator function that measures and saves the time of the calling method `caller`
    
    The decorator function is used by adding ::
    
        from analytics.performance import time_analysis
    
    to the module of the caller method and by adding ::
    
        @time_analysis
        def methodtomeasure():
            ...
    
    on the line before the caller function definition    
    '''
    if caller.__name__ not in measurments:
        measurments[caller.__name__]=[]
    
    def new_caller(*args):
        t_start = time.time() #starting time
        r = caller(*args) #execute funtion
        t_end =  time.time() #end time
        measurments[caller.__name__].append((t_end-t_start))
        return r        
        #print 'Executed %s in %s s'%(caller.__name__,(t_end-t_start))    
        
        #print measurments
    return new_caller
    
def displayTimeAnalysis():
    ''' Displays statistics about the running times of all methods that are decorated with the @time_analysis'''
    for (caller,times) in measurments.items():
        print '%s() exution time:'%(caller)
        print '\tNumber of calls = %s'%(len(times))
        if len(times) != 0:
            print '\tTotal = %5e / Min = %5e / Max = %5e / Mean = %5e / Var = %5e'%(N.sum(times),N.min(times),N.max(times),N.mean(times),N.var(times))

