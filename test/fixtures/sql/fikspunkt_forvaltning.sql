CREATE TABLE BEREGNING (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   SAGSEVENTID VARCHAR2(36) NOT NULL
);

CREATE TABLE BEREGNING_KOORDINAT (

   BEREGNINGOBJECTID INTEGER NOT NULL,
   KOORDINATOBJECTID INTEGER NOT NULL,
   PRIMARY KEY (BEREGNINGOBJECTID, KOORDINATOBJECTID)
);

CREATE TABLE BEREGNING_OBSERVATION (

   BEREGNINGOBJECTID INTEGER NOT NULL,
   OBSERVATIONOBJECTID INTEGER NOT NULL,
   PRIMARY KEY (BEREGNINGOBJECTID, OBSERVATIONOBJECTID)
);

CREATE TABLE EVENTTYPE (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   BESKRIVELSE VARCHAR2(4000) NOT NULL,
   EVENT VARCHAR2(4000) NOT NULL
);

CREATE TABLE GEOMETRIOBJEKT (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   SAGSEVENTID VARCHAR2(36) NOT NULL,
   GEOMETRI SDO_GEOMETRY NOT NULL,
   PUNKTID VARCHAR2(36) NOT NULL
);

CREATE TABLE KOORDINAT (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   SAGSEVENTID VARCHAR2(36) NOT NULL,
   SRID VARCHAR2(36) NOT NULL,
   SX NUMBER,
   SY NUMBER,
   SZ NUMBER,
   T TIMESTAMP WITH TIME ZONE,
   TRANSFORMERET VARCHAR2(5) NOT NULL,
   X NUMBER,
   Y NUMBER,
   Z NUMBER,
   PUNKTID VARCHAR2(36) NOT NULL
);

CREATE TABLE OBSERVATION (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
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
   SAGSEVENTID VARCHAR2(36) NOT NULL,
   ANTAL INTEGER NOT NULL,
   OBSERVATIONSTYPE VARCHAR2(4000) NOT NULL,
   GRUPPE INTEGER,
   OBSERVATIONSTIDSPUNKT TIMESTAMP WITH TIME ZONE NOT NULL,
   OPSTILLINGSPUNKTID VARCHAR2(36) NOT NULL,
   SIGTEPUNKTID VARCHAR2(36)
);

CREATE TABLE OBSERVATIONTYPE (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   BESKRIVELSE VARCHAR2(4000) NOT NULL,
   OBSERVATIONSTYPE VARCHAR2(4000) NOT NULL,
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

CREATE TABLE OBSERVATIONTYPENAMESPACE (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   BESKRIVELSE VARCHAR2(4000) NOT NULL,
   NAMESPACE VARCHAR2(4000) NOT NULL
);

CREATE TABLE PUNKT (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   SAGSEVENTID VARCHAR2(36) NOT NULL,
   ID VARCHAR2(36) NOT NULL
);

CREATE TABLE PUNKTINFO (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   SAGSEVENTID VARCHAR2(36) NOT NULL,
   INFOTYPE VARCHAR2(4000) NOT NULL,
   TAL NUMBER,
   TEKST VARCHAR2(4000),
   PUNKTID VARCHAR2(36) NOT NULL
);

CREATE TABLE PUNKTINFOTYPE (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   INFOTYPE VARCHAR2(4000) NOT NULL,
   ANVENDELSE VARCHAR2(9) NOT NULL,
   BESKRIVELSE VARCHAR2(4000) NOT NULL
);

CREATE TABLE PUNKTINFOTYPENAMESPACE (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   BESKRIVELSE VARCHAR2(4000) NOT NULL,
   NAMESPACE VARCHAR2(4000) NOT NULL
);

CREATE TABLE SAG (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   ID VARCHAR2(36) NOT NULL,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE SAGSEVENT (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   ID VARCHAR2(36) NOT NULL,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   EVENT VARCHAR2(4000) NOT NULL,
   SAGID VARCHAR2(36) NOT NULL
);

CREATE TABLE SAGSEVENTINFO (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   BESKRIVELSE VARCHAR2(4000),
   SAGSEVENTID VARCHAR2(36) NOT NULL
);

CREATE TABLE SAGSEVENTINFO_MATERIALE (

   SAGSEVENTINFOOBJECTID INTEGER NOT NULL,
   MATERIALE VARCHAR2(4000) NOT NULL,
   PRIMARY KEY (SAGSEVENTINFOOBJECTID, MATERIALE)
);

CREATE TABLE SAGSEVENTINFO_RAPPORTHTML (

   SAGSEVENTINFOOBJECTID INTEGER NOT NULL,
   RAPPORTHTML VARCHAR2(4000) NOT NULL,
   PRIMARY KEY (SAGSEVENTINFOOBJECTID, RAPPORTHTML)
);

CREATE TABLE SAGSINFO (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   AKTIV VARCHAR2(5) NOT NULL,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   JOURNALNUMMER VARCHAR2(4000),
   BEHANDLER VARCHAR2(4000) NOT NULL,
   BESKRIVELSE VARCHAR2(4000),
   SAGID VARCHAR2(36) NOT NULL
);

CREATE TABLE SRIDNAMESPACE (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   NAMESPACE VARCHAR2(4000) NOT NULL,
   BESKRIVELSE VARCHAR2(4000) NOT NULL
);

CREATE TABLE SRIDTYPE (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   SRID VARCHAR2(36) NOT NULL,
   BESKRIVELSE VARCHAR2(4000) NOT NULL
);


ALTER TABLE KOORDINAT ADD CONSTRAINT CK_KOORDINAT_TRANSFORMER248 CHECK (TRANSFORMERET IN ('true', 'false'));
ALTER TABLE OBSERVATIONTYPE ADD CONSTRAINT CK_OBSERVATION_SIGTEPUNKT085 CHECK (SIGTEPUNKT IN ('true', 'false'));
ALTER TABLE PUNKTINFOTYPE ADD CONSTRAINT CK_PUNKTINFOTY_ANVENDELSE138 CHECK (ANVENDELSE IN ('FLAG', 'TAL', 'TEKST'));
ALTER TABLE SAGSINFO ADD CONSTRAINT CK_SAGSINFO_AKTIV060 CHECK (AKTIV IN ('true', 'false'));

INSERT INTO USER_SDO_GEOM_METADATA (TABLE_NAME, COLUMN_NAME, DIMINFO, SRID) VALUES ('GEOMETRIOBJEKT', 'GEOMETRI', MDSYS.SDO_DIM_ARRAY(MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005), MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)), 4326);

