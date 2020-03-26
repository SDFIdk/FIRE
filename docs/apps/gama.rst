.. click:: fire.cli.gama:gama
  :prog: fire gama
  :show-nested:

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
