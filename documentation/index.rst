.. ProbReM documentation master file, created by
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
   
   
.. |probrem| replace:: **P**\ rob\ **R**\ e\ **M**   
.. _contact: fabian.kaelin\@mail.mcgill.ca

Welcome to ProbReM!
===================================


..
    .. WARNING::

        This is a very new framework which was released in December 2010. It is sure to contain bugs. Please `contact`_ us if you are interested in using/extending the existing framework.


|probrem| is a framework for modelling relational data using Probabilistic Relational Models (\ **PRM**\ s). 

Several :ref:`frameworks<relatedResearch>` have so far been proposed in Statistical Relational Learning, we hope to contribute to these efforts. |probrem| allows to model relational domains in the form of a directed graphical model which is specified in XML; the data lives in a relational database. 

* It is based on the Directed Acyclic Probabilistic Entity Relationship (DAPER) model
* It supports discrete variables
* The parameters of the model can be learned using a Maximum Likelihood (ML) estimate 
* Generic aggregation functions (e.g. average, min, max, mode) are used for nodes with multiple parents for one dependency
* Markov Chain Monte Carlo (MCMC) methods are used for approximate inference


|probrem| is being developed by `Fabian Kaelin <http://cs.mcgill.ca/~fkaeli>`_ at `McGill University <http://mcgill.ca/>`_ and the `National Institute of Informatics <http://www.nii.ac.jp/en/?page_id=59&lang=english>`_. This software is free to use for academic research only.



Content
==================


The documentation is organized as follows:

.. toctree::
    :maxdepth: 1
        
    about.rst
    
    using.rst
    example.rst
    
    extensions.rst    
    
    reference.rst
    

    



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

