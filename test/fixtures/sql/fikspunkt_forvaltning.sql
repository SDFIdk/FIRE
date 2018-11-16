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

CREATE TABLE EVENTYPE (

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
   VALUE1 NUMBER NOT NULL,
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
   GRUPPE INTEGER,
   OBSERVATIONSTYPE VARCHAR2(4000) NOT NULL,
   SIGTEPUNKTID1 VARCHAR2(36),
   SIGTEPUNKTID2 VARCHAR2(36),
   OPSTILLINGSPUNKTID VARCHAR2(36) NOT NULL
);

CREATE TABLE OBSERVATIONTYPE (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   BESKRIVELSE VARCHAR2(4000) NOT NULL,
   OBSERVATIONSTYPE VARCHAR2(4000) NOT NULL,
   SIGTEPUNKT1 VARCHAR2(5) NOT NULL,
   SIGTEPUNKT2 VARCHAR2(5) NOT NULL,
   VALUE1 VARCHAR2(4000) NOT NULL,
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
   REELTAL NUMBER,
   TEKST VARCHAR2(4000),
   PUNKTID VARCHAR2(36) NOT NULL
);

CREATE TABLE PUNKTINFOTYPE (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   ANVENDELSE VARCHAR2(9) NOT NULL,
   BESKRIVELSE VARCHAR2(4000) NOT NULL,
   INFOTYPE VARCHAR2(4000) NOT NULL
);

CREATE TABLE PUNKTINFOTYPENAMESPACE (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   BESKRIVELSE VARCHAR2(4000) NOT NULL,
   NAMESPACE VARCHAR2(4000) NOT NULL
);

CREATE TABLE SAG (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   ID VARCHAR2(36) NOT NULL,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   SAGSTYPE VARCHAR2(21) NOT NULL,
   JOURNALNUMMER VARCHAR2(4000),
   BEHANDLER VARCHAR2(4000) NOT NULL,
   BESKRIVELSE VARCHAR2(4000)
);

CREATE TABLE SAGSEVENT (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   ID VARCHAR2(36) NOT NULL,
   REGISTRERINGFRA TIMESTAMP WITH TIME ZONE NOT NULL,
   REGISTRERINGTIL TIMESTAMP WITH TIME ZONE,
   EVENT VARCHAR2(4000) NOT NULL,
   BESKRIVELSE VARCHAR2(4000),
   SAGID VARCHAR2(36) NOT NULL
);

CREATE TABLE SAGSEVENT_MATERIALE (

   SAGSEVENTOBJECTID INTEGER NOT NULL,
   MATERIALE VARCHAR2(4000) NOT NULL,
   PRIMARY KEY (SAGSEVENTOBJECTID, MATERIALE)
);

CREATE TABLE SAGSEVENT_RAPPORTHTML (

   SAGSEVENTOBJECTID INTEGER NOT NULL,
   RAPPORTHTML VARCHAR2(4000) NOT NULL,
   PRIMARY KEY (SAGSEVENTOBJECTID, RAPPORTHTML)
);

CREATE TABLE SAGSTYPE (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   BESKRIVELSE VARCHAR2(4000) NOT NULL,
   SAGSTYPE VARCHAR2(4000) NOT NULL
);

CREATE TABLE SRIDNAMESPACE (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   BESKRIVELSE VARCHAR2(4000) NOT NULL,
   NAMESPACE VARCHAR2(4000) NOT NULL
);

CREATE TABLE SRIDTYPE (

   OBJECTID INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1 ORDER NOCACHE) PRIMARY KEY,
   BESKRIVELSE VARCHAR2(4000) NOT NULL,
   SRID VARCHAR2(36) NOT NULL
);