CREATE INDEX IDX_GEOMETRIOBJEKT_GEOMETRI ON GEOMETRIOBJEKT (GEOMETRI) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');

COMMENT ON TABLE BEREGNING IS 'Sammenknytter beregnede koordinater med de anvendte observationer.';
COMMENT ON COLUMN BEREGNING.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN BEREGNING.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN BEREGNING.SAGSEVENTID IS 'Angivelse af den hændelse der har ændret et fikspunktsobjekt.';
COMMENT ON COLUMN BEREGNING_KOORDINAT.KOORDINATOBJECTID IS 'Udpegning af de koordinater der er indgået i en beregning.';
COMMENT ON COLUMN BEREGNING_OBSERVATION.OBSERVATIONOBJECTID IS 'Udpegning af de observationer der er brugt i en beregning.';
COMMENT ON TABLE EVENTTYPE IS 'Objekt til at holde liste over lovlige typer af events i fikspunktsforvaltningssystemet, samt en beskrivelse hvad eventtypen dækker over.';
COMMENT ON COLUMN EVENTTYPE.BESKRIVELSE IS 'Kort beskrivelse af en eventype.';
COMMENT ON COLUMN EVENTTYPE.EVENT IS 'Navngivning af en eventtype.';
COMMENT ON TABLE GEOMETRIOBJEKT IS 'Objekt indeholdende et punkts placeringsgeometri til brug for anvendes til visualisering.';
COMMENT ON COLUMN GEOMETRIOBJEKT.GEOMETRI IS 'Placeringsgeometri til brug for visning i f.eks et GIS sysstem.';
COMMENT ON COLUMN GEOMETRIOBJEKT.PUNKTID IS 'Punkt som har en placeringsgeometri tilknyttet.';
COMMENT ON COLUMN GEOMETRIOBJEKT.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN GEOMETRIOBJEKT.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN GEOMETRIOBJEKT.SAGSEVENTID IS 'Angivelse af den hændelse der har ændret et fikspunktsobjekt.';
COMMENT ON TABLE KOORDINAT IS 'Generisk 4D koordinat.';
COMMENT ON COLUMN KOORDINAT.PUNKTID IS 'Punkt som kordinaten hører til.';
COMMENT ON COLUMN KOORDINAT.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN KOORDINAT.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN KOORDINAT.SAGSEVENTID IS 'Angivelse af den hændelse der har ændret et fikspunktsobjekt.';
COMMENT ON COLUMN KOORDINAT.SRID IS 'Unik værdi til angivelse af et koordinatsystem.';
COMMENT ON COLUMN KOORDINAT.SX IS 'A posteriori spredning på førstekoordinaten.';
COMMENT ON COLUMN KOORDINAT.SY IS 'A posteriori spredning på andenkoordinaten.';
COMMENT ON COLUMN KOORDINAT.SZ IS 'A posteriori spredning på tredjekoordinaten.';
COMMENT ON COLUMN KOORDINAT.T IS 'Observationstidspunktet.';
COMMENT ON COLUMN KOORDINAT.TRANSFORMERET IS 'Angivelse om positionen er målt, eller transformeret fra et andet koordinatsystem';
COMMENT ON COLUMN KOORDINAT.X IS 'Førstekoordinat.';
COMMENT ON COLUMN KOORDINAT.Y IS 'Andenkoordinat.';
COMMENT ON COLUMN KOORDINAT.Z IS 'Tredjekoordinat.';
COMMENT ON TABLE OBSERVATION IS 'Generisk observationsobjekt indeholdende informationer om en observation.';
COMMENT ON COLUMN OBSERVATION.OBSERVATIONSTIDSPUNKT IS 'Tidspunktet hvor observationen er foretaget';
COMMENT ON COLUMN OBSERVATION.OBSERVATIONSTYPE IS 'Kortnavn for observationstypen, fx dH';
COMMENT ON COLUMN OBSERVATION.OPSTILLINGSPUNKTID IS 'Udpegning af det punkt der er anvendt ved opstilling ved en observation.';
COMMENT ON COLUMN OBSERVATION.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN OBSERVATION.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN OBSERVATION.SAGSEVENTID IS 'Angivelse af den hændelse der har ændret et fikspunktsobjekt.';
COMMENT ON COLUMN OBSERVATION.SIGTEPUNKTID IS 'Udpegning af punktder er sigtet til ved en observation.';
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
COMMENT ON TABLE OBSERVATIONTYPE IS 'Objekttype til beskrivelse af hvorledes en Observation skal læses, ud fra typen af observation.';
COMMENT ON COLUMN OBSERVATIONTYPE.BESKRIVELSE IS 'Overordnet beskrivelse af denne observationstype.';
COMMENT ON COLUMN OBSERVATIONTYPE.OBSERVATIONSTYPE IS 'Kortnavn for observationstypen, fx dH';
COMMENT ON COLUMN OBSERVATIONTYPE.SIGTEPUNKT IS 'Indikator for om Sigtepunkt 1 anvendes for denne observationstype.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE1 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE10 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE11 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE12 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE13 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE14 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE15 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE2 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE3 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE4 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE5 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE6 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE7 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE8 IS 'Beskrivelse af første observationselement.';
COMMENT ON COLUMN OBSERVATIONTYPE.VALUE9 IS 'Beskrivelse af første observationselement.';
COMMENT ON TABLE OBSERVATIONTYPENAMESPACE IS 'Type der afgrænser de lovlige namspaces der kan anvendes i observationstype, samt en beskrivese af denne.';
COMMENT ON COLUMN OBSERVATIONTYPENAMESPACE.BESKRIVELSE IS 'Kort beskrivelse af hvad der dækkes af et observationsnamespace.';
COMMENT ON COLUMN OBSERVATIONTYPENAMESPACE.NAMESPACE IS 'Navn på et lovlige namspace for en observation.';
COMMENT ON TABLE PUNKT IS 'Abstrakt repræsentation af et fysisk punkt. Knytter alle punktinformationer sammen.';
COMMENT ON COLUMN PUNKT.ID IS 'Persistent unik nøgle.';
COMMENT ON COLUMN PUNKT.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN PUNKT.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN PUNKT.SAGSEVENTID IS 'Angivelse af den hændelse der har ændret et fikspunktsobjekt.';
COMMENT ON TABLE PUNKTINFO IS 'Generisk information om et punkt.';
COMMENT ON COLUMN PUNKTINFO.INFOTYPE IS 'Arten af dette informationselement.';
COMMENT ON COLUMN PUNKTINFO.PUNKTID IS 'Punktet som punktinfo er holder information om.';
COMMENT ON COLUMN PUNKTINFO.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN PUNKTINFO.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN PUNKTINFO.SAGSEVENTID IS 'Angivelse af den hændelse der har ændret et fikspunktsobjekt.';
COMMENT ON COLUMN PUNKTINFO.TAL IS 'Værdien for numeriske informationselementer';
COMMENT ON COLUMN PUNKTINFO.TEKST IS 'Værdien for tekstinformationselementer';
COMMENT ON TABLE PUNKTINFOTYPE IS 'Udfaldsrum for punktinforobjekter med definition af hvodan PunktInfo skal læses og beskrivelse af typen af punktinfo.';
COMMENT ON COLUMN PUNKTINFOTYPE.ANVENDELSE IS 'Er det reelTal, tekst, eller ingen af disse, der angiver værdien';
COMMENT ON COLUMN PUNKTINFOTYPE.BESKRIVELSE IS 'Beskrivelse af denne informationstypes art.';
COMMENT ON COLUMN PUNKTINFOTYPE.INFOTYPE IS 'Arten af dette informationselement';
COMMENT ON TABLE PUNKTINFOTYPENAMESPACE IS 'Type der afgrænser de lovlige namspaces der kan anvendes i tinfotype, samt en beskrivese af denne.';
COMMENT ON COLUMN PUNKTINFOTYPENAMESPACE.BESKRIVELSE IS 'Kort beskrivelse af hvad der dækkes af et punktinfonamespace.';
COMMENT ON COLUMN PUNKTINFOTYPENAMESPACE.NAMESPACE IS 'Navn på et lovlige namspace for en punktinformation.';
COMMENT ON TABLE SAG IS 'Samling af administrativt relaterede sagshændelser.';
COMMENT ON COLUMN SAG.ID IS 'Persistent unik nøgle.';
COMMENT ON COLUMN SAG.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON TABLE SAGSEVENT IS 'Udvikling i sag som kan, men ikke behøver, medføre opdateringer af fikspunktregisterobjekter.';
COMMENT ON COLUMN SAGSEVENT.EVENT IS 'Generisk beskrivelse af fremdriftens art.';
COMMENT ON COLUMN SAGSEVENT.ID IS 'Persistent unik nøgle.';
COMMENT ON COLUMN SAGSEVENT.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN SAGSEVENT.SAGID IS 'Udpegning af den sag i fikspunktsforvalningssystemet som en event er foretaget i.';
COMMENT ON TABLE SAGSEVENTINFO IS 'Udvikling i sag som kan, men ikke behøver, medføre opdateringer af fikspunktregisterobjekter.';
COMMENT ON COLUMN SAGSEVENTINFO.BESKRIVELSE IS 'Specifik beskrivelse af den aktuelle fremdrift.';
COMMENT ON COLUMN SAGSEVENTINFO.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN SAGSEVENTINFO.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN SAGSEVENTINFO_MATERIALE.MATERIALE IS 'Generisk materiale tilknyttet sagsevent - typisk en filmappe URI.';
COMMENT ON COLUMN SAGSEVENTINFO_RAPPORTHTML.RAPPORTHTML IS 'Generisk operatørlæsbart orienterende rapportmateriale.';
COMMENT ON TABLE SAGSINFO IS 'Samling af administrativt relaterede sagshændelser.';
COMMENT ON COLUMN SAGSINFO.AKTIV IS 'Markerer om sagen er åben eller lukket.';
COMMENT ON COLUMN SAGSINFO.BEHANDLER IS 'Angivelse af en sagsbehandler.';
COMMENT ON COLUMN SAGSINFO.BESKRIVELSE IS 'Kort beskrivelse af en fikspunktssag.';
COMMENT ON COLUMN SAGSINFO.JOURNALNUMMER IS 'Sagsmappeidentifikation i opmålings- og beregningssagsregistret.';
COMMENT ON COLUMN SAGSINFO.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN SAGSINFO.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON TABLE SRIDNAMESPACE IS 'Type der afgrænser de lovlige namspaces der kan anvendes i SRIDtype, samt en beskrivese af denne.';
COMMENT ON COLUMN SRIDNAMESPACE.BESKRIVELSE IS 'Kort beskrivelse af hvad der dækkes af et SRIDnamespace.';
COMMENT ON COLUMN SRIDNAMESPACE.NAMESPACE IS 'Navn på et lovlige namspace for en SRID.';
COMMENT ON TABLE SRIDTYPE IS 'Udfaldsrum for SRID-koordinatbeskrivelser.';
COMMENT ON COLUMN SRIDTYPE.BESKRIVELSE IS 'Generel beskrivelse af systemet.';
COMMENT ON COLUMN SRIDTYPE.SRID IS 'Den egentlige referencesystemindikator.';

