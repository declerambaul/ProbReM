'''
Visualization Module :mod:`analytics.visualization`
---------------------------------------------------------------


The :mod:`!analytics.visualization` module can be used to create desciption files for graph visualization software. Note that the networks tend to be very large and thus creating meaningful graphs is usually not trivial nor useful.


'''

import time
import numpy as N
from analytics.gvgen import GvGen

def createGraphvizFile(GBNgraph):
    """Generates a description file `reports/gbn.dot` for the `GraphViz <http://www.graphviz.org/>`_ software. It makes use of `GvGen` written by Sebastien Tricaud.
    
    :arg GBNgraph: :class:`network.groundBN.GBNGraph`
    """
        
    graph = GvGen()

    graph.smart_mode = 1
    
    nodes = {}
    attNodes = {}

    graph.styleDefaultAppend("color","black")
    
    graph.styleAppend("event", "color", "red")
    graph.styleAppend("event", "style", "filled")
    graph.styleAppend("evidence", "color", "blue")
    graph.styleAppend("evidence", "style", "filled")
    #graph.styleAppend("event", "shape", "rectangle")
    
    
    #Nodes with attribute boxes
    for (attr,gbnVs) in GBNgraph.allByAttribute.items():
        attNodes[attr] = graph.newItem(attr.name)
        for gbnV in gbnVs:
            nodes[gbnV] = graph.newItem(gbnV.ID,attNodes[attr])
            
            if gbnV.ID in GBNgraph.eventVertices: 
                graph.styleApply("event", nodes[gbnV])
            
            if gbnV.fixed: 
                graph.styleApply("evidence", nodes[gbnV])
            

    #Nodes without attribute boxes
    # for gbnV in GBNgraph.values(): 
    #     nodes[gbnV] = graph.newItem(gbnV.ID)

        
    #Edges
    for gbnV in GBNgraph.values(): 
        for paVs in  gbnV.parents.values():
            for paV in paVs:
                graph.newLink(nodes[paV],nodes[gbnV])
                
                if paV.ID in GBNgraph.eventVertices:
                    graph.propertyForeachLinksAppend(nodes[paV], "color", "red")
            

    
    # Example Code
    # 
    # parents = graph.newItem("Parents")
    # father = graph.newItem("Bob", parents)
    # mother = graph.newItem("Alice", parents)
    # children = graph.newItem("Children")
    # child1 = graph.newItem("Carol", children)
    # child2 = graph.newItem("Eve", children)
    # child3 = graph.newItem("Isaac", children)
    # postman = graph.newItem("Postman")
    # graph.newLink(father,child1)
    # graph.newLink(child1, father)
    # graph.newLink(father, child1)
    # graph.newLink(father,child2)
    # graph.newLink(mother,child2)
    # myl = graph.newLink(mother,child1)
    # graph.newLink(mother,child3)
    # graph.newLink(postman,child3,"Email is safer")
    # graph.newLink(parents, postman)    # Cluster link
    # 
    # graph.propertyForeachLinksAppend(parents, "color", "blue")
    # 
    # graph.propertyForeachLinksAppend(father, "label", "My big link")
    # graph.propertyForeachLinksAppend(father, "color", "red")
    # 
    # graph.propertyAppend(postman, "color", "red")
    # graph.propertyAppend(postman, "fontcolor", "white")
    # 
    # graph.styleAppend("link", "label", "mylink")
    # graph.styleAppend("link", "color", "green")
    # graph.styleApply("link", myl)
    # graph.propertyAppend(myl, "arrowhead", "empty")
    # 
    # graph.styleAppend("Post", "color", "blue")
    # graph.styleAppend("Post", "style", "filled")
    # graph.styleAppend("Post", "shape", "rectangle")
    # graph.styleApply("Post", postman)


    graph.dot(open('reports/gbn.dot','w'))
    
   
def displayGraph(graph):
    """Plots the graph using `NetworkX <http://networkx.lanl.gov/>`_. 
    
    :arg graph: :class:`network.groundBN.GBNGraph`
    """ 
    
    import networkx as nx
    import pylab as P
    
    G = nx.DiGraph()

    #G.add_nodes_from(mcmcInference.GBN.values())

    for v in graph.values():
        for p in v.parents:
            G.add_edge(p.ID, v.ID)
            #G.add_edge(p, v)


    #print G.nodes()

    #print G.edges()

    #nx.draw(G,font_size=0)
    nx.draw_spring(G,font_size=10)
    P.show()


def plotAttrCPD(attr):
	"""
	Displayes the CPD of the :class:`~!.Attribute` `attr` using `matplotlib`. If `attr` has parents and thus different possible parent assigments, the method attempts to display a separate line for each assignment. It is safe to say that this doesn't scale well.
	
	:arg attr: :class:`.Attribute` 
	"""
	
	print 'Create plot for attribute %s'%(attr.fullname())
	
	hold(True)
	lines = []
	labels = []
	for i in range(0,attr.CPD.parentAssignments):
		if len(attr.parents)==1:
			labels.append('%s'%(attr.parents[0].domain[i]))
		lines.append(plot(attr.CPD.cpdMatrix[i,:])) 
	if len(attr.parents)==1:
		figlegend( lines,labels,'upper right' )    
	show()