ALTER TABLE KOORDINAT ADD CONSTRAINT CK_KOORDINAT_TRANSFORMER248 CHECK (TRANSFORMERET IN ('true', 'false'));
ALTER TABLE OBSERVATIONTYPE ADD CONSTRAINT CK_OBSERVATION_SIGTEPUNKT1128 CHECK (SIGTEPUNKT1 IN ('true', 'false'));
ALTER TABLE OBSERVATIONTYPE ADD CONSTRAINT CK_OBSERVATION_SIGTEPUNKT2100 CHECK (SIGTEPUNKT2 IN ('true', 'false'));
ALTER TABLE PUNKTINFOTYPE ADD CONSTRAINT CK_PUNKTINFOTY_ANVENDELSE138 CHECK (ANVENDELSE IN ('FLAG', 'TAL', 'TEKST'));

INSERT INTO USER_SDO_GEOM_METADATA (TABLE_NAME, COLUMN_NAME, DIMINFO, SRID) VALUES ('GEOMETRIOBJEKT', 'GEOMETRI', MDSYS.SDO_DIM_ARRAY(MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005), MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)), 4326);

CREATE INDEX IDX_GEOMETRIOBJEKT_GEOMETRI ON GEOMETRIOBJEKT (GEOMETRI) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');

COMMENT ON TABLE BEREGNING IS 'Sammenknytter beregnede koordinater med de anvendte observationer.';
COMMENT ON COLUMN BEREGNING.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN BEREGNING.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN BEREGNING.SAGSEVENTID IS 'Angivelse af den hændelse der har ændret et fikspunktsobjekt.';
COMMENT ON COLUMN BEREGNING_KOORDINAT.KOORDINATOBJECTID IS 'Udpegning af de koordinater der er indgået i en beregning.';
COMMENT ON COLUMN BEREGNING_OBSERVATION.OBSERVATIONOBJECTID IS 'Udpegning af de observationer der er brugt i en beregning.';
COMMENT ON TABLE EVENTYPE IS 'Objekt til at holde liste over lovlige typer af events i fikspunktsforvaltningssystemet, samt en beskrivelse hvad eventtypen dækker over.';
COMMENT ON COLUMN EVENTYPE.BESKRIVELSE IS 'Kort beskrivelse af en eventype.';
COMMENT ON COLUMN EVENTYPE.EVENT IS 'Navngivning af en eventtype.';
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
COMMENT ON COLUMN OBSERVATION.OBSERVATIONSTYPE IS 'Kortnavn for observationstypen, fx dH';
COMMENT ON COLUMN OBSERVATION.OPSTILLINGSPUNKTID IS 'Udpegning af det punkt der er anvendt ved opstilling ved en observation.';
COMMENT ON COLUMN OBSERVATION.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN OBSERVATION.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN OBSERVATION.SAGSEVENTID IS 'Angivelse af den hændelse der har ændret et fikspunktsobjekt.';
COMMENT ON COLUMN OBSERVATION.SIGTEPUNKTID1 IS 'Udpegning af punktder er sigtet til ved en observation.';
COMMENT ON COLUMN OBSERVATION.SIGTEPUNKTID2 IS 'Udpegning af punktder er sigtet til ved en observation.';
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
COMMENT ON COLUMN OBSERVATIONTYPE.SIGTEPUNKT1 IS 'Indikator for om Sigtepunkt 1 anvendes for denne observationstype.';
COMMENT ON COLUMN OBSERVATIONTYPE.SIGTEPUNKT2 IS 'Indikator for om Sigtepunkt 2 anvendes for denne observationstype.';
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
COMMENT ON COLUMN PUNKTINFO.REELTAL IS 'Værdien for numeriske informationselementer';
COMMENT ON COLUMN PUNKTINFO.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN PUNKTINFO.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN PUNKTINFO.SAGSEVENTID IS 'Angivelse af den hændelse der har ændret et fikspunktsobjekt.';
COMMENT ON COLUMN PUNKTINFO.TEKST IS 'Værdien for tekstinformationselementer';
COMMENT ON TABLE PUNKTINFOTYPE IS 'Udfaldsrum for punktinforobjekter med definition af hvodan PunktInfo skal læses og beskrivelse af typen af punktinfo.';
COMMENT ON COLUMN PUNKTINFOTYPE.ANVENDELSE IS 'Er det reelTal, tekst, eller ingen af disse, der angiver værdien';
COMMENT ON COLUMN PUNKTINFOTYPE.BESKRIVELSE IS 'Beskrivelse af denne informationstypes art.';
COMMENT ON COLUMN PUNKTINFOTYPE.INFOTYPE IS 'Arten af dette informationselement';
COMMENT ON TABLE PUNKTINFOTYPENAMESPACE IS 'Type der afgrænser de lovlige namspaces der kan anvendes i tinfotype, samt en beskrivese af denne.';
COMMENT ON COLUMN PUNKTINFOTYPENAMESPACE.BESKRIVELSE IS 'Kort beskrivelse af hvad der dækkes af et punktinfonamespace.';
COMMENT ON COLUMN PUNKTINFOTYPENAMESPACE.NAMESPACE IS 'Navn på et lovlige namspace for en punktinformation.';
COMMENT ON TABLE SAG IS 'Samling af administrativt relaterede sagshændelser.';
COMMENT ON COLUMN SAG.BEHANDLER IS 'Angivelse af en sagsbehandler.';
COMMENT ON COLUMN SAG.BESKRIVELSE IS 'Kort beskrivelse af en fikspunktssag.';
COMMENT ON COLUMN SAG.ID IS 'Persistent unik nøgle.';
COMMENT ON COLUMN SAG.JOURNALNUMMER IS 'Sagsmappeidentifikation i opmålings- og beregningssagsregistret.';
COMMENT ON COLUMN SAG.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN SAG.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN SAG.SAGSTYPE IS 'Inddeling af fikspunktsager ud fra opgavetype.';
COMMENT ON TABLE SAGSEVENT IS 'Udvikling i sag som kan, men ikke behøver, medføre opdateringer af fikspunktregisterobjekter.';
COMMENT ON COLUMN SAGSEVENT.BESKRIVELSE IS 'Specifik beskrivelse af den aktuelle fremdrift.';
COMMENT ON COLUMN SAGSEVENT.EVENT IS 'Generisk beskrivelse af fremdriftens art.';
COMMENT ON COLUMN SAGSEVENT.ID IS 'Persistent unik nøgle.';
COMMENT ON COLUMN SAGSEVENT.REGISTRERINGFRA IS 'Tidspunktet hvor registreringen er foretaget.';
COMMENT ON COLUMN SAGSEVENT.REGISTRERINGTIL IS 'Tidspunktet hvor en ny registrering er foretaget på objektet, og hvor denne version således ikke længere er den seneste.';
COMMENT ON COLUMN SAGSEVENT.SAGID IS 'Udpegning af den sag i fikspunktsforvalningssystemet som en event er foretaget i.';
COMMENT ON COLUMN SAGSEVENT_MATERIALE.MATERIALE IS 'Generisk materiale tilknyttet sagsevent - typisk en filmappe URI.';
COMMENT ON COLUMN SAGSEVENT_RAPPORTHTML.RAPPORTHTML IS 'Generisk operatørlæsbart orienterende rapportmateriale.';
COMMENT ON TABLE SAGSTYPE IS 'Liste over typer af sager i fikspunktsregisterforvaltningssystemet med beskrivelse af hvad sagstypen dækker over.';
COMMENT ON COLUMN SAGSTYPE.BESKRIVELSE IS 'Lkort beskrivelse af hvad sagstypen dækker over.';
COMMENT ON COLUMN SAGSTYPE.SAGSTYPE IS 'Lovlig navn for en sagstype.';
COMMENT ON TABLE SRIDNAMESPACE IS 'Type der afgrænser de lovlige namspaces der kan anvendes i SRIDtype, samt en beskrivese af denne.';
COMMENT ON COLUMN SRIDNAMESPACE.BESKRIVELSE IS 'Kort beskrivelse af hvad der dækkes af et SRIDnamespace.';
COMMENT ON COLUMN SRIDNAMESPACE.NAMESPACE IS 'Navn på et lovlige namspace for en SRID.';
COMMENT ON TABLE SRIDTYPE IS 'Udfaldsrum for SRID-koordinatbeskrivelser.';
COMMENT ON COLUMN SRIDTYPE.BESKRIVELSE IS 'Generel beskrivelse af systemet.';
COMMENT ON COLUMN SRIDTYPE.SRID IS 'Den egentlige referencesystemindikator.';

