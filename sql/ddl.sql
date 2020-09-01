CREATE TABLE BEREGNING (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   SAGSEVENTFRAID VARCHAR2(36) NOT NULL,
   SAGSEVENTTILID VARCHAR2(36)
);

CREATE TABLE BEREGNING_KOORDINAT (

   BEREGNINGOBJEKTID INTEGER NOT NULL,
   KOORDINATOBJEKTID INTEGER NOT NULL,
   PRIMARY KEY (BEREGNINGOBJEKTID, KOORDINATOBJEKTID)
);

CREATE TABLE BEREGNING_OBSERVATION (

   BEREGNINGOBJEKTID INTEGER NOT NULL,
   OBSERVATIONOBJEKTID INTEGER NOT NULL,
   PRIMARY KEY (BEREGNINGOBJEKTID, OBSERVATIONOBJEKTID)
);

CREATE TABLE EVENTTYPE (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   BESKRIVELSE VARCHAR2(4000) NOT NULL,
   EVENT VARCHAR2(4000) NOT NULL,
   EVENTTYPEID INTEGER NOT NULL
);

CREATE TABLE GEOMETRIOBJEKT (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   SAGSEVENTFRAID VARCHAR2(36) NOT NULL,
   SAGSEVENTTILID VARCHAR2(36),
   GEOMETRI SDO_GEOMETRY NOT NULL,
   PUNKTID VARCHAR2(36) NOT NULL
);

CREATE TABLE HERREDSOGN (
  OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
  KODE VARCHAR2(6) NOT NULL,
  GEOMETRI SDO_GEOMETRY NOT NULL
);

CREATE TABLE KOORDINAT (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   SAGSEVENTFRAID VARCHAR2(36) NOT NULL,
   SAGSEVENTTILID VARCHAR2(36),
   SRIDID INTEGER NOT NULL,
   SX NUMBER,
   SY NUMBER,
   SZ NUMBER,
   T TIMESTAMP WITH TIME ZONE NOT NULL,
   TRANSFORMERET VARCHAR2(5) NOT NULL,
   ARTSKODE INTEGER,
   X NUMBER,
   Y NUMBER,
   Z NUMBER,
   PUNKTID VARCHAR2(36) NOT NULL
);

CREATE TABLE KONFIGURATION (
  OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
  DIR_SKITSER VARCHAR(200) NOT NULL,
  DIR_MATERIALE VARCHAR(200) NOT NULL
);
-- Index sikrer at der kun kan indsættes een række i tabellen
CREATE UNIQUE INDEX only_one_row ON konfiguration ('1');

CREATE TABLE OBSERVATION (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   ID VARCHAR2(36) NOT NULL,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   VALUE1 NUMBER,
   VALUE2 NUMBER,
   VALUE3 NUMBER,
   VALUE4 NUMBER,
   VALUE5 NUMBER,
   VALUE6 NUMBER,
   VALUE7 NUMBER,
   VALUE8 NUMBER,
   VALUE9 NUMBER,
   VALUE10 NUMBER,
   VALUE11 NUMBER,
   VALUE12 NUMBER,
   VALUE13 NUMBER,
   VALUE14 NUMBER,
   VALUE15 NUMBER,
   SAGSEVENTFRAID VARCHAR2(36) NOT NULL,
   SAGSEVENTTILID VARCHAR2(36),
   OBSERVATIONSTYPEID INTEGER NOT NULL,
   ANTAL INTEGER NOT NULL,
   GRUPPE INTEGER,
   OBSERVATIONSTIDSPUNKT TIMESTAMP WITH TIME ZONE NOT NULL,
   OPSTILLINGSPUNKTID VARCHAR2(36) NOT NULL,
   SIGTEPUNKTID VARCHAR2(36)
);

CREATE TABLE OBSERVATIONSTYPE (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   OBSERVATIONSTYPEID INTEGER NOT NULL,
   OBSERVATIONSTYPE VARCHAR2(4000) NOT NULL,
   BESKRIVELSE VARCHAR2(4000) NOT NULL,
   SIGTEPUNKT VARCHAR2(5) NOT NULL,
   VALUE1 VARCHAR2(4000),
   VALUE2 VARCHAR2(4000),
   VALUE3 VARCHAR2(4000),
   VALUE4 VARCHAR2(4000),
   VALUE5 VARCHAR2(4000),
   VALUE6 VARCHAR2(4000),
   VALUE7 VARCHAR2(4000),
   VALUE8 VARCHAR2(4000),
   VALUE9 VARCHAR2(4000),
   VALUE10 VARCHAR2(4000),
   VALUE11 VARCHAR2(4000),
   VALUE12 VARCHAR2(4000),
   VALUE13 VARCHAR2(4000),
   VALUE14 VARCHAR2(4000),
   VALUE15 VARCHAR2(4000)
);

CREATE TABLE PUNKT (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   SAGSEVENTFRAID VARCHAR2(36) NOT NULL,
   SAGSEVENTTILID VARCHAR2(36),
   ID VARCHAR2(36) NOT NULL
);

CREATE TABLE PUNKTINFO (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   SAGSEVENTFRAID VARCHAR2(36) NOT NULL,
   SAGSEVENTTILID VARCHAR2(36),
   INFOTYPEID INTEGER NOT NULL,
   TAL NUMBER,
   TEKST VARCHAR2(4000),
   PUNKTID VARCHAR2(36) NOT NULL
);

CREATE TABLE PUNKTINFOTYPE (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   INFOTYPEID INTEGER NOT NULL,
   INFOTYPE VARCHAR2(4000) NOT NULL,
   ANVENDELSE VARCHAR2(9) NOT NULL,
   BESKRIVELSE VARCHAR2(4000) NOT NULL
);