-- Constraints og triggers ikke defineret i modellen
-- Constraint der tjekker at PUNKTID eksisterer i PUNKT tabellen inden en række sættes ind i KOORDINAT-, OBESARVATION- og PUNKTINFO-tabellen
CREATE UNIQUE INDEX ID_IDX_0001 ON PUNKT
(ID)
LOGGING
STORAGE    (
            BUFFER_POOL      DEFAULT
            FLASH_CACHE      DEFAULT
            CELL_FLASH_CACHE DEFAULT
           )
NOPARALLEL;

ALTER TABLE PUNKT ADD (
  CONSTRAINT PUNKT_R01
  UNIQUE (ID)
  USING INDEX ID_IDX_0001
  ENABLE VALIDATE);

ALTER TABLE KOORDINAT ADD 
CONSTRAINT punktid_con_0001
FOREIGN KEY (PUNKTID)
REFERENCES PUNKT (ID)
ENABLE
VALIDATE;

ALTER TABLE OBSERVATION ADD 
CONSTRAINT observation_sp_con_0001
FOREIGN KEY (SIGTEPUNKTID)
REFERENCES PUNKT (ID)
ENABLE
VALIDATE;

ALTER TABLE OBSERVATION ADD 
CONSTRAINT observation_op1_con_0001
FOREIGN KEY (OPSTILLINGSPUNKTID)
REFERENCES PUNKT (ID)
ENABLE
VALIDATE;

