.. _kommandolinjeprogrammer_mtl:

================================================================================
fire mtl
================================================================================

.. Index:: apps

.. only:: html

Program til digitalisering, databaseopdatering og beregning af markarbejde (revision og opmåling). ::
	
	fire mtl [OPTIONS] COMMAND [ARGS] ...

Programkald
--------------

For at se hvilke valgmuligheder man har i *fire mtl*, køres kaldet::

	> fire mtl --help
	
eller uden parametre (options)::
 
	> fire mtl


Herfra ses en liste af parametre og kommandoer (commands), som man kan benytte, eller få mere information fra vha. *--help*-parameteren. 
	
Parametre
-----------------
.. option:: --help <n>

Vis denne hjælpetekst


Kommandoer 
--------------
Listen udbygges løbende efter behov, og indeholder bl.a.

============  =================================
**Kommando**  **Beskrivelse**
------------  ---------------------------------
indlæs        Importer data fra observationsfiler og opbyg punktoversigt
regn          Udfør netanalyse og beregn nye koter
============  =================================
	
Mere information kan opnås ved at tilføje *--help*-parameteren, fx ved::
 
	> fire mtl regn --help