CREATE TABLE SAG (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   ID VARCHAR2(36) NOT NULL,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE SAGSEVENT (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   ID VARCHAR2(36) NOT NULL,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   EVENTTYPEID INTEGER NOT NULL,
   SAGSID VARCHAR2(36) NOT NULL
);

CREATE TABLE SAGSEVENTINFO (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   BESKRIVELSE VARCHAR2(4000),
   SAGSEVENTID VARCHAR2(36) NOT NULL
);

CREATE TABLE SAGSEVENTINFO_HTML (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   HTML CLOB NOT NULL,
   SAGSEVENTINFOOBJEKTID INTEGER NOT NULL
);

CREATE TABLE SAGSEVENTINFO_MATERIALE (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   MD5SUM VARCHAR2(32) NOT NULL,
   STI VARCHAR2(4000) NOT NULL,
   SAGSEVENTINFOOBJEKTID INTEGER NOT NULL
);

CREATE TABLE SAGSINFO (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   AKTIV VARCHAR2(5) NOT NULL,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   JOURNALNUMMER VARCHAR2(4000),
   BEHANDLER VARCHAR2(4000) NOT NULL,
   BESKRIVELSE VARCHAR2(4000),
   SAGSID VARCHAR2(36) NOT NULL
);


CREATE TABLE SRIDTYPE (

   OBJEKTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   X VARCHAR2(4000),
   Y VARCHAR2(4000),
   Z VARCHAR2(4000),
   SRIDID INTEGER NOT NULL,
   SRID VARCHAR2(36) NOT NULL,
   BESKRIVELSE VARCHAR2(4000) NOT NULL
);


ALTER TABLE KOORDINAT ADD CONSTRAINT CK_KOORDINAT_TRANSFORMER248 CHECK (TRANSFORMERET IN ('true', 'false'));
ALTER TABLE OBSERVATIONSTYPE ADD CONSTRAINT CK_OBSERVATION_SIGTEPUNKT085 CHECK (SIGTEPUNKT IN ('true', 'false'));
ALTER TABLE PUNKTINFOTYPE ADD CONSTRAINT CK_PUNKTINFOTY_ANVENDELSE138 CHECK (ANVENDELSE IN ('FLAG', 'TAL', 'TEKST'));
ALTER TABLE SAGSINFO ADD CONSTRAINT CK_SAGSINFO_AKTIV060 CHECK (AKTIV IN ('true', 'false'));

INSERT INTO USER_SDO_GEOM_METADATA (TABLE_NAME, COLUMN_NAME, DIMINFO, SRID) VALUES ('GEOMETRIOBJEKT', 'GEOMETRI', MDSYS.SDO_DIM_ARRAY(MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005), MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)), 4326);
INSERT INTO USER_SDO_GEOM_METADATA (TABLE_NAME, COLUMN_NAME, DIMINFO, SRID) VALUES ('HERREDSOGN', 'GEOMETRI', MDSYS.SDO_DIM_ARRAY(MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005), MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)), 4326);

CREATE INDEX IDX_GEOMETRIOBJEKT_GEOMETRI ON GEOMETRIOBJEKT (GEOMETRI) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');
CREATE INDEX IDX_HERREDSOGN_GEOMETRI ON HERREDSOGN (GEOMETRI) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS ('layer_gtype=polygon');

COMMENT ON TABLE BEREGNING IS 'Sammenknytter beregnede koordinater med de anvendte observationer.';
COMMENT ON COLUMN BEREGNING.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN BEREGNING.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN BEREGNING.SAGSEVENTFRAID IS 'Angivelse af den hændelse der har bevirket registrering af et fikspunktsobjekt';
COMMENT ON COLUMN BEREGNING.SAGSEVENTTILID IS 'Angivelse af den hændelse der har bevirket afregistrering af et fikspunktsobjekt';
COMMENT ON COLUMN BEREGNING_KOORDINAT.KOORDINATOBJEKTID IS 'Udpegning af de koordinater der er indgået i en beregning.';
COMMENT ON COLUMN BEREGNING_OBSERVATION.OBSERVATIONOBJEKTID IS 'Udpegning af de observationer der er brugt i en beregning.';
COMMENT ON TABLE EVENTTYPE IS 'Objekt til at holde en liste over lovlige typer af events i fikspunktsforvaltningssystemet, samt en beskrivelse hvad eventtypen dækker over.';
COMMENT ON COLUMN EVENTTYPE.BESKRIVELSE IS 'Kort beskrivelse af en eventtype.';
COMMENT ON COLUMN EVENTTYPE.EVENT IS 'Navngivning af en eventtype.';
COMMENT ON COLUMN EVENTTYPE.EVENTTYPEID IS 'Identifikation af typen af en sagsevent.';
COMMENT ON TABLE GEOMETRIOBJEKT IS 'Objekt indeholdende et punkts placeringsgeometri.';
COMMENT ON COLUMN GEOMETRIOBJEKT.GEOMETRI IS 'Geometri til brug for visning i f.eks et GIS system.';
COMMENT ON COLUMN GEOMETRIOBJEKT.PUNKTID IS 'Punkt som har en placeringsgeometri tilknyttet.';
COMMENT ON COLUMN GEOMETRIOBJEKT.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN GEOMETRIOBJEKT.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN GEOMETRIOBJEKT.SAGSEVENTFRAID IS 'Angivelse af den hændelse der har bevirket registrering af et fikspunktsobjekt';
COMMENT ON COLUMN GEOMETRIOBJEKT.SAGSEVENTTILID IS 'Angivelse af den hændelse der har bevirket afregistrering af et fikspunktsobjekt';
COMMENT ON TABLE KOORDINAT IS 'Generisk 4D koordinat.';
COMMENT ON COLUMN KOORDINAT.PUNKTID IS 'Punkt som koordinaten hører til.';
COMMENT ON COLUMN KOORDINAT.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN KOORDINAT.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN KOORDINAT.SAGSEVENTFRAID IS 'Angivelse af den hændelse der har bevirket registrering af et fikspunktsobjekt';
COMMENT ON COLUMN KOORDINAT.SAGSEVENTTILID IS 'Angivelse af den hændelse der har bevirket afregistrering af et fikspunktsobjekt';
COMMENT ON COLUMN KOORDINAT.SRIDID IS 'Unik ID i fikspunktsforvaltningssystemet for et et koordinatsystem.';
COMMENT ON COLUMN KOORDINAT.SX IS 'A posteriori spredning på førstekoordinaten.';
COMMENT ON COLUMN KOORDINAT.SY IS 'A posteriori spredning på andenkoordinaten.';
COMMENT ON COLUMN KOORDINAT.SZ IS 'A posteriori spredning på tredjekoordinaten.';
COMMENT ON COLUMN KOORDINAT.T IS 'Observationstidspunktet.';
COMMENT ON COLUMN KOORDINAT.TRANSFORMERET IS 'Angivelse om positionen er målt, eller transformeret fra et andet koordinatsystem';
COMMENT ON COLUMN KOORDINAT.ARTSKODE IS 'Fra REFGEO. Værdierne skal forstås som følger:

 artskode = 1 control point in fundamental network, first order.
 artskode = 2 control point in superior plane network.
 artskode = 2 control point in superior height network.
 artskode = 3 control point in network of high quality.
 artskode = 4 control point in network of lower or unknown quality.
 artskode = 5 coordinate computed on just a few measurements.
 artskode = 6 coordinate transformed from local or an not valid coordinate system.
 artskode = 7 coordinate computed on an not valid coordinate system, or system of unknown origin.
 artskode = 8 coordinate computed on few measurements, and on an not valid coordinate system.
 artskode = 9 location coordinate or location height.

 Artskode er kun tilgængelig for koordinater der stammer fra REFGEO.';