ALTER TABLE PUNKTINFO ADD 
CONSTRAINT punktinfo_con_001
FOREIGN KEY (PUNKTID)
REFERENCES PUNKT (ID)
ENABLE
VALIDATE;

-- Constraint der tjekker at registreringtil er større end registreringfra
ALTER TABLE BEREGNING ADD 
CONSTRAINT beregning_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE;   
   
ALTER TABLE GEOMETRIOBJEKT ADD 
CONSTRAINT geometriobjekt_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE;     
   
ALTER TABLE KOORDINAT ADD 
CONSTRAINT KOORDINAT_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE;  
   
ALTER TABLE OBSERVATION ADD 
CONSTRAINT OBSERVATION_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE;
 
 
ALTER TABLE PUNKT ADD 
CONSTRAINT PUNKT_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE;
 
 
ALTER TABLE PUNKTINFO ADD 
CONSTRAINT PUNKTINFO_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE;

ALTER TABLE SAG ADD ( 
  CONSTRAINT SAG_U01
  UNIQUE (ID)
  ENABLE VALIDATE);

ALTER TABLE SAGSINFO ADD (
  CONSTRAINT SAGSINFO_R01 
  FOREIGN KEY (SAGID) 
  REFERENCES SAG (ID)
  ENABLE VALIDATE);


