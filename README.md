# fire-gama
FireDb Gama import/export plugin til fire-cli (https://github.com/Kortforsyningen/fire-cli)

### Forudsætninger
Python 3+  
Installér https://github.com/Septima/fikspunktsregister  
Installér https://github.com/Kortforsyningen/fire-cli  
installér click (pip install click)

## Installér
Installér https://github.com/Septima/fikspunktsregister  

## Brug

fire gama KOMMANDO [PARAMETRE]

```
fire gama --help

Kommandoer:
  read   Indlæs en gama output fil (fire gama read --help)  
  write  Skab en gama input file fra fire (fire gama write --help)
```
### parametre til write  

```
fire gama write --help

  -o, --out FILENAME             Navn på gama input, der skal skabes (.xml) [default: output.xml]  
  -g, --geometri TEXT            wkt. Anvendes som geometri i udvælgelsen af observationer  
  -gf, --geometrifil FILENAME    Fil, som indeholder en wkt-streng. Anvendes som geometri i udvælgelsen af observationer  
  -b, --buffer INTEGER           Den buffer omkring den givne geometri som skal bruges i udvælgelsen af observationer [default: 0]  
  -df, --fra DATE                Fra-dato, som bruges i udvælgelsen af observationer  
  -dt, --til DATE                Til-dato, som bruges i udvælgelsen af observationer  
  -f, --fixpunkter TEXT          Komma-separeret liste af punkt-id'er, som skal fastholdes  
  -ff, --fixpunkterfil FILENAME  Fil, som indeholder komma-separeret liste af punkt-id'er, som skal fastholdes  
  -pf, --parameterfil FILENAME   Fil, som indeholder netværks-parametre og -attributter  [required]  
  --help                         Show this message and exit.  
```
#### format på parameterfil  

Parameter-filen er en .ini-fil med følgende indhold:  
```
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
```  

Kopiér og tilpas eventuelt https://raw.githubusercontent.com/Septima/fire-gama/master/fire-gama.ini


### Database-forbindelse  
  
Læs venligst https://github.com/Kortforsyningen/fire-cli#konfigurationsfil   