COMMENT ON COLUMN KOORDINAT.X IS 'Førstekoordinat.';
COMMENT ON COLUMN KOORDINAT.Y IS 'Andenkoordinat.';
COMMENT ON COLUMN KOORDINAT.Z IS 'Tredjekoordinat.';
COMMENT ON TABLE OBSERVATION IS 'Generisk observationsobjekt indeholdende informationer om en observation.';
COMMENT ON COLUMN OBSERVATION.ANTAL IS 'Antal gentagne observationer hvoraf en middelobservationen er fremkommet.';
COMMENT ON COLUMN OBSERVATION.GRUPPE IS 'ID der angiver observationsgruppen for en observation der indgår i en gruppe.';
COMMENT ON COLUMN OBSERVATION.OBSERVATIONSTIDSPUNKT IS 'Tidspunktet hvor observationen er foretaget';
COMMENT ON COLUMN OBSERVATION.OBSERVATIONSTYPEID IS 'Identifikation af en observations type.';
COMMENT ON COLUMN OBSERVATION.OPSTILLINGSPUNKTID IS 'Udpegning af det punkt der er anvendt ved opstilling ved en observation.';
COMMENT ON COLUMN OBSERVATION.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN OBSERVATION.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN OBSERVATION.SAGSEVENTFRAID IS 'Angivelse af den hændelse der har bevirket registrering af et fikspunktsobjekt';
COMMENT ON COLUMN OBSERVATION.SAGSEVENTTILID IS 'Angivelse af den hændelse der har bevirket afregistrering af et fikspunktsobjekt';
COMMENT ON COLUMN OBSERVATION.SIGTEPUNKTID IS 'Udpegning af punkt der er sigtet til ved en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE1 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE10 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE11 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE12 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE13 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE14 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE15 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE2 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE3 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE4 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE5 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE6 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE7 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE8 IS 'En værdi for en observation.';
COMMENT ON COLUMN OBSERVATION.VALUE9 IS 'En værdi for en observation.';
COMMENT ON TABLE OBSERVATIONSTYPE IS 'Objekttype til beskrivelse af hvorledes en Observation skal læses, ud fra typen af observation.';
COMMENT ON COLUMN OBSERVATIONSTYPE.BESKRIVELSE IS 'Overordnet beskrivelse af denne observationstype.';
COMMENT ON COLUMN OBSERVATIONSTYPE.OBSERVATIONSTYPE IS 'Kortnavn for observationstypen, fx dH';
COMMENT ON COLUMN OBSERVATIONSTYPE.OBSERVATIONSTYPEID IS 'Identifikation af observationenst type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.SIGTEPUNKT IS 'Indikator for om Sigtepunkt anvendes for denne observationstype.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE1 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE10 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE11 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE12 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE13 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE14 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE15 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE2 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE3 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE4 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE5 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE6 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE7 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE8 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON COLUMN OBSERVATIONSTYPE.VALUE9 IS 'Beskrivelse af en observations værdis betydning for afhænging af observationens type.';
COMMENT ON TABLE PUNKT IS 'Abstrakt repræsentation af et fysisk punkt. Knytter alle punktinformationer sammen.';
COMMENT ON COLUMN PUNKT.ID IS 'Persistent unik nøgle.';
COMMENT ON COLUMN PUNKT.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN PUNKT.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN PUNKT.SAGSEVENTFRAID IS 'Angivelse af den hændelse der har bevirket registrering af et fikspunktsobjekt';
COMMENT ON COLUMN PUNKT.SAGSEVENTTILID IS 'Angivelse af den hændelse der har bevirket afregistrering af et fikspunktsobjekt';
COMMENT ON TABLE PUNKTINFO IS 'Generisk information om et punkt.';
COMMENT ON COLUMN PUNKTINFO.INFOTYPEID IS 'Unik ID for typen af Punktinfo.';
COMMENT ON COLUMN PUNKTINFO.PUNKTID IS 'Punktet som punktinfo er holder information om.';
COMMENT ON COLUMN PUNKTINFO.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN PUNKTINFO.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN PUNKTINFO.SAGSEVENTFRAID IS 'Angivelse af den hændelse der har bevirket registrering af et fikspunktsobjekt';
COMMENT ON COLUMN PUNKTINFO.SAGSEVENTTILID IS 'Angivelse af den hændelse der har bevirket afregistrering af et fikspunktsobjekt';
COMMENT ON COLUMN PUNKTINFO.TAL IS 'Værdien for numeriske informationselementer';
COMMENT ON COLUMN PUNKTINFO.TEKST IS 'Værdien for tekstinformationselementer';
COMMENT ON TABLE PUNKTINFOTYPE IS 'Udfaldsrum for punktinforobjekter med definition af hvordan PunktInfo skal læses og beskrivelse af typen af punktinfo.';
COMMENT ON COLUMN PUNKTINFOTYPE.ANVENDELSE IS 'Er det reelTal, tekst, eller ingen af disse, der angiver værdien';
COMMENT ON COLUMN PUNKTINFOTYPE.BESKRIVELSE IS 'Beskrivelse af denne informationstypes art.';
COMMENT ON COLUMN PUNKTINFOTYPE.INFOTYPE IS 'Arten af dette informationselement';
COMMENT ON COLUMN PUNKTINFOTYPE.INFOTYPEID IS 'Unik ID for typen af Punktinfo.';
COMMENT ON TABLE SAG IS 'Samling af administrativt relaterede sagshændelser.';
COMMENT ON COLUMN SAG.ID IS 'Persistent unik nøgle.';
COMMENT ON COLUMN SAG.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON TABLE SAGSEVENT IS 'Udvikling i sag som kan, men ikke behøver, medføre opdateringer af fikspunktregisterobjekter.';
COMMENT ON COLUMN SAGSEVENT.EVENTTYPEID IS 'Identifikation af typen af en sagsevent.';
COMMENT ON COLUMN SAGSEVENT.ID IS 'Persistent unik nøgle.';
COMMENT ON COLUMN SAGSEVENT.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN SAGSEVENT.SAGSID IS 'Udpegning af den sag i fikspunktsforvalningssystemet som en event er foretaget i.';
COMMENT ON TABLE SAGSEVENTINFO IS 'Informationer der knytter sig til en et sagsevent.';
COMMENT ON COLUMN SAGSEVENTINFO.BESKRIVELSE IS 'Specifik beskrivelse af den aktuelle fremdrift.';
COMMENT ON COLUMN SAGSEVENTINFO.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN SAGSEVENTINFO.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN SAGSEVENTINFO.SAGSEVENTID IS 'Den sagsevent som sagseventinfo har information om.';
COMMENT ON COLUMN SAGSEVENTINFO_HTML.HTML IS 'Generisk operatørlæsbart orienterende rapportmateriale.';
COMMENT ON TABLE SAGSEVENTINFO_MATERIALE IS 'Eksternt placeret materiale knyttet til en event';
COMMENT ON COLUMN SAGSEVENTINFO_MATERIALE.MD5SUM IS 'Sum brugt til at kontrollere materialets integritet.';
COMMENT ON COLUMN SAGSEVENTINFO_MATERIALE.STI IS 'Placering af materialet.';
COMMENT ON TABLE SAGSINFO IS 'Samling af administrativt relaterede sagshændelser.';
COMMENT ON COLUMN SAGSINFO.AKTIV IS 'Markerer om sagen er åben eller lukket.';
COMMENT ON COLUMN SAGSINFO.BEHANDLER IS 'Angivelse af en sagsbehandler.';
COMMENT ON COLUMN SAGSINFO.BESKRIVELSE IS 'Kort beskrivelse af en fikspunktssag.';
COMMENT ON COLUMN SAGSINFO.JOURNALNUMMER IS 'Sagsmappeidentifikation i opmålings- og beregningssagsregistret.';
COMMENT ON COLUMN SAGSINFO.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN SAGSINFO.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN SAGSINFO.SAGSID IS 'Den sag som sagsinfo holder information for.';
COMMENT ON TABLE SRIDTYPE IS 'Udfaldsrum for SRID-koordinatbeskrivelser.';
COMMENT ON COLUMN SRIDTYPE.BESKRIVELSE IS 'Generel beskrivelse af systemet.';
COMMENT ON COLUMN SRIDTYPE.SRID IS 'Den egentlige referencesystemindikator.';
COMMENT ON COLUMN SRIDTYPE.SRIDID IS 'Unik ID i fikspunktsforvaltningssystemet for et et koordinatsystem.';
COMMENT ON COLUMN SRIDTYPE.X IS 'Beskrivelse af x-koordinatens indhold';
COMMENT ON COLUMN SRIDTYPE.Y IS 'Beskrivelse af y-koordinatens indhold.';
COMMENT ON COLUMN SRIDTYPE.Z IS 'Beskrivelse af z-koordinatens indhold.';

