.. singlet documentation master file, created by
   sphinx-quickstart on Tue Aug  8 11:15:11 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/logo.png
   :width: 150
   :alt: t-SNE example

singlet
=======
Single cell RNA-Seq analysis with quantitative phenotypes.

Rationale
------------
Singlet's specialty is dealing with single cell **quantitative phenotypes**: these are numerical properties of the single cells that enrich the usual transcript abundances. A few examples:

- pathogen abundance in infected cells (`link1 <https://doi.org/10.7554/eLife.32942>`_, `link2 <https://doi.org/10.7554/eLife.32303>`_, `link3 <https://doi.org/10.1128/JVI.01778-18>`_)
- membrane potentials and other electrophysiology measurements (`link1 <https://www.biorxiv.org/content/10.1101/555110v1>`_)
- cell morphology (`link1 <https://doi.org/10.1186/s13059-018-1607-x>`_)
- cell localization in a tissue (`link1 <https://spatialtranscriptomics.com/>`_)

All these things are not part of a standard scRNA-Seq dataset. However, if combined with transcriptomics, they can help greatly in understanding the biology of a heterogeneous cell population, so experimental protocols for these are rapidly becoming common. The bottleneck then becomes data analysis, hence: singlet.


Tutorial
--------
Please follow this link_ to learn how to use singlet.


Requirements
------------
Python 3.4+ is required. Moreover, you will need:

- `pyyaml <https://pyyaml.org/>`_
- `numpy <http://www.numpy.org/>`_
- `scipy <https://www.scipy.org/>`_
- `pandas <http://pandas.pydata.org/>`_
- `xarray <http://xarray.pydata.org/en/stable/>`_
- `scikit-learn <http://scikit-learn.org>`_

Optional requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- `matplotlib <https://matplotlib.org/>`_
- `seaborn <https://seaborn.pydata.org/>`_
- `numba <https://numba.pydata.org/>`_
- `umap <https://github.com/lmcinnes/umap>`_
- `lshknn <https://github.com/iosonofabio/lshknn>`_
- `loompy <http://loompy.org/>`_

Get those from pip, conda, or any other source.

Install
-------
To get the latest **stable** version, use pip::

  pip install singlet

To get the latest **development** version, clone the git repo and then call::

  python3 setup.py install

Usage example
-------------
You can have a look inside the `test` folder for examples. To start using the example dataset:

- Set the environment variable `SINGLET_CONFIG_FILENAME` to the location of the example YAML file
- Open a Python/IPython shell and type:

.. code-block:: python

  from singlet.dataset import Dataset
  ds = Dataset(
          samplesheet='example_sheet_tsv',
          counts_table='example_table_tsv')

  ds.counts = ds.counts.iloc[:200]
  vs = ds.dimensionality.tsne(
          n_dims=2,
          transform='log10',
          theta=0.5,
          perplexity=0.8)
  ax = ds.plot.scatter_reduced_samples(
          vs,
          color_by='quantitative_phenotype_1_[A.U.]')
  plt.show()

This will calculate a t-SNE embedding of the first 200 features and then show your samples in the reduced space. It should look like this:

.. image:: _static/example_tsne.png
   :width: 600
   :alt: t-SNE example

.. note:: The figure looks different on OSX, but no worries, if you got there without errors chances are all is working correctly!

Contents
-------------
.. toctree::
   :maxdepth: 1
   :glob:

   examples
   config
   api


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _link: tutorial
