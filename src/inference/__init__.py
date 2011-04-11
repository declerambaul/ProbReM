"""
The package `inference` contains modules that implement different inference methods as well as helper modules:

* :mod:`inference.engine` handles the interaction between the submodules, configures the inference engine (e.g. specifies the inference algo)
* :mod:`inference.query` specifies a query language
* :mod:`inference.mcmc` implements `MCMC` based algorithms
    * :mod:`inference.mcmc.gibbs` implements a `GIBBS` sampler
    * :mod:`inference.mcmc.posterior` collects the posterior samples for a given query as well. It also implements various convergence diagnostics
    * :mod:`inference.mcmc.likelihood` offers a data structure to access the `conditional likelihood functions` of probablistic attributes


:mod:`~!inference.engine` module
-----------------------------------------

.. automodule:: inference.engine
    :members:

:mod:`~!.query` module
------------------------

.. automodule:: inference.query
    :members:
    

:mod:`~!.mcmc` module
------------------------

.. automodule:: inference.mcmc
    :members:


"""