-- Constraints og triggers ikke defineret i modellen
-- Constraint der tjekker at PUNKTID eksisterer
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
VALIDATE

ALTER TABLE OBSERVATION ADD 
CONSTRAINT observation_sp1_con_0001
FOREIGN KEY (SIGTEPUNKT_1ID)
REFERENCES PUNKT (ID)
ENABLE
VALIDATE

ALTER TABLE OBSERVATION ADD 
CONSTRAINT observation_sp2_con_0001
FOREIGN KEY (SIGTEPUNKT_2ID)
REFERENCES PUNKT (ID)
ENABLE
VALIDATE

ALTER TABLE OBSERVATION ADD 
CONSTRAINT observation_op1_con_0001
FOREIGN KEY (OPSTILLINGSPUNKTID)
REFERENCES PUNKT (ID)
ENABLE
VALIDATE

ALTER TABLE PUNKTINFO ADD 
CONSTRAINT punktinfo_con_001
FOREIGN KEY (PUNKTID)
REFERENCES PUNKT (ID)
ENABLE
VALIDATE

-- Constraint der tjekker at registreringtil er større end registreringfra
ALTER TABLE BEREGNING ADD 
CONSTRAINT beregning_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE   
   
ALTER TABLE GEOMETRIOBJEKT ADD 
CONSTRAINT geometriobjekt_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE      
   