-- Constraints og triggers ikke defineret i modellen
-- Constraint der tjekker at PUNKTID eksisterer i PUNKT tabellen inden en række
-- sættes ind i KOORDINAT-, OBSERVATION- og PUNKTINFO-tabellen
CREATE UNIQUE INDEX ID_IDX_0001 ON PUNKT (ID);

ALTER TABLE PUNKT ADD (
CONSTRAINT PUNKT_R01
UNIQUE (ID)
USING INDEX ID_IDX_0001
ENABLE VALIDATE);

CREATE UNIQUE INDEX ID_IDX_0002 ON OBSERVATION (ID);

ALTER TABLE OBSERVATION ADD (
  CONSTRAINT OBSERVATION_R02
  UNIQUE (ID)
  USING INDEX ID_IDX_0002
  ENABLE VALIDATE
);

CREATE UNIQUE INDEX SRIDTYPE_U01 ON SRIDTYPE (SRIDID);

ALTER TABLE SRIDTYPE ADD
CONSTRAINT SRIDTYPE_U01
UNIQUE (SRIDID)
USING INDEX SRIDTYPE_U01
ENABLE VALIDATE;

CREATE UNIQUE INDEX EVENTTYPE_U01 ON EVENTTYPE (EVENTTYPEID);

ALTER TABLE EVENTTYPE ADD
CONSTRAINT EVENTTYPE_U01
UNIQUE (EVENTTYPEID)
USING INDEX EVENTTYPE_U01
ENABLE VALIDATE;

-- Index der skal sikre at der til samme punkt ikke tilføjes en koordinat
-- med samme SRIDID, hvis denne ikke er afregistreret
CREATE UNIQUE INDEX KOOR_UNIQ_001 ON KOORDINAT (SRIDID, PUNKTID, REGISTRERINGTIL);


CREATE UNIQUE INDEX PUNKTINFOTYPE_IDX_01 ON PUNKTINFOTYPE (INFOTYPEID);

ALTER TABLE PUNKTINFOTYPE ADD
CONSTRAINT PUNKTINFOTYPE_U01
UNIQUE (INFOTYPEID)
USING INDEX PUNKTINFOTYPE_IDX_01
ENABLE VALIDATE;


CREATE UNIQUE INDEX OBSERVATIONSTYPE_IDX_001 ON OBSERVATIONSTYPE
(OBSERVATIONSTYPEID);

ALTER TABLE OBSERVATIONSTYPE ADD
CONSTRAINT OBSERVATIONSTYPE_U01
UNIQUE (OBSERVATIONSTYPEID)
USING INDEX OBSERVATIONSTYPE_IDX_001
ENABLE VALIDATE;


ALTER TABLE KOORDINAT ADD
CONSTRAINT KOORDINAT_R01
FOREIGN KEY (SRIDID)
REFERENCES SRIDTYPE (SRIDID)
ENABLE VALIDATE;