ALTER TABLE SAGSINFO ADD 
CONSTRAINT SAGSINFO_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE; 
 

ALTER TABLE SAGSEVENT ADD (
  CONSTRAINT SAGSEVENT_R01 
  FOREIGN KEY (SAGID) 
  REFERENCES SAG (ID)
  ENABLE VALIDATE); 
  
  ALTER TABLE SAGSEVENT ADD ( 
  CONSTRAINT SAGSEVENT_U01
  UNIQUE (ID)
  ENABLE VALIDATE);

  
ALTER TABLE SAGSEVENTINFO ADD 
CONSTRAINT SAGSEVENTINFO_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE;  
 
ALTER TABLE SAGSEVENTINFO ADD (
  CONSTRAINT SAGSEVENTINFO_R01 
  FOREIGN KEY (SAGSEVENTID) 
  REFERENCES SAGSEVENT (ID)
  ENABLE VALIDATE);





-- Triggere der sikre at kun registreringtil kan opdateres i en tabel
CREATE OR REPLACE TRIGGER AUD#BEREGNING
after update ON BEREGNING
for each row
begin
IF :new.OBJECTID != :old.OBJECTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

--IF :new.REGISTRERINGTIL != :old.REGISTRERINGTIL THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;


IF :new.SAGSEVENTID != :old.SAGSEVENTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

end;
/


CREATE OR REPLACE TRIGGER AUD#GEOMETRIOBJEKT
after update ON GEOMETRIOBJEKT
for each row
begin
--IF :new.GEOMETRI != :old.GEOMETRI THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.OBJECTID != :old.OBJECTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;


-- IF :new.REGISTRERINGTIL != :old.REGISTRERINGTIL THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.SAGSEVENTID != :old.SAGSEVENTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.PUNKTID != :old.PUNKTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

end;
/

CREATE OR REPLACE TRIGGER AUD#KOORDINAT
after update ON KOORDINAT
for each row
begin
IF :new.OBJECTID != :old.OBJECTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

-- IF :new.REGISTRERINGTIL != :old.REGISTRERINGTIL THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.SRID != :old.SRID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.SX != :old.SX THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.SY != :old.SY THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;


IF :new.SZ != :old.SZ THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.T != :old.T THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.TRANSFORMERET != :old.TRANSFORMERET THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.X != :old.X THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;


IF :new.Y != :old.Y THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.Z != :old.Z THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.SAGSEVENTID != :old.SAGSEVENTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.PUNKTID != :old.PUNKTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

end;
/


CREATE OR REPLACE TRIGGER AUD#OBSERVATION
after update ON OBSERVATION
for each row
begin
IF :new.OBJECTID != :old.OBJECTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

--IF :new.REGISTRERINGTIL != :old.REGISTRERINGTIL THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.ANTAL != :old.ANTAL THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.GRUPPE != :old.GRUPPE THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;


IF :new.OBSERVATIONSTYPE != :old.OBSERVATIONSTYPE THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE1 != :old.VALUE1 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE2 != :old.VALUE2 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE3 != :old.VALUE3 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;


IF :new.VALUE4 != :old.VALUE4 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE5 != :old.VALUE5 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE6 != :old.VALUE6 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE7 != :old.VALUE7 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE8 != :old.VALUE8 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE9 != :old.VALUE9 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE10 != :old.VALUE10 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE11 != :old.VALUE11 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE12 != :old.VALUE12 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE13 != :old.VALUE13 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE14 != :old.VALUE14 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.VALUE15 != :old.VALUE15 THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.SAGSEVENTID != :old.SAGSEVENTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.OPSTILLINGSPUNKTID != :old.OPSTILLINGSPUNKTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.SIGTEPUNKTID != :old.SIGTEPUNKTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

end;
/


CREATE OR REPLACE TRIGGER AUD#PUNKT
after update ON PUNKT
for each row
begin
IF :new.OBJECTID != :old.OBJECTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

--IF :new.REGISTRERINGTIL != :old.REGISTRERINGTIL THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.ID != :old.ID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.SAGSEVENTID != :old.SAGSEVENTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

end;
/


CREATE OR REPLACE TRIGGER AUD#SAG
before update ON SAG
for each row
begin
IF :new.OBJECTID != :old.OBJECTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;


IF :new.ID != :old.ID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

--IF :new.REGISTRERINGTIL != :old.REGISTRERINGTIL THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

end;
/


CREATE OR REPLACE TRIGGER AUD#SAGSEVENT
before update ON SAGSEVENT
for each row
begin
IF :new.OBJECTID != :old.OBJECTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.ID != :old.ID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