ALTER TABLE KOORDINAT ADD 
CONSTRAINT KOORDINAT_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE    
   
ALTER TABLE OBSERVATION ADD 
CONSTRAINT OBSERVATION_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE  
 
 
ALTER TABLE PUNKT ADD 
CONSTRAINT PUNKT_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE 
 
 
ALTER TABLE PUNKTINFO ADD 
CONSTRAINT PUNKTINFO_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE 


ALTER TABLE SAG ADD 
CONSTRAINT SAG_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE 
 
 
ALTER TABLE SAGSEVENT ADD 
CONSTRAINT SAGSEVENT_con_0001
CHECK (nvl(registreringtil,to_timestamp_tz('31/12/2099 00:00:00.000000 +1:00','dd/mm/yyyy hh24:mi:ss.ff tzh:tzm')) >= registreringfra)
ENABLE
VALIDATE

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

IF :new.SIGTEPUNKT1ID != :old.SIGTEPUNKT1ID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.SIGTEPUNKT2ID != :old.SIGTEPUNKT2ID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

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

IF :new.SAGSTYPE != :old.SAGSTYPE THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;


IF :new.JOURNALNUMMER != :old.JOURNALNUMMER THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.BEHANDLER != :old.BEHANDLER THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.BESKRIVELSE != :old.BESKRIVELSE THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

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

IF :new.EVENT != :old.EVENT THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

IF :new.BESKRIVELSE != :old.BESKRIVELSE THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;


IF :new.SAGID != :old.SAGID THEN RAISE_APPLICATION_ERROR(20000,'You cannot update this column '); END IF;

end;
/




-- Constraints der sikre at punktinfotype er unikke, samt at de har korrekt namespace
CREATE UNIQUE INDEX PUNKTINFOTYPENAMESPACE_U01 ON PUNKTINFOTYPENAMESPACE
(NAMESPACE);



ALTER TABLE PUNKTINFOTYPENAMESPACE ADD (
  PRIMARY KEY
  (OBJECTID)
  USING INDEX
  ENABLE VALIDATE,
  CONSTRAINT PUNKTINFOTYPENAMESPACE_U01
  UNIQUE (NAMESPACE)
  USING INDEX PUNKTINFOTYPENAMESPACE_U01
  ENABLE VALIDATE);