ALTER TABLE KOORDINAT ADD
CONSTRAINT PUNKTID_CON_0001
FOREIGN KEY (PUNKTID)
REFERENCES PUNKT (ID)
ENABLE VALIDATE;

ALTER TABLE OBSERVATION ADD
CONSTRAINT OBSERVATION_SP_CON_0001
FOREIGN KEY (SIGTEPUNKTID)
REFERENCES PUNKT (ID)
ENABLE VALIDATE;

ALTER TABLE OBSERVATION ADD
CONSTRAINT OBSERVATION_OP1_CON_0001
FOREIGN KEY (OPSTILLINGSPUNKTID)
REFERENCES PUNKT (ID)
ENABLE VALIDATE;

ALTER TABLE OBSERVATION ADD
CONSTRAINT OBSERVATION_R01
FOREIGN KEY (OBSERVATIONSTYPEID)
REFERENCES OBSERVATIONSTYPE (OBSERVATIONSTYPEID)
ENABLE VALIDATE;

ALTER TABLE PUNKTINFO ADD
CONSTRAINT PUNKTINFO_CON_001
FOREIGN KEY (PUNKTID)
REFERENCES PUNKT (ID)
ENABLE VALIDATE;

ALTER TABLE PUNKTINFO ADD
CONSTRAINT PUNKTINFO_R01
FOREIGN KEY (INFOTYPEID)
REFERENCES PUNKTINFOTYPE (INFOTYPEID)
ENABLE VALIDATE;

-- Diverse index

CREATE INDEX idx_punktinfo_pid ON punktinfo(punktid);
CREATE INDEX idx_koordinat_pid ON koordinat(punktid);
CREATE INDEX idx_geomobj_pid ON geometriobjekt(punktid);

CREATE INDEX idx_observ_opid ON observation(opstillingspunktid);
CREATE INDEX idx_observ_spid ON observation(sigtepunktid);

CREATE INDEX idx_punktinfotyp_anv ON punktinfotype(anvendelse);
CREATE INDEX idx_punktinfotyp_typ ON punktinfotype(infotype);


--- --  Dette bør lægges på ifm indlæsning fra REFGEO
create unique index geomobj_datopid on geometriobjekt(punktid, registreringfra);

-- Constraint der tjekker at registreringtil er større end registreringfra
ALTER TABLE BEREGNING ADD
CONSTRAINT BEREGNING_CON_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE VALIDATE;

ALTER TABLE GEOMETRIOBJEKT ADD
CONSTRAINT GEOMETRIOBJEKT_CON_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE VALIDATE;

ALTER TABLE KOORDINAT ADD
CONSTRAINT KOORDINAT_CON_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE VALIDATE;

ALTER TABLE OBSERVATION ADD
CONSTRAINT OBSERVATION_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE VALIDATE;


ALTER TABLE PUNKT ADD
CONSTRAINT PUNKT_CON_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE VALIDATE;


ALTER TABLE PUNKTINFO ADD
CONSTRAINT PUNKTINFO_CON_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE VALIDATE;

ALTER TABLE SAG ADD (
CONSTRAINT SAG_U01
UNIQUE (ID)
ENABLE VALIDATE);

ALTER TABLE SAGSINFO ADD (
CONSTRAINT SAGSINFO_R01
FOREIGN KEY (SAGSID)
REFERENCES SAG (ID)
ENABLE VALIDATE);


ALTER TABLE SAGSINFO ADD
CONSTRAINT SAGSINFO_CON_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE VALIDATE;

-- Constraint der sikrer at et sagsevent henviser til en eksisterende sag
ALTER TABLE SAGSEVENT ADD
CONSTRAINT SAGSEVENT_R01
FOREIGN KEY (SAGSID)
REFERENCES SAG (ID)
ENABLE VALIDATE;

ALTER TABLE SAGSEVENT ADD
CONSTRAINT SAGSEVENT_R02
FOREIGN KEY (EVENTTYPEID)
REFERENCES EVENTTYPE (EVENTTYPEID)
ENABLE VALIDATE;

ALTER TABLE SAGSEVENT ADD (
CONSTRAINT SAGSEVENT_U01
UNIQUE (ID)
ENABLE VALIDATE);

ALTER TABLE SAGSEVENTINFO ADD
CONSTRAINT SAGSEVENTINFO_CON_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE VALIDATE;

ALTER TABLE SAGSEVENTINFO ADD (
CONSTRAINT SAGSEVENTINFO_R01
FOREIGN KEY (SAGSEVENTID)
REFERENCES SAGSEVENT (ID)
ENABLE VALIDATE);


-- Triggere der sikrer at kun registreringtil kan opdateres i en tabel
CREATE OR REPLACE TRIGGER AUD#BEREGNING
after update ON BEREGNING
for each row
begin
IF :new.OBJEKTID != :old.OBJEKTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.SAGSEVENTFRAID != :old.SAGSEVENTFRAID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

end;
/


CREATE OR REPLACE TRIGGER AUD#GEOMETRIOBJEKT
after update ON GEOMETRIOBJEKT
for each row
begin

IF :new.OBJEKTID != :old.OBJEKTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.SAGSEVENTFRAID != :old.SAGSEVENTFRAID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.PUNKTID != :old.PUNKTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

end;
/

CREATE OR REPLACE TRIGGER AUD#KOORDINAT
after update ON KOORDINAT
for each row
begin
IF :new.OBJEKTID != :old.OBJEKTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.SRIDID != :old.SRIDID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.SX != :old.SX THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.SY != :old.SY THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;


IF :new.SZ != :old.SZ THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.T != :old.T THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.TRANSFORMERET != :old.TRANSFORMERET THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.X != :old.X THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;


IF :new.Y != :old.Y THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.Z != :old.Z THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.SAGSEVENTFRAID != :old.SAGSEVENTFRAID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.PUNKTID != :old.PUNKTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

end;
/


CREATE OR REPLACE TRIGGER AUD#OBSERVATION
after update ON OBSERVATION
for each row
begin
IF :new.OBJEKTID != :old.OBJEKTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.ANTAL != :old.ANTAL THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.GRUPPE != :old.GRUPPE THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;


