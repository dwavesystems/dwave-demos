Demo of the MIQUBO Method of Feature Selection
==============================================

Statistical and machine-learning models use a set of input variables (features)
to predict output variables of interest. `Feature selection`_, which can be
part of the model design process, simplifies the model and reduces dimensionality by selecting,
from a given set of potential features, a subset of highly informative ones. One
statistical criterion that can guide this selection is `mutual information`_ (MI).

Ideally, to select the :math:`k` most relevant features, you might maximize :math:`I({X_s}; Y)`,
the MI between a set of :math:`k` features, :math:`X_s`, and the variable of interest, :math:`Y`.
This is a hard calculation because the number of states is exponential with :math:`k`.

The Mutual Information QUBO (`MIQUBO`_\ ) method of feature selection formulates a quadratic
unconstrained binary optimization (QUBO) based on an approximation for :math:`I({X_s}; Y)`,
which is submitted to the D-Wave quantum computer for solution.

The demo illustrates the MIQUBO method by finding an optimal feature set for predicting
survival of Titanic passengers. It uses records provided in file
formatted_titanic.csv, which is a feature-engineered version of a public database of
passenger information recorded by the ship's crew (in addition to a column showing
survival for each passenger, it contains information on gender, title, class, port
of embarkation, etc). Its output is a ranking of subsets of features that have
high MI with the variable of interest (survival) and low redundancy.

.. For more information about MIQUBO and the concepts used in this demo, see the
   Leap demo and Jupyter Notebook. 

Setting Up the Demo
-------------------

Copy (clone) this demo repository to your local machine.

The demo has the Ocean SDK as a dependency. Typically the demo is installed in a virtual
environment in which the `SDK is installed`_.

`Access to a D-Wave system`_ must be configured.

Running the Demo
----------------

.. code-block:: bash

  python titanic.py

License
-------

Released under the Apache License 2.0

.. _`Feature selection`: https://en.wikipedia.org/wiki/Feature_selection
.. _`mutual information`: https://en.wikipedia.org/wiki/Mutual_information
.. _`dwave-cloud-client`: http://dwave-cloud-client.readthedocs.io/en/latest/#module-dwave.cloud.config
.. _`SDK is installed`: https://docs.ocean.dwavesys.com/en/latest/overview/install.html
.. _`Access to a D-Wave system`: https://docs.ocean.dwavesys.com/en/latest/overview/dwavesys.html

.. _MIQUBO:

MIQUBO
------

PLACEHOLDER DRAFT:

As described above, to select the :math:`k` most relevant features, you might maximize
:math:`I({X_s}; Y)`, the MI between a set of :math:`k` features, :math:`X_s`, and the
variable of interest, :math:`Y`. Given :math:`N` features out of which you select
:math:`k`, maximize mutual information, I, as

.. math::

    {X_1, X_2, ...X_k} = \arg \max I(X_k; Y)

by expanding,

.. math::

    I(X_k;Y) = N^{-1} \sum_i \left\{ I(X_i;Y) + I(X_{k(i)};Y|X_i) \right\}

Approximate the second term by assuming conditional independence:

.. math::

    I(X_k;Y|X_i) \approx \sum_{j \in X_k(i)} I(X_j;Y|X_i)

Using the following equations for Shannon entropy,

.. math::

    H(X) = -\sum_x P(x)\mathrm{log}P(x)

    H(X|Y) = H(X,Y)-H(Y)

You can then calculate all these terms as follows:

.. math::

     I(X;Y) = H(X)-H(X|Y)

     I(X;Y|Z) = H(X|Z)-H(X|Y,Z)

The approximated equation for MI can now be formed as a QUBO:

.. math:
    {X_1, X_2, ...X_k} = \arg \max \left\{MI - Penalty}

where the penalty is some multiple of :math:`\sum_{i} (x_i - k)^2` that enforces
the constraint of :math:`k` features.


To be obsoleted:
----------------

main file: File Titanic_FS.ipynb
write up: [Quantum Annealing Feature Selection](https://confluence.dwavesys.com/x/JzaiAg)