ALTER TABLE PUNKTINFOTYPE ADD 
CONSTRAINT pt_con_0001
CHECK (substr(infotype,1,instr(infotype,':')-1) in 
('AFM',
'ATTR',
'IDENT',
'NET',
'PS',
'REGION',
'SKITSE'))
ENABLE
VALIDATE


ALTER TABLE OBSERVATIONTYPE ADD 
CONSTRAINT ot_con_0001
CHECK (substr(observationstype,1,instr(observationstype,':')-1) in ('OBS'))
ENABLE
VALIDATE


-- Indehold til observationtype
INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt1, sigtepunkt2, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Koteforskel fra fikspunkt1 til fikspunkt2 (h2-h1) opmålt geometrisk ', 'geometrisk_koteforskel', TRUE, FALSE, 'Koteforskel [m]', 'Nivellementslængde [m]', 'Antal opstillinger', 'Variabel vedr. eta_1 (refraktion) [m^3]', 'Afstandsafhængig varians koteforskel pr. målt koteforskel [m^2/m]', 'Afstandsuafhængig varians koteforskel pr. målt koteforskel [m^2]', 'Total varians koteforskel [m^2]', 'Præcisionsnivellement [0,1,2,3]', NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt1, sigtepunkt2, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Koteforskel fra fikspunkt1 til fikspunkt2 (h2-h1) opmålt trigonometrisk' , 'trigonometrisk_koteforskel', TRUE, FALSE, 'Koteforskel [m]', 'Nivellementslængde [m]', 'Antal opstillinger', 'Afstandsafhængig varians pr. målt koteforskel [m^2/m^2]', 'Afstandsuafhængig varians pr. målt koteforskel [m^2]', 'Total varians koteforskel [m^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt1, sigtepunkt2, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Horisontal retning med uret fra opstilling til sigtepunkt (reduceret til ellipsoiden)' , 'retning', TRUE, FALSE, 'Retning [m]', 'Varians  retning hidrørende instrument, pr. sats  [rad^2]', 'Samlet centreringsvarians for instrument prisme [m^2]', 'Total varians retning [rad^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt1, sigtepunkt2, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Horisontal afstand mellem opstilling og sigtepunkt (reduceret til ellipsoiden)' , 'horisontalafstand', TRUE, FALSE, 'Afstand [m]', 'Afstandsafhængig varians afstandsmåler [m^2/m^2]', 'Samlet varians for centrering af instrument og prisme, samt grundfejl på afstandsmåler [m^2]', 'Total varians horisontalafstand [m^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt1, sigtepunkt2, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Skråafstand mellem opstilling og sigtepunkt' , 'skråafstand', TRUE, FALSE, 'Afstand [m]', 'Afstandsafhængig varians afstandsmåler pr. måling [m^2/m^2]', 'Samlet varians for centrering af instrument og prisme, samt grundfejl på afstandsmåler pr. måling [m^2]', 'Total varians skråafstand [m^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt1, sigtepunkt2, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Zenitvinkel mellem opstilling og sigtepunkt' , 'zenitvinkel', TRUE, FALSE, 'Zenitvinkel [rad]', 'Instrumenthøjde [m]', 'Højde sigtepunkt [m]', 'Varians zenitvinkel hidrørende instrument, pr. sats  [rad^2]', 'Samlet varians instrumenthøjde/højde sigtepunkt [m^2]', 'Total varians zenitvinkel [rad^2]', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO observationtype (beskrivelse, observationstype, sigtepunkt1, sigtepunkt2, value1, value2, value3, value4, value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15)
VALUES ('Vektor der beskriver koordinatforskellen fra punkt 1 til punkt 1 (v2-v1)' , 'vektor', TRUE, FALSE, 'dx [m]', 'dy [m]', 'dz [m]', 'Afstandsafhængig varians [m^2/m^2]', 'Samlet varians for centrering af antenner [m^2]', 'Total varians [m^2]', 'Varians dx [m^2]', 'Varians dy [m^2]', 'Varians dz [m^2]', 'Covarians dx, dy [m^2]', 'Covarians dx, dz [m^2]', 'Covarians dy, dz [m^2]', NULL, NULL, NULL);

-- End