IF :new.OBSERVATIONSTYPEID != :old.OBSERVATIONSTYPEID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE1 != :old.VALUE1 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE2 != :old.VALUE2 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE3 != :old.VALUE3 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;


IF :new.VALUE4 != :old.VALUE4 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE5 != :old.VALUE5 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE6 != :old.VALUE6 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE7 != :old.VALUE7 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE8 != :old.VALUE8 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE9 != :old.VALUE9 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE10 != :old.VALUE10 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE11 != :old.VALUE11 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE12 != :old.VALUE12 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE13 != :old.VALUE13 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE14 != :old.VALUE14 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.VALUE15 != :old.VALUE15 THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.SAGSEVENTFRAID != :old.SAGSEVENTFRAID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.OPSTILLINGSPUNKTID != :old.OPSTILLINGSPUNKTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.SIGTEPUNKTID != :old.SIGTEPUNKTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

end;
/

-- Trigger der sikrer at indeholdet i tabellen KOORDINAT matcher hvad der er specificeret omkring SRID i SRIDTYPE tabellen
CREATE OR REPLACE TRIGGER AIU#KOORDINAT
after insert Or UPDATE ON KOORDINAT
for each row
declare
   valX varchar2(4000):= '';
   valY varchar2(4000):= '';
   valZ varchar2(4000):= '';
begin

  select x,
         y,
         z into
         valX,
         valY,
         valZ
  from sridtype a
  where A.SRIDID = :new.SRIDID;


  if (:new.X is null OR :new.SX is NULL) and valX is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Hverken X eller SX må ikke være NULL');
  end if;

  if (:new.Y is null OR :new.SY is NULL) and valY is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Hverken Y eller SY må ikke være NULL');
  end if;

  if (:new.Z is null OR :new.SZ is NULL) and valZ is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Hverken Z eller SZ må ikke være NULL');
  end if;

end;
/


CREATE OR REPLACE TRIGGER AUD#PUNKT
after update ON PUNKT
for each row
begin
IF :new.OBJEKTID != :old.OBJEKTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.ID != :old.ID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.SAGSEVENTFRAID != :old.SAGSEVENTFRAID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

end;
/


CREATE OR REPLACE TRIGGER AUD#SAG
before update ON SAG
for each row
begin
IF :new.OBJEKTID != :old.OBJEKTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;


IF :new.ID != :old.ID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

end;
/


CREATE OR REPLACE TRIGGER AUD#SAGSEVENT
after update ON SAGSEVENT
for each row
begin
IF :new.OBJEKTID != :old.OBJEKTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column(a) '); END IF;

IF :new.ID != :old.ID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column(b) '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column(c) '); END IF;

IF :new.SAGSID != :old.SAGSID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column(d) '); END IF;

end;
/



CREATE OR REPLACE TRIGGER AUD#SAGSEVENTINFO
before update ON SAGSEVENTINFO
for each row
begin
IF :new.OBJEKTID != :old.OBJEKTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.SAGSEVENTID != :old.SAGSEVENTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.BESKRIVELSE != :old.BESKRIVELSE THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

end;
/


CREATE OR REPLACE TRIGGER AUD#SAGSINFO
before update ON SAGSINFO
for each row
begin
IF :new.OBJEKTID != :old.OBJEKTID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.SAGSID != :old.SAGSID THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.AKTIV != :old.AKTIV THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.JOURNALNUMMER != :old.JOURNALNUMMER THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.BEHANDLER != :old.BEHANDLER THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

IF :new.BESKRIVELSE != :old.BESKRIVELSE THEN RAISE_APPLICATION_ERROR(-20000,'You cannot update this column '); END IF;

end;
/


-- Trigger der sikrer at sageevents kun knyttes til en aktiv sag
CREATE OR REPLACE TRIGGER AID#SAGSEVENT
after insert ON SAGSEVENT
for each row
declare
cnt number := 0;
begin

  begin
    select 1 into cnt
    from sagsinfo
    where aktiv = 'true'
    and registreringtil is null
    and sagsid = :new.sagsid;
  exception when no_data_found then cnt:=0;
  end;

  if cnt = 0 then
    RAISE_APPLICATION_ERROR(-20000,'Ingen aktiv sag fundet paa sagsid '||:new.sagsid);
  END IF;

end;
/


-- Trigger der skal sikre at inholdet i Observation-tabellen matcher hvad der er defineret observationstype-tabellen
CREATE OR REPLACE TRIGGER AID#OBSERVATION
after insert Or UPDATE ON OBSERVATION
for each row
declare
   val1 varchar2(4000):= '';
   val2 varchar2(4000):= '';
   val3 varchar2(4000):= '';
   val4 varchar2(4000):= '';
   val5 varchar2(4000):= '';
   val6 varchar2(4000):= '';
   val7 varchar2(4000):= '';
   val8 varchar2(4000):= '';
   val9 varchar2(4000):= '';
   val10 varchar2(4000):= '';
   val11 varchar2(4000):= '';
   val12 varchar2(4000):= '';
   val13 varchar2(4000):= '';
   val14 varchar2(4000):= '';
   val15 varchar2(4000):= '';
begin

  select value1,
         value2,
         value3,
         value4,
         value5,
         value6,
         value7,
         value8,
         value9,
         value10,
         value11,
         value12,
         value13,
         value14,
         value15 into
         val1,
         val2,
         val3,
         val4,
         val5,
         val6,
         val7,
         val8,
         val9,
         val10,
         val11,
         val12,
         val13,
         val14,
         val15
  from observationstype a
  where A.OBSERVATIONSTYPEID = :new.OBSERVATIONSTYPEID;


  if :new.value1 is null and val1 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value1 må ikke være NULL');
  end if;
  if :new.value2 is null and val2 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value2 må ikke være NULL');
  end if;
  if :new.value3 is null and val3 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value3 må ikke være NULL');
  end if;
  if :new.value4 is null and val4 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value4 må ikke være NULL');
  end if;
  if :new.value5 is null and val5 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value5 må ikke være NULL');
  end if;
  if :new.value6 is null and val6 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value6 må ikke være NULL');
  end if;
  if :new.value7 is null and val7 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value7 må ikke være NULL');
  end if;
  if :new.value8 is null and val8 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value8 må ikke være NULL');
  end if;
  if :new.value9 is null and val9 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value9 må ikke være NULL');
  end if;
  if :new.value10 is null and val10 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value10 må ikke være NULL');
  end if;
  if :new.value11 is null and val11 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value11 må ikke være NULL');
  end if;
  if :new.value12 is null and val12 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value12 må ikke være NULL');
  end if;
  if :new.value13 is null and val13 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value13 må ikke være NULL');
  end if;
  if :new.value14 is null and val14 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value14 må ikke være NULL');
  end if;
  if :new.value15 is null and val15 is not null THEN
    RAISE_APPLICATION_ERROR(-20000,'Value15 må ikke være NULL');
  end if;

