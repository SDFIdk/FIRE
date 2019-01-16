# fire-gama
FireDb Gama import and export module and CLI

### Requirements
Python 3+  
Install https://github.com/Septima/fikspunktsregister 
install click 

## Install
pip install firegama

## Usage

Usage: cli.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  read   Read a gama output file (read --help)
  write  Create a gama input file

### Specifying database connection info

For both write and read the database connection string may be set _either_ by
* an option; -db user:pass@host:port/database
_or_ by
* prior to the command setting the environment varable _fire-db_

### Write input file to gama
Create a gama input file

´´´
cli.py write [OPTIONS]

Options:
  -db TEXT                       Connection-streng til fire database.
                                 [default: environment variabel %fire-db%]
  -o, --out FILENAME             Navn på gama input, der skal skabes (.xml)
                                 [default: output.xml]
  -g, --geometri TEXT            wkt. Anvendes som geometri i udvælgelsen af
                                 observationer
  -gf, --geometrifil FILENAME    Fil, som indeholder en wkt-streng. Anvendes
                                 som geometri i udvælgelsen af observationer
  -b, --buffer INTEGER           Den buffer omkring den givne geometri som
                                 skal bruges i udvælgelsen af observationer
                                 [default: 0]
  -df, --fra DATE                Fra-dato, som bruges i udvælgelsen af
                                 observationer
  -dt, --til DATE                Til-dato, som bruges i udvælgelsen af
                                 observationer
  -f, --fixpunkter TEXT          Komma-separeret liste af punkt-id'er, som
                                 skal fastholdes
  -ff, --fixpunkterfil FILENAME  Fil, som indeholder komma-separeret liste af
                                 punkt-id'er, som skal fastholdes
  -pf, --parameterfil FILENAME   Fil, som indeholder netværks-parametre og
                                 -attributter  [default: fire-gama.ini]
  --help                         Show this message and exit.
´´´


### Environment variable

## Test

###python


### CLI 
