'''
A module containing utils for handling data.

'''


class Discretizer:
    '''
    :class:`.Discretizer` can be used to discretize continuous data. `self.bins` is a list of values starting with the smallest possible value and ending with the largest possible value. All intervals in between are bins, e.g. when `discretize(self,value)` is called the index of the bin that `value` falls in is returned.
    '''
    
    def __init__(self, bins):
        '''
        bins : array of 
        '''
        self.bins =  bins
        self.bins_str = ['%s-%s'%(bins[i],bins[i+1]) for i in range(0,len(bins)-1)]
        
    def discretize(self,value):
        ind = None
        if value < self.bins[0]:
            raise Exception('Value %s out of bins range %s'%(value,self.bins[0]))
        for i,b in enumerate(self.bins):            
            if value <= b:
                return i
                
        if ind is None:    
            #if no value has been returned
            raise Exception('Value %s out of bins range %s'%(value,self.bins[-1]))
        else:
            return ind
         
    