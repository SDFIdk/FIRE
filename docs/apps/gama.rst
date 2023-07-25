fire gama
==========

.. deprecated:: 1.6

Kommandogruppen :program:`fire gama` tilbyder mulighed for udtræk
og indlæsning af nivellementsobservationer og beregningsresultater.

Funktionaliteten er ikke vedligeholdt og blev indført som noget af
det første da FIRE oprindeligt blev udviklet. Tilsvarende, og bedre,
funktionalitet tilbydes med :ref:`kommandolinjeprogrammer_niv`
programmerne.

.. program-output:: fire gama --help

.. warning::

    Kommandogruppen forventes at blive fjernet i en kommende version
    af FIRE programpakken.

Parameterfil
------------

Parameter-filen er en .ini-fil med følgende indhold

.. code-block:: ini

  [network-attributes]
  axes-xy=en
  angles=left-handed
  epoch=0.0

  [network-parameters]
  algorithm=gso
  angles=400
  conf-pr=0.95
  cov-band=0
  ellipsoid=grs80
  latitude=55.7
  sigma-act=apriori
  sigma-apr=1.0
  tol-abs=1000.0
  update-constrained-coordinates=no

  [points-observations-attributes]


.. click:: fire.cli.gama:read
  :prog: fire gama read
  :nested: full

.. click:: fire.cli.gama:write
  :prog: fire gama write
  :nested: full
