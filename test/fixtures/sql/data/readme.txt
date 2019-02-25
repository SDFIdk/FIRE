Der er kun medtaget tabeller som indeholder data
Data er begrænset til de 10000 senest tilkomne punkter
Data er dannet på baggrund af DDL af 2019-02-01 - se evt. udfordringer med DDL nederst. 

Rækkefølge for import
FIRE_ADM.SAG.sql
FIRE_ADM.SAGSINFO.sql
FIRE_ADM.EVENTTYPE.sql
FIRE_ADM.SAGSEVENT.sql
FIRE_ADM.SAGSEVENTINFO.sql
FIRE_ADM.SAGSEVENTINFO_HTML.sql
FIRE_ADM.SAGSEVENTINFO_MATERIALE.sql
FIRE_ADM.PUNKTINFOTYPENAMESPACE.sql
FIRE_ADM.PUNKTINFOTYPE.sql
FIRE_ADM.SRIDNAMESPACE.sql
FIRE_ADM.SRIDTYPE.sql
FIRE_ADM.PUNKT.sql
FIRE_ADM.PUNKTINFO.sql
FIRE_ADM.KOORDINAT.sql
FIRE_ADM.GEOMETRIOBJEKT.sql
FIRE_ADM.OBSERVATION.sql
FIRE_ADM.BEREGNING.sql
FIRE_ADM.BEREGNING_KOORDINAT.sql
FIRE_ADM.BEREGNING_OBSERVATION.sql

Udfordringer med DLL
Ingen udfordringer udover, at insertFireRows.sql IKKE skal afvikles. Kun DDL skal afvikles. Desuden skal objectid fjernes, der er vist et script til det.