--IF :new.REGISTRERINGTIL != :old.REGISTRERINGTIL THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.SAGID != :old.SAGID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

end;
/


CREATE OR REPLACE TRIGGER AUD#SAGSEVENTINFO
before update ON SAGSEVENTINFO
for each row
begin
IF :new.OBJECTID != :old.OBJECTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.SAGSEVENTID != :old.SAGSEVENTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

--IF :new.REGISTRERINGTIL != :old.REGISTRERINGTIL THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.BESKRIVELSE != :old.BESKRIVELSE THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

end;
/


CREATE OR REPLACE TRIGGER AUD#SAGSINFO
before update ON SAGSINFO
for each row
begin
IF :new.OBJECTID != :old.OBJECTID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.SAGID != :old.SAGID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.REGISTRERINGFRA != :old.REGISTRERINGFRA THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

--IF :new.REGISTRERINGTIL != :old.REGISTRERINGTIL THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.AKTIV != :old.AKTIV THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.JOURNALNUMMER != :old.JOURNALNUMMER THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.BEHANDLER != :old.BEHANDLER THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.BESKRIVELSE != :old.BESKRIVELSE THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

end;
/

-- Index der skal sikre at der til samme punkt ikke tilføjes en koordinat med samme SRID, hvis denne ikke er afregistreret
CREATE UNIQUE INDEX KOOR_UNIQ_001 ON KOORDINAT
(SRID, PUNKTID, REGISTRERINGTIL);


-- Trigger der skal sikre at inholdet i Observation-tabellen matcher hvad der er defineret observationtype-tabellen
CREATE OR REPLACE TRIGGER AID#OBSERVATION
after insert Or UPDATE ON FIRE_TEST.OBSERVATION
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
  from observationtype a
  where A.OBSERVATIONSTYPE = :new.observationstype;
         

  if :new.value1 is null and val1 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value1 må ikke være NULL'); 
  end if;
  if :new.value2 is null and val2 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value2 må ikke være NULL'); 
  end if;
  if :new.value3 is null and val3 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value3 må ikke være NULL'); 
  end if;
  if :new.value4 is null and val4 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value4 må ikke være NULL'); 
  end if;
  if :new.value5 is null and val5 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value5 må ikke være NULL'); 
  end if;
  if :new.value6 is null and val6 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value6 må ikke være NULL'); 
  end if;
  if :new.value7 is null and val7 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value7 må ikke være NULL'); 
  end if;
  if :new.value8 is null and val8 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value8 må ikke være NULL'); 
  end if;
  if :new.value9 is null and val9 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value9 må ikke være NULL'); 
  end if;
  if :new.value10 is null and val10 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value10 må ikke være NULL'); 
  end if;
  if :new.value11 is null and val11 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value11 må ikke være NULL'); 
  end if;
  if :new.value12 is null and val12 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value12 må ikke være NULL'); 
  end if;
  if :new.value13 is null and val13 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value13 må ikke være NULL'); 
  end if;
  if :new.value14 is null and val14 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value14 må ikke være NULL'); 
  end if;
  if :new.value15 is null and val15 is not null THEN
    RAISE_APPLICATION_ERROR(20000,'Value15 må ikke være NULL'); 
  end if;
  
end;
/




-- Constraints der sikre at namespacedelen er korrekt i PUNKTINFOTYPE, OBSERVATIONTYPE og SRIDTYPE
ALTER TABLE PUNKTINFOTYPE ADD 
CONSTRAINT pt_con_0001
CHECK (substr(infotype,1,instr(infotype,':')-1) in ('AFM','ATTR','IDENT','NET','PS','REGION','SKITSE'))
ENABLE
VALIDATE;

ALTER TABLE OBSERVATIONTYPE ADD 
CONSTRAINT ot_con_0001
CHECK (substr(observationstype,1,instr(observationstype,':')-1) in ('OBS'))
ENABLE
VALIDATE;

ALTER TABLE SRIDTYPE ADD 
CONSTRAINT ot_srid_0001
CHECK (substr(SRID,1,instr(SRID,':')-1) in ('DK','EPSG','FO','GL','LOC','NKG','TS'))
ENABLE
VALIDATE;

-- Sikre at infotype i PUNKTINFO eksisterer i PUNKTINFOTYPE, og at data i PUNKTINFO matcher definition i PUNKTINFOTYPE
CREATE OR REPLACE TRIGGER PUNKTINFO_TYPE_VALID_TRG
BEFORE INSERT OR UPDATE
ON PUNKTINFO
FOR EACH ROW
DECLARE
this_andv varchar2(10);
begin
  begin
    select anvendelse into this_andv 
    from punktinfotype 
    where infotype = :new.infotype;
  
   exception  when no_data_found then
      RAISE_APPLICATION_ERROR(20000,'No infotype found(!)');
  end;

 if this_andv = 'FLAG' and (:new.TEKST is not null or :new.TAL is not null) THEN
   RAISE_APPLICATION_ERROR(20000,'Incorrect data (A)(!)');
end if;

