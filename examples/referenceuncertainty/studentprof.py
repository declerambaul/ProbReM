'''
Reference Uncertainty

Student-Professor example from the Pasula/Stuart paper

'''
import sys
import logging

# if the the current folder is a sub folder or the root Probrem foler, otherwise supply the full path to the 'Probrem/src' folder
sys.path.append("./../../src")


import probrem

from ui import config
from ui import cmd
from analytics import performance
from analytics import visualization

'''  
THINGS TO THAT NEED TO BE INSTANTIATED: 

    PRM : probrem.PRM
    Data Interface : probrem.DI
    Learners : probrem.learners
    Inference : probrem.engine
'''

''' PRM '''
prmSpec = "./model/studentprofPRM.xml"    
config.loadPRM(prmSpec)


''' DATA INTERFACE '''
diSpec = "./model/studentprofDI.xml"
config.loadDI(diSpec)


''' LEARNERS '''
#we load a cpd learner to learn the CPDs for our attributes          
probrem.learners['ourCPDlearner'] = config.loadLearner('CPDTabularLearner')
# for ease of use
ourCPDlearner = probrem.learners['ourCPDlearner']

#we learn the distributions for all attributes
# ourCPDlearner.learnCPDsFull(saveDistributions=False,forceLearning=True)
# cmd.displayCPDs()

''' CONFIGURE INFERENCE ENGINE  '''
# assigne inference algorithm to engine 
# infAlgo = 'GIBBS
infAlgo = 'MH'
config.loadInferenceAlgorithm(infAlgo)
# for ease of use
mcmcInference = probrem.engine.inferenceAlgo

logging.info('====================================================================================')


from inference.query import *

event = [createQvar(attrName='Student.success', objsConstraint='incl', objsPkValues=[(1,)])]
evidence = [createQvar(attrName='Professor.funding', objsConstraint='incl', objsPkValues=[(1,),(2,),(3,),(4,),(5,),(6,),(7,),(8,),(9,),(10,)]), # ,(3,)
            createQvar(attrName='Professor.fame', objsConstraint='incl', objsPkValues=[(1,),(2,),(3,),(4,),(5,),(6,),(7,),(8,),(9,),(10,)]),
            #createQvar(attrName='advisor.exist', objsConstraint='incl', objsPkValues=[(2,1),(1,2),(3,3)])
            ]

# event = [   createQvar(attrName='Professor.funding', objsConstraint='incl', objsPkValues=[(1,),(3,),(2,)]),
#             createQvar(attrName='Professor.fame', objsConstraint='incl', objsPkValues=[(1,),(3,),(2,)]),
#             createQvar(attrName='advisor.exist', objsConstraint='incl', objsPkValues=[(1,1),(1,2),(1,3)])]
# evidence = [#createQvar(attrName='Professor.funding', objsConstraint='incl', objsPkValues=[(1,),(3,),(2,)]),
#             #createQvar(attrName='Professor.fame', objsConstraint='incl', objsPkValues=[(1,),(3,),(2,)]),
#             createQvar(attrName='Student.success', objsConstraint='incl', objsPkValues=[(1,)])
#             ]


query = Query(event,evidence)

# if the dependency for the exist variable is removed, the loaded CPD is incorrect -> overwriting to uniform prior
# probrem.PRM.attributes['advisor.exist'].CPD.cpdMatrix[0,1]=0.5
# probrem.PRM.attributes['advisor.exist'].CPD.cpdMatrix[0,0]=0.5



#  setting inference parameters
mcmcInference.ITER = 1000
mcmcInference.BURNIN = 500
mcmcInference.CHAINS = 10


probrem.engine.infer(query)


# convenience
GBN = probrem.engine.GBN



def showCumMean():
	for i,v in enumerate(GBN.samplingVertices.values()):
		mcmcInference.posterior.plotCumulativeMeanAllChains(gbnV=v)		




def compSucces():

	s = GBN['Student.success.1']
	mcmcInference.posterior.plotCumulativeMeanAllChains(gbnV=s)

	a = 0.7*0.2*0.8*0.4+0.2*0.2*0.8*0.4+0.2*0.8*0.8*0.6
	b = 0.3*0.2*0.8*0.4+0.8*0.2*0.8*0.4+0.8*0.8*0.8*0.6
	d = a/(a+b)

	f = mcmcInference.posterior.PL.gcf()
	f.axes[0].axhline(d)
	



# cmd.displayCPDs()

# showCumMean()


'''
Run Chains in parallel
Convergence diagnositc Rubin/Gelman?
Check Daphne Koller book


Calculate the aggregation/ k>1 parent assignment using the weighted conditional probability


Scale for N professors

Pub Dataset
'''


# to enter into an interactive ipython session
# cmd.ipythonShell()


#display the analystics that were gathered
#performance.displayTimeAnalysis()

# to display the current GBN 
#visualization.displayGraph(probrem.engine.GBN)
