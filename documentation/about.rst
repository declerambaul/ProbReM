

.. |probrem| replace:: **P**\ rob\ **R**\ e\ **M**

.. _referencesPRM:

About |probrem|
===========================

A Probabilistic Relational Model (PRM), [1]_, [2]_, is a directed probabilistic graphical model used in the field of  Statistical Relational Learning (SRL). PRMs define a language that can be used to describe the relationships - structural and probabilistic - between classes and variables, and thus allows representing dependencies between sets of objects. Heckerman et al. [4]_ introduced the directed acyclic probabilistic entity-relationship (DAPER) model which is based on the entity-relationship model used to design relational databases.
|probrem| is built on the DAPER specification of a PRM, thus it requires the data to be modelled with a entity-relationship diagram. The  probabilistic structure defines the dependencies among the probabilistic attributes of the entity-relationship model. 
The parent and the child attribute of a dependency can be associated with different entities or relationships; Getoor et al. refer to the path from child to parent attribute the *slotchain* whereas Heckerman et al. associate a more general *constraint* with the dependency instead.  The traditional *slotchain* is the most common *constraint*, |probrem| makes use of both expressions depending which one is more appropriate in the context.
Relationships are either of type `1:n` or `m:n`, therefore it is possible that attribute objects have multiple parent attribute objects for the same probabilistic dependency. Aggregation of the parent attribute objects is a common way to deal with this problem, |probrem| allows to define `generic aggregation functions` (avg, min, max).
Different inference methods have been implemented, all of which are based on `Markov Chain Monte Carlo <http://en.wikipedia.org/wiki/Markov_chain_Monte_Carlo>`_ methods. The paper `An Approach to Inference in Probabilistic Relational Models using Block Sampling` [6]_ - the first publication making use of |probrem| - details the basic inference algorithm used. Please see :ref:`Extensions <extensions>` for current and future work. 

The section :ref:`Using ProbReM<using_probrem>` illustrates the approach used in |probrem|, and the :ref:`example model<example_model>` is a walkthrough with an applied example. For theoretical background, we recommend `Introduction to Statistical Relational Learning` [3]_ by Lise Getoor \& Ben Taskar for an excellent introduction to the different approaches introduced in the SRL field. For more background on using `MCMC` in graphical models, D. Koller \& N. Friedman's `Probabilistic Graphical Models: Principles and Techniques` [5]_ is an excellent reference.


.. _relatedResearch:

Related Research
^^^^^^^^^^^^^^^^^^^^

Many different approaches are pursued in relational learning, below an incomplete list of frameworks that have already been published. 

* `Alchemy <http://alchemy.cs.washington.edu/>`_ by `Pedro Domingos <http://www.cs.washington.edu/homes/pedrod/>`_'s research group at the University of Washington. 
* `Primula <http://www.cs.aau.dk/~jaeger/Primula/>`_  by `Manfred Jaeger <http://www.cs.aau.dk/~jaeger/>`_ at the Aalborg university in Denmark.
* `BLOG <http://people.csail.mit.edu/milch/blog/>`_ by `Brian Milch <http://sites.google.com/site/bmilch/>`_ 
* `IBAL <http://www.eecs.harvard.edu/~avi/IBAL/>`_ by `Avi Pfeffer <http://www.eecs.harvard.edu/~avi/>`_ at Harvard


For a more complete list and more information and about other frameworks, `Manfred Jaeger <http://www.cs.aau.dk/~jaeger/>`_ has started a `Comparative Study of Probabilistic Logic Languages and Systems <http://www.cs.aau.dk/~jaeger/plsystems/>`_ that serves as platform to compare different approaches on different challenge problems. 


.. _publications:

Publications
^^^^^^^^^^^^^^^^^^^^

* Kaelin, Fabian and Precup, Doina. An Approach to Inference in Probabilistic Relational Models using Block Sampling. Asian Conference on Machine Learning, 2010. 325-340.



.. _references:

References
^^^^^^^^^^^^^^^^^^^^

.. [1] 
    N. Friedman, L. Getoor, D. Koller, and A. Pfeffer. Learning probabilistic relational models. 
    In IJCAI, pages 1300–1309, 1999.

.. [2] 
    Lise Getoor. Learning probabilistic relational models. In SARA ’02: Proceedings of the 4th Interna- tional
    Symposium on Abstraction, Reformulation, and Approximation, pages 322–323. Springer- Verlag, 2000.

.. [3] 
    Lise Getoor and Ben Taskar. Introduction to Statistical Relational Learning (Adaptive Computation and
    Machine Learning). The MIT Press, 2007.

.. [4] 
    D. Heckerman, C. Meek, and D. Koller. Probabilistic models for relational data. Technical Report 
    MSR-TR-2004-30, Microsoft Research, 2004.

.. [5]
    D. Koller and N. Friedman. Probabilistic Graphical Models: 
    Principles and Techniques. MIT Press, 2009.

.. [6]
    Kaelin, Fabian and Precup, Doina. An Approach to Inference in Probabilistic Relational Models using 
    Block Sampling. Asian Conference on Machine Learning, 2010. 325-340.