if this_andv = 'TEKST' and:new.TAL is not null THEN
   RAISE_APPLICATION_ERROR(20000,'Incorrect data (B)(!)');
end if;

if this_andv = 'TAL' and:new.TEKST is not null THEN
   RAISE_APPLICATION_ERROR(20000,'Incorrect data (C)(!)');
end if;

end;
/

CREATE UNIQUE INDEX PUNKTINFOTYPE_IDX_01 ON PUNKTINFOTYPE
(INFOTYPE);

ALTER TABLE PUNKTINFOTYPE ADD (
  CONSTRAINT PUNKTINFOTYPE_U01
  UNIQUE (INFOTYPE)
  USING INDEX PUNKTINFOTYPE_IDX_01
  ENABLE VALIDATE);

ALTER TABLE PUNKTINFO ADD 
CONSTRAINT PUNKTINFO_R01
FOREIGN KEY (INFOTYPE)
REFERENCES PUNKTINFOTYPE (INFOTYPE)
ENABLE
VALIDATE;
 
CREATE UNIQUE INDEX OBSERVATIONSTYPE_IDX_001 ON OBSERVATIONTYPE
(OBSERVATIONSTYPE);
 
ALTER TABLE OBSERVATIONTYPE ADD (
  CONSTRAINT OBSERVATIONTYPE_U01
  UNIQUE (OBSERVATIONSTYPE)
  USING INDEX OBSERVATIONSTYPE_IDX_001
  ENABLE VALIDATE);

  ALTER TABLE OBSERVATION ADD 
CONSTRAINT OBSERVATION_R01
FOREIGN KEY (OBSERVATIONSTYPE)
REFERENCES OBSERVATIONTYPE (OBSERVATIONSTYPE)
ENABLE
VALIDATE;



-- Indehold til observationtype
INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Koteforskel fra fikspunkt1 til fikspunkt2 (h2-h1) opmålt geometrisk ', 'geometrisk_koteforskel', 'true','Koteforskel [m]', 'Nivellementslængde [m]', 'Antal opstillinger', 'Variabel vedr. eta_1 (refraktion) [m^3]', 'Afstandsafhængig varians koteforskel pr. målt koteforskel [m^2/m]', 'Afstandsuafhængig varians koteforskel pr. målt koteforskel [m^2]', 'Total varians koteforskel [m^2]', 'Præcisionsnivellement [0,1,2,3]', NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Koteforskel fra fikspunkt1 til fikspunkt2 (h2-h1) opmålt trigonometrisk' , 'trigonometrisk_koteforskel', 'true','Koteforskel [m]', 'Nivellementslængde [m]', 'Antal opstillinger', 'Afstandsafhængig varians pr. målt koteforskel [m^2/m^2]', 'Afstandsuafhængig varians pr. målt koteforskel [m^2]', 'Total varians koteforskel [m^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Horisontal retning med uret fra opstilling til sigtepunkt (reduceret til ellipsoiden)' , 'retning', 'true','Retning [m]', 'Varians  retning hidrørende instrument, pr. sats  [rad^2]', 'Samlet centreringsvarians for instrument prisme [m^2]', 'Total varians retning [rad^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Horisontal afstand mellem opstilling og sigtepunkt (reduceret til ellipsoiden)' , 'horisontalafstand', 'true','Afstand [m]', 'Afstandsafhængig varians afstandsmåler [m^2/m^2]', 'Samlet varians for centrering af instrument og prisme, samt grundfejl på afstandsmåler [m^2]', 'Total varians horisontalafstand [m^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Skråafstand mellem opstilling og sigtepunkt' , 'skråafstand', 'true','Afstand [m]', 'Afstandsafhængig varians afstandsmåler pr. måling [m^2/m^2]', 'Samlet varians for centrering af instrument og prisme, samt grundfejl på afstandsmåler pr. måling [m^2]', 'Total varians skråafstand [m^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Zenitvinkel mellem opstilling og sigtepunkt' , 'zenitvinkel', 'true','Zenitvinkel [rad]', 'Instrumenthøjde [m]', 'Højde sigtepunkt [m]', 'Varians zenitvinkel hidrørende instrument, pr. sats  [rad^2]', 'Samlet varians instrumenthøjde/højde sigtepunkt [m^2]', 'Total varians zenitvinkel [rad^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Vektor der beskriver koordinatforskellen fra punkt 1 til punkt 1 (v2-v1)' , 'vektor', 'true','dx [m]', 'dy [m]', 'dz [m]', 'Afstandsafhængig varians [m^2/m^2]', 'Samlet varians for centrering af antenner [m^2]', 'Total varians [m^2]', 'Varians dx [m^2]', 'Varians dy [m^2]', 'Varians dz [m^2]', 'Covarians dx, dy [m^2]', 'Covarians dx, dz [m^2]', 'Covarians dy, dz [m^2]', NULL, NULL, NULL);

INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('observation nummer nul, indlagt fra start i observationstabellen, så der kan refereres til den i de mange beregningsevents der fører til population af koordinattabellen' , 'nulobservation', 'false', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

commit;
-- Oprettelse af første sag samt tilhørende sagsrelaterede informationer
INSERT INTO SAG (ID, REGISTRERINGFRA)
VALUES ('4f8f29c8-c38f-4c69-ae28-c7737178de1f', SYSDATE);

INSERT INTO SAGSINFO (AKTIV, SAGID, REGISTRERINGFRA, REGISTRERINGTIL, JOURNALNUMMER, BEHANDLER, BESKRIVELSE)
VALUES ('true','4f8f29c8-c38f-4c69-ae28-c7737178de1f', SYSDATE, NULL,  NULL, 'Thomas Knudsen', 'Sagen er oprette i forbindelse med migrering af data fra REFGEO til FIRE');

commit;
-- Nulobservationspunkt:
-- Første punkt i Punkt-tabellen. Udelukkende til brug for at at nulobservatioen kan henvise til det.

INSERT INTO SAGSEVENT (ID, REGISTRERINGFRA, EVENT, SAGID)
VALUES ('ce5d92cb-e890-411b-a836-0b3f19564500', SYSDATE, 'punkt_oprettet', '4f8f29c8-c38f-4c69-ae28-c7737178de1f');

INSERT INTO PUNKT (ID, REGISTRERINGFRA, REGISTRERINGTIL, SAGSEVENTID)
VALUES ('cb29ee7b-d5ab-4903-aecd-3860a80caf0b', SYSDATE, NULL, 'ce5d92cb-e890-411b-a836-0b3f19564500');

commit;
-- Første række i observationstabellen. 
-- Udelukkende til brug for at beregninger uden egentlige observationer kan overholde modellen.

INSERT INTO SAGSEVENT (ID, REGISTRERINGFRA, EVENT, SAGID)
VALUES ('a36bc4c3-cb99-4d69-b891-52f976d69451', SYSDATE, 'observation_indsat', '4f8f29c8-c38f-4c69-ae28-c7737178de1f');

INSERT INTO OBSERVATION (REGISTRERINGFRA, SAGSEVENTID, OBSERVATIONSTIDSPUNKT, ANTAL, OBSERVATIONSTYPE, OPSTILLINGSPUNKTID)
VALUES (SYSDATE, 'a36bc4c3-cb99-4d69-b891-52f976d69451', SYSDATE , 0, 'nulobservation', 'cb29ee7b-d5ab-4903-aecd-3860a80caf0b');

commit;


-- Oprettelse af sagsevents til anvendelsem ved migrering fra REFGEO til FIRE samt tilhørende sagsevent relaterede tabeller
INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT)
VALUES ('bruges når koordinater indsættes efter en beregning', 'koordinat_beregnet');

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT)
VALUES ('bruges når en koordinat nedlægges', 'koordinat_nedlagt');

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT)
VALUES ('Indsættelse af en eller flere observationer', 'observation_indsat');

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT)
VALUES ('bruges når en observation aflyses fordi den er fejlbehæftet', 'observation_nedlagt');

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT)
VALUES ('bruges når der tilføjes Punkinfo til et eller flere punkter', 'punktinfo_tilføjet');

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT)
VALUES ('bruges når Punktinfo fjernes fra et eller flere punkter', 'punktinfo_fjernet');

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT)
VALUES ('bruges når et punkt og tilhørende geometri oprettes', 'punkt_oprettet');

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT)
VALUES ('bruges når et punkt og tilhørende geometri nedlægges', 'punkt_nedlagt');

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT)
VALUES ('bruges når nye koordinater skabes. Knytter observationer til koordinater', 'beregning');

INSERT INTO EVENTTYPE (BESKRIVELSE, EVENT)
VALUES ('bruges til at tilføje fritekst kommentarer til sagen i tilfælde af at der er behov for at påhæfte sagen yderligere information som ikke passer i andre hændelser. Bruges fx også til påhæftning af materiale på sagen.', 'kommentar');

INSERT INTO SAGSEVENT (ID, REGISTRERINGFRA, EVENT, SAGID)
VALUES ('7f2952b7-7729-4952-8f05-b4f372abe939', SYSDATE, 'koordinat_beregnet', '4f8f29c8-c38f-4c69-ae28-c7737178de1f');

INSERT INTO SAGSEVENT (ID, REGISTRERINGFRA, EVENT, SAGID)
VALUES ('d4a8c021-3b6a-4efb-86fb-2e1b9d6dd694', SYSDATE, 'observation_indsat', '4f8f29c8-c38f-4c69-ae28-c7737178de1f');

INSERT INTO SAGSEVENT (ID, REGISTRERINGFRA, EVENT, SAGID)
VALUES ('15101d43-ac91-4c7c-9e58-c7a0b5367910', SYSDATE, 'punktinfo_tilføjet', '4f8f29c8-c38f-4c69-ae28-c7737178de1f');

INSERT INTO SAGSEVENT (ID, REGISTRERINGFRA, EVENT, SAGID)
VALUES ('e964cca6-7b16-414a-9538-8639eacaac3d', SYSDATE, 'punkt_oprettet', '4f8f29c8-c38f-4c69-ae28-c7737178de1f');

-- End