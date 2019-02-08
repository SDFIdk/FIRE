# fire-gama
FireDb Gama import and export module and CLI

### Requirements
Python 3+  
Install https://github.com/Septima/fikspunktsregister  
install click (pip install click)

## Install
* Download and unpack https://github.com/Septima/fire-gama/archive/master.zip (Suggestion c:/tmp/fire-gama)
* pip install c:/tmp/fire-gama

## Usage

Usage: fire-gama [OPTIONS] COMMAND [ARGS]...

```
fire-gama --help

Commands:
  read   Read a gama output file (fire-gama read --help)  
  write  Create a gama input file (fire-gama write --help)
```

### Specifying database connection info

For both write and read the database connection string may be set _either_ by
* an option; -db user:pass@host:port/database
_or_ by
* prior to the command setting the environment varable _fire-db_

