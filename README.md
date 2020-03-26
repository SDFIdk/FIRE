# FIRE - FIkspunktRegister

Dette repository indeholder al kode og andet materiale der relaterer sig til forretningssystemet bag SDFE's
fikspunktregister. 

Repositoriet omfatter

- Et Python API-kode til interaktion med den bagvedliggende database (`fire.api`) samt til at læse og skrive
  [GNU Gama](https://www.gnu.org/software/gama/) filer (`fire.api.gama`).
- En kommandolinjeapplikationen `fire`, der indeholder en række brugbare underapplikationer, såsom `fire info`.
- Et QGIS plugin kaldet `flame`, der tilbyder en grafisk brugerflade til fikspunktsregisteret og beregningsprogrammel