end;
/


-- Constraints der sikrer at namespacedelen er korrekt i PUNKTINFOTYPE og SRIDTYPE
ALTER TABLE PUNKTINFOTYPE ADD
CONSTRAINT PUNKTINFOTYPE_CON_0001
CHECK (substr(infotype,1,instr(infotype,':')-1) in ('AFM','ATTR','IDENT','NET','REGION','SKITSE'))
ENABLE
VALIDATE;

ALTER TABLE SRIDTYPE ADD
CONSTRAINT OT_SRID_0001
CHECK (substr(SRID,1,instr(SRID,':')-1) in ('DK','EPSG','GL','TS'))
ENABLE VALIDATE;

-- Sikrer at infotype i PUNKTINFO eksisterer i PUNKTINFOTYPE, og at data i PUNKTINFO matcher definition i PUNKTINFOTYPE
-- og at tidligere version af punktinfo afregistreres korrekt ved indsættelse af ny
CREATE OR REPLACE TRIGGER PUNKTINFO_TYPE_VALID_TRG
BEFORE INSERT OR UPDATE
ON PUNKTINFO
FOR EACH ROW
DECLARE
  this_andv varchar2(10);
  cnt NUMBER;
begin
  begin
    select anvendelse into this_andv
    from punktinfotype
    where infotypeid = :new.infotypeid;

   exception  when no_data_found then
      RAISE_APPLICATION_ERROR(-20000,'No infotype found(!)');
  end;

 if this_andv = 'FLAG' and (:new.TEKST is not null or :new.TAL is not null) THEN
   RAISE_APPLICATION_ERROR(-20000,'Incorrect data (A)(!)');
end if;

if this_andv = 'TEKST' and:new.TAL is not null THEN
   RAISE_APPLICATION_ERROR(-20000,'Incorrect data (B)(!)');
end if;

if this_andv = 'TAL' and:new.TEKST is not null THEN
   RAISE_APPLICATION_ERROR(-20000,'Incorrect data (C)(!)');
end if;

-- afregistrer forrige version af punktinfo når nyt indsættes
IF :new.registreringtil IS NULL THEN
  SELECT count(*) INTO cnt
  FROM punktinfo
  WHERE punktid = :new.PUNKTID AND infotypeid = :new.infotypeid AND registreringtil IS NULL;

  IF cnt = 1 THEN
    UPDATE punktinfo
    SET registreringtil = :new.registreringfra, sagseventtilid = :new.sagseventfraid
    WHERE objektid = (SELECT objektid FROM punktinfo WHERE punktid = :new.punktid AND infotypeid = :new.infotypeid AND registreringtil IS NULL);
  END IF;
END IF;

END;
/


CREATE OR REPLACE TRIGGER BID#PUNKT
before insert ON PUNKT
for each row
declare
cnt1 number;
begin
IF :new.REGISTRERINGFRA = :new.REGISTRERINGTIL THEN

  select count(*) into cnt1
  from PUNKT
  where REGISTRERINGTIL = :new.REGISTRERINGFRA;

  if cnt1 = 0 THEN
    RAISE_APPLICATION_ERROR(-20000,'No parent record found (!) ');
  END IF;

END IF;

end;
/

CREATE OR REPLACE TRIGGER BID#KOORDINAT
before insert ON KOORDINAT
for each row
declare
cnt number;
begin
IF :new.REGISTRERINGFRA = :new.REGISTRERINGTIL THEN
  select count(*) into cnt
  from KOORDINAT
  where REGISTRERINGTIL = :new.REGISTRERINGFRA;

  if cnt = 0 THEN
    RAISE_APPLICATION_ERROR(-20000,'No parent record found (!) ');
  END IF;
END IF;

IF :new.REGISTRERINGTIL IS NULL THEN
  select count(*) into cnt
  from KOORDINAT
  where punktid = :new.PUNKTID AND sridid = :new.sridid AND registreringtil IS NULL;

  if cnt = 1 THEN
    UPDATE koordinat
    SET registreringtil = :new.registreringfra, sagseventtilid = :new.sagseventfraid
    WHERE objektid = (SELECT objektid FROM koordinat WHERE punktid = :new.punktid AND sridid = :new.sridid AND registreringtil IS NULL);
  END IF;
END IF;

end;
/

CREATE OR REPLACE TRIGGER BID#SAGSINFO
BEFORE INSERT ON sagsinfo
FOR EACH ROW
DECLARE
cnt number;
BEGIN
IF :new.REGISTRERINGTIL IS NULL THEN
  SELECT count(*) INTO cnt
  FROM SAGSINFO
  WHERE sagsid = :new.sagsid AND registreringtil IS NULL;

  IF cnt = 1 THEN
    UPDATE sagsinfo
    SET registreringtil = :new.registreringfra
    WHERE objektid = (
        SELECT objektid
        FROM sagsinfo
        WHERE sagsid = :new.sagsid AND registreringtil IS NULL
    );
  END IF;
END IF;

END;
/

CREATE OR REPLACE TRIGGER BID#SAGSEVENTINFO
BEFORE INSERT ON sagseventinfo
FOR EACH ROW
DECLARE
cnt number;
BEGIN
IF :new.REGISTRERINGTIL IS NULL THEN
  SELECT count(*) INTO cnt
  FROM sagseventinfo
  WHERE sagseventid = :new.sagseventid AND registreringtil IS NULL;

  IF cnt = 1 THEN
    UPDATE sagseventinfo
    SET registreringtil = :new.registreringfra
    WHERE objektid = (
        SELECT objektid
        FROM sagseventinfo
        WHERE sagseventid = :new.sagseventid AND registreringtil IS NULL
    );
  END IF;
END IF;

END;
/

-------------------------------------------------------------------------------
-- Indhold til observationtype
-------------------------------------------------------------------------------

