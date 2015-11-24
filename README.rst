sphinxcontrib-apiblueprint
==========================

`sphinxcontrib-apiblueprint` is Sphinx extension to create API docs using `API Blueprint`_

.. _API Blueprint: https://apiblueprint.org/

Usage
-----

Include this extension in conf.py::

    extensions = ['sphinxcontrib.apiblueprint']

Write ``apiblueprint`` directive into reST file where you want to import API doc::

    .. apiblueprint:: [path to API blueprint definition file]
