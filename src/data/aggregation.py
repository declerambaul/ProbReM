'''
Aggregation becomes necessary if an attribute object has multiple parent attribute objects for one single dependency, e.g. in the case of a `1:n` or `m:n` relationship. As the conditional probability distribution (:class:`.CPD` ) of that attribute class allows only one parent value for this dependency, the values of these parent attribute objects must be aggregated. Any function :math:`f(pa1,pa2,...) = pa_{aggr}` where :math:`pa_i` are the parent values and :math:`pa_{aggr}` is a single value in the domain of the parent attribute class.


Aggregation can be performed on different levels, e.g. on the database level using SQL keywords or during runtime by aggregating values in the Ground Bayesian Network. The :mod:`!.aggregation` module provides this functionality for a set of aggregation functions. When instantiating an aggregator type for a dependency, e.g. the `MAX` aggregator during runtime::
    
    import data.aggregation
    aggr = data.aggregation.aggregators['MAX']['runtime']
    
returns the method :meth:`data.aggregation.runtime_avg`. Or ::
    
    aggr = data.aggregation.aggregators['MAX']['SQLite']   
    
simply returns the SQL keyword `AVG`. 
    
'''


'''
########################################################################################################################
AVERAGE AGGREGATOR
'''
def runtime_avg(values):
    '''All variables are discrete, therefore we round to the nearest integer.
    
    :arg values: List of attribute object values
    :returns: Average of values
    '''
    return round(sum(values)*1./len(values))
    
SQLite_keyword = 'AVG'
""" SQLite keyword for average, `AVG` """

# The average dictionary maps the different ways to do aggregation to keywords/methods 
avg_dict = {'SQLite':SQLite_keyword,'runtime':runtime_avg}

def agg_avg(aggOrigin):
    return avg_dict[aggOrigin]


'''
########################################################################################################################
MAX AGGREGATOR
'''
def runtime_max(values):
    '''
    Compute MAX of all values.
    
    :arg values: List of attribute object values
    :returns: Maximum of values
    '''
    return max(values)
    
SQLite_keyword = "MAX"
""" SQLite keyword for maximum, `MAX` """

    
max_dict = {'SQLite':SQLite_keyword,'runtime':runtime_max}

def agg_max(aggOrigin):
    return max_dict[aggOrigin]

'''
########################################################################################################################
MIN AGGREGATOR
'''
def runtime_min(values):
    '''
    Compute  min of all values
    
    :arg values: List of attribute object values
    :returns: Minimum of values
    '''
    return min(values)
    
SQLite_keyword = "MIN"
""" SQLite keyword for maximum, `MIN` """    
    
    
min_dict = {'SQLite':SQLite_keyword,'runtime':runtime_min}

def agg_min(aggOrigin):
    return min_dict[aggOrigin]

'''
########################################################################################################################
MODE AGGREGATOR
'''
def runtime_mode(values):
    '''
    Compute mode of all values
    '''
    return None
    
SQLite_keyword = "DOESN'T EXIST"

mode_dict = {'SQLite':SQLite_keyword,'runtime':runtime_mode}

def agg_mode(aggOrigin):
    return mode_dict[aggOrigin]




'''
########################################################################################################################
The dictionary used by the parser to asign a aggregator method to a dependency
'''
aggregators = {'AVG':agg_avg,'MAX':agg_max,'MIN':agg_min,'MODE':agg_mode}
"""
Dictionary of supported aggregation types.

    * AVG : 'SQLite','runtime' supported
    * MAX : 'SQLite','runtime' supported
    * MIN : 'SQLite','runtime' supported
    * MODE : only 'runtime' supported
        
"""



    