--
-- Geometrisk nivellement
--

INSERT INTO observationstype (
    -- Overordnet beskrivelse
    beskrivelse,
    OBSERVATIONSTYPEID,
    observationstype,
    sigtepunkt,

    -- Observationen
    value1,
    value2,
    value3,

    -- Nøjagtighedsestimat og korrektion
    value4,
    value5,
    value6,

    -- Historisk administrative grupperinger
    value7
)
VALUES (
    -- Overordnet beskrivelse
    'Koteforskel fra fikspunkt1 til fikspunkt2 (h2-h1) opmålt geometrisk',
     1,
    'geometrisk_koteforskel',
    'true',

    -- Observationen 1-3
    'Koteforskel [m]',
    'Nivellementslængde [m]',
    'Antal opstillinger',

    -- Nøjagtighedsestimat og korrektion 4-6
    'Variabel vedr. eta_1 (refraktion) [m^3]',
    'Empirisk spredning pr. afstandsenhed [mm/sqrt(km)]',
    'Empirisk centreringsfejl pr. opstilling [mm]',

    -- Historisk administrative grupperinger 7
    'Præcisionsnivellement [0,1,2,3]'

    -- Ikke anvendt value8-value15
);

--
-- Trigonometrisk nivellement
--

INSERT INTO observationstype (
    -- Overordnet beskrivelse
    beskrivelse,
    OBSERVATIONSTYPEID,
    observationstype,
    sigtepunkt,

    -- Observationen
    value1,
    value2,
    value3,

    -- Nøjagtighedsestimat
    value4,
    value5
)
VALUES (
    -- Overordnet beskrivelse
    'Koteforskel fra fikspunkt1 til fikspunkt2 (h2-h1) opmålt trigonometrisk',
     2 ,
    'trigonometrisk_koteforskel',
    'true',

    -- Observationen 1-3
    'Koteforskel [m]',
    'Nivellementslængde [m]',
    'Antal opstillinger',

    -- Nøjagtighedsestimat 4-5
    'Empirisk spredning pr. afstandsenhed [mm/sqrt(km)]',
    'Empirisk centreringsfejl pr. opstilling [mm]'

    -- Ikke anvendt value6-value15
);

INSERT INTO observationstype (beskrivelse, OBSERVATIONSTYPEID, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Horisontal retning med uret fra opstilling til sigtepunkt (reduceret til ellipsoiden)', 3 , 'retning', 'true','Retning [m]', 'Varians  retning hidrørende instrument, pr. sats  [rad^2]', 'Samlet centreringsvarians for instrument prisme [m^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationstype (beskrivelse, OBSERVATIONSTYPEID, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Horisontal afstand mellem opstilling og sigtepunkt (reduceret til ellipsoiden)', 4 , 'horisontalafstand', 'true','Afstand [m]', 'Afstandsafhængig varians afstandsmåler [m^2/m^2]', 'Samlet varians for centrering af instrument og prisme, samt grundfejl på afstandsmåler [m^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationstype (beskrivelse, OBSERVATIONSTYPEID, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Skråafstand mellem opstilling og sigtepunkt', 5 , 'skråafstand', 'true','Afstand [m]', 'Afstandsafhængig varians afstandsmåler pr. måling [m^2/m^2]', 'Samlet varians for centrering af instrument og prisme, samt grundfejl på afstandsmåler pr. måling [m^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationstype (beskrivelse, OBSERVATIONSTYPEID, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Zenitvinkel mellem opstilling og sigtepunkt', 6 , 'zenitvinkel', 'true','Zenitvinkel [rad]', 'Instrumenthøjde [m]', 'Højde sigtepunkt [m]', 'Varians zenitvinkel hidrørende instrument, pr. sats  [rad^2]', 'Samlet varians instrumenthøjde/højde sigtepunkt [m^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationstype (beskrivelse, OBSERVATIONSTYPEID, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Vektor der beskriver koordinatforskellen fra punkt 1 til punkt 2 (v2-v1)', 7 , 'vektor', 'true','dx [m]', 'dy [m]', 'dz [m]', 'Afstandsafhængig varians [m^2/m^2]', 'Samlet varians for centrering af antenner [m^2]', 'Varians dx [m^2]', 'Varians dy [m^2]', 'Varians dz [m^2]', 'Covarians dx, dy [m^2]', 'Covarians dx, dz [m^2]', 'Covarians dy, dz [m^2]', NULL, NULL, NULL, NULL);

INSERT INTO observationstype (beskrivelse, OBSERVATIONSTYPEID, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('observation nummer nul, indlagt fra start i observationstabellen, så der kan refereres til den i de mange beregningsevents der fører til population af koordinattabellen', 8 , 'nulobservation', 'false', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);



-- Oprettelse af eventtyper i FIRE
INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT, EVENTTYPEID)
VALUES ('Bruges når koordinater indsættes efter en beregning.', 'koordinat_beregnet', 1);

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT, EVENTTYPEID)
VALUES ('Bruges når en koordinat nedlægges.', 'koordinat_nedlagt', 2);

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT, EVENTTYPEID)
VALUES ('Indsættelse af en eller flere observationer.', 'observation_indsat', 3);

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT, EVENTTYPEID)
VALUES ('Bruges når en observation aflyses fordi den er fejlbehæftet.', 'observation_nedlagt', 4);

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT, EVENTTYPEID)
VALUES ('Bruges når der tilføjes Punktinfo til et eller flere punkter.', 'punktinfo_tilføjet', 5);

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT, EVENTTYPEID)
VALUES ('Bruges når Punktinfo fjernes fra et eller flere punkter.', 'punktinfo_fjernet', 6);

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT, EVENTTYPEID)
VALUES ('Bruges når et punkt og tilhørende geometri oprettes.', 'punkt_oprettet', 7);

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT, EVENTTYPEID)
VALUES ('Bruges når et punkt og tilhørende geometri nedlægges.', 'punkt_nedlagt', 8);

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT, EVENTTYPEID)
VALUES ('Bruges til at tilføje fritekst-kommentarer til sagen i tilfælde af at der er behov for at påhæfte sagen yderligere information, som ikke passer i andre hændelser. Bruges fx også til påhæftning af materiale på sagen.', 'kommentar', 9);

-- End

