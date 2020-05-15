-------------------------------------------------------------------------------
--                              FIRE TEST DATA
-------------------------------------------------------------------------------
-- I denne fil oprettes test datasæt som er en forudsætning for at unit tests
-- af API kode kan afvikles. Datasættet fungerer desuden som en trykprøve af
-- datamodellen i FIRE, især med henblik på at teste sags- og eventstyring.

-- Datasættet inddeles i 5 sager, der simulerer to års kommunal vedligeholds-
-- opgaver på en strækning mellem domkirken i Aarhus og geodætisk vigtige
-- punkter i Aarhus N og Skejby. Det drejer sig om henholdvis 5D-punktet RDIO
-- den permanente GNSS station SKEJ.
--
-- Simuleringen forløber cirka som følgende
--
--  1. Bootstrap punkter, koordinatsystemer, mm.
--  2. Opmålingskampagne 2015: Indsæt observationer og koordinater
--  3. Punkt meldes tabtgået
--  4. Opmålingskampagne 2019: Indsæt observationer og koordinater
--  5. Afregistrer al information til det tabtgåede punkt (primært for at teste
--     håndtering af events og historik)

-- Data er til dels skabt ud fra indhold i testdatabasen der er etableret forud
-- for idrifttagelse af FIRE databasen. Hvor der er indsat udkommenterede
-- SELECT-statements er data trukket fra databasen. Udtrækkene er gemt her i
-- tilfælde det bliver nødvendigt at genskabe data på ny. Bemærk at punkt ID'er
-- ikke kan forventes at kunne genfindes i produktionsdatabasen.
-------------------------------------------------------------------------------


-------------------------------------------------------------------------------
--                            BOOTSTRAPPING DATA

-- SRID, punktinfotype osv
-------------------------------------------------------------------------------
-- Grundlæggende FIRE konfiguration
INSERT INTO konfiguration (
    dir_skitser,
    dir_materiale
) VALUES (
    'F:\GDB\FIRE\skitser',
    'F:\GDB\FIRE\materiale'
)

-- SELECT
--   infotypeid, infotype, anvendelse, beskrivelse FROM punktinfotype
-- WHERE infotype IN (
--  'IDENT:landsnr',
--  'IDENT:GNSS',
--  'ATTR:tabtgået'
--);
Insert into PUNKTINFOTYPE (INFOTYPEID,INFOTYPE,ANVENDELSE,BESKRIVELSE) values (347,'IDENT:GNSS','TEKST','GNNS Stationsnummer');
Insert into PUNKTINFOTYPE (INFOTYPEID,INFOTYPE,ANVENDELSE,BESKRIVELSE) values (346,'IDENT:landsnr','TEKST','Landsnummer');
Insert into PUNKTINFOTYPE (INFOTYPEID,INFOTYPE,ANVENDELSE,BESKRIVELSE) values (331,'ATTR:tabtgået','FLAG','Fysisk punkt ikke længere tilgængeligt');

-- Manuel indtastning, kun til testbrug.
Insert into PUNKTINFOTYPE (INFOTYPEID,INFOTYPE,ANVENDELSE,BESKRIVELSE) values (1,'ATTR:test','FLAG','Testattribut');

-- SELECT x,y,z,sridid, srid, beskrivelse FROM SRIDTYPE WHERE srid='EPSG:5799';
Insert into SRIDTYPE (X,Y,Z,SRIDID,SRID,BESKRIVELSE) values (null,null,'Kote [m]',8,'EPSG:5799','Kotesystem: Dansk Vertikal Reference 1990');


COMMIT;

-------------------------------------------------------------------------------
-- INDSÆT PUNKTER, GEOMETRIER OG PUNKTINFORMATION

-- Først indsættes en række punkter, der sidenhen bruges i forbindelse med
-- indsættelse af observationer og koordinater. Punkterne herunder kan
-- betragtes som gamle eksisterende punkter uden yderligere historik
-- (tilsvarende punkter skabt før migration fra REFGEO til FIRE).
-------------------------------------------------------------------------------
INSERT INTO sag (
    id,
    registreringfra
) VALUES (
    'sag00001-aaaa-bbbb-cccc-000000000001',
    sysdate
);

COMMIT;

INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagid
) VALUES (
    'true',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Indsættelse punkter mellem Aarhus Domkirke og GNSS station SKEJ via 5D-punkt RDIO',
    'sag00001-aaaa-bbbb-cccc-000000000001'
);

COMMIT;

INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagid
) VALUES (
    'sagevent-aaaa-bbbb-0001-000000000001',
    sysdate,
    7, -- oprettelse af punkt+geometri
    'sag00001-aaaa-bbbb-cccc-000000000001'
);

INSERT INTO sagseventinfo (
    REGISTRERINGFRA,
    REGISTRERINGTIL,
    BESKRIVELSE,
    SAGSEVENTID
) VALUES (
    sysdate,
    null,
    'Indsættelse af punkter og geometrier til testdata fra Aarhus',
    'sagevent-aaaa-bbbb-0001-000000000001'
);

COMMIT;


-- SELECT
--   p.id,
--   p.registreringfra,
--   p.registreringtil,
--   'sagevent-aaaa-bbbb-0001-000000000001' as sagseventfraid -- Dette skal korrespondere med ID fra tidligere indsat sagsevent
-- FROM punkt p
-- JOIN punktinfo pi ON pi.punktid = p.id
-- WHERE
--   pi.infotypeid = (SELECT infotypeid FROM punktinfotype WHERE infotype = 'IDENT:landsnr')
--     AND
--   pi.tekst IN (
--     'K-63-09946', -- G.M.902, Domkirken i Aarhus
--     'K-63-09944',
--     'K-63-09017',
--     'K-63-09933',
--     'K-63-09027',
--     'K-63-09451',
--     'K-63-09300',
--     'K-63-09191',
--     'K-63-09338',
--     'K-63-09141',
--     'K-63-09116',
--     'K-63-09446',
--     'K-63-09145',
--     'K-63-00909', -- RDIO, 5D-punkt ved Radiohuset, Aarhus
--     'K-63-19113',
--     'K-63-05436',
--     '102-08-09067',
--     '102-08-09060',
--     '102-08-00802' -- SKEJ, Permanent station i Aarhus
-- );
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('87d09ddc-42f3-41cf-a9b1-73f6ece692e6',to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('fd2627db-144d-4591-8bc7-d4c3afcdb92d',to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('4871c57b-d325-45fa-a03a-fdcff49273c0',to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('8718db7f-ae22-4cd9-aa56-fc8cea3b8c46',to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('bfe1d698-09fb-450a-81e7-4e2832b6bea7',to_timestamp_tz('1988-03-21 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('61c61847-ed54-4969-b94e-df74fd63f108',to_timestamp_tz('1991-02-03 00:34:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('67e3987a-dc6b-49ee-8857-417ef35777af',to_timestamp_tz('1991-02-03 00:34:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('8608b23d-479f-43b9-9e17-2d07041db842',to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('47285c0d-791d-4ca4-8d4a-e5a0db9f0746',to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('7a45fb99-0772-4be5-9182-d651d429b3b7',to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('d9cb77ab-2825-4f32-bb65-239aab7bfa67',to_timestamp_tz('1946-01-03 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('00380e23-ccf7-4655-9e55-8c299c8a0d6f',to_timestamp_tz('1946-11-07 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('301b8578-8cc8-48a8-8446-541f31482f86',to_timestamp_tz('1999-09-22 08:59:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('7ae0fe55-075a-4d21-8de1-4daee63d0de5',to_timestamp_tz('2019-02-28 20:23:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('4b4c5c17-32e8-495d-a598-cdf42e0892de',to_timestamp_tz('2015-11-25 13:23:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('b54a5515-d050-4049-bcb8-93a5e1039cc3',to_timestamp_tz('2015-11-25 13:25:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c',to_timestamp_tz('2019-01-08 08:38:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('fca43e51-5166-44b3-b941-c46915cd791b',to_timestamp_tz('2019-01-29 08:13:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');
Insert into PUNKT (ID,REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID) values ('c3d38a21-329e-474a-a4d1-068e8219b622',to_timestamp_tz('1700-03-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001');

COMMIT;

-- SELECT
--   g.registreringfra,
--   g.registreringtil,
--   'sagevent-aaaa-bbbb-0001-000000000001' as sagseventfraid,
--   g.sagseventtilid,
--   g.punktid,
--   g.geometri
-- FROM
--   geometriobjekt g
-- JOIN punktinfo pi ON g.punktid = pi.punktid
-- WHERE
--   pi.infotypeid = (SELECT infotypeid FROM punktinfotype WHERE infotype = 'IDENT:landsnr')
--     AND
--   pi.tekst IN (
--     'K-63-09946', -- G.M.902, Domkirken i Aarhus
--     'K-63-09944',
--     'K-63-09017',
--     'K-63-09933',
--     'K-63-09027',
--     'K-63-09451',
--     'K-63-09300',
--     'K-63-09191',
--     'K-63-09338',
--     'K-63-09141',
--     'K-63-09446',
--     'K-63-09145',
--     'K-63-00909', -- RDIO, 5D-punkt ved Radiohuset, Aarhus
--     'K-63-19113',
--     'K-63-05436',
--     '102-08-09067',
--     '102-08-09060',
--     '102-08-00802' -- SKEJ, Permanent station i Aarhus
-- );
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('2001-07-31 12:32:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'87d09ddc-42f3-41cf-a9b1-73f6ece692e6',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.2118455581149312477800821259087457756,56.15836989928831704282196112013597360986,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('2009-05-19 13:20:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'fd2627db-144d-4591-8bc7-d4c3afcdb92d',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.21164447348075751181215359132504892263,56.16198612317136722246758414491203875208,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('1934-02-02 12:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'4871c57b-d325-45fa-a03a-fdcff49273c0',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.20753284870787350433549478363194392193,56.16768503132520323874510978378037388227,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('1994-10-04 12:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'8718db7f-ae22-4cd9-aa56-fc8cea3b8c46',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.20307332580492196004911919781442754974,56.17288610959091174949333117551133512338,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('1997-06-23 15:28:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'bfe1d698-09fb-450a-81e7-4e2832b6bea7',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.21336101878642842916300500963354543729,56.16047559438626864707438224916374519188,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('2001-05-07 12:57:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'61c61847-ed54-4969-b94e-df74fd63f108',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.21147626020366636853001005326049110193,56.15680942928517814595259381593053437526,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('1997-08-27 13:42:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'67e3987a-dc6b-49ee-8857-417ef35777af',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.21126093527880157804208716243735084463,56.15673549027781002830332076738859122403,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('1934-02-02 12:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'8608b23d-479f-43b9-9e17-2d07041db842',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.20081703198857687415324237189273033074,56.17645726467592676301595354922643301699,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('1934-02-02 12:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'47285c0d-791d-4ca4-8d4a-e5a0db9f0746',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.19616205331323212854274065878936787364,56.18320546052818322031246713524564585082,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('1934-02-02 12:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'7a45fb99-0772-4be5-9182-d651d429b3b7',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.20717446721802150695736873068683105148,56.17063574033886545390661151579227408376,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('1986-03-11 05:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'d9cb77ab-2825-4f32-bb65-239aab7bfa67',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.19959539442736963942695489334749656191,56.178607639836412065841174229108599557,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('1934-02-02 12:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'00380e23-ccf7-4655-9e55-8c299c8a0d6f',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.20865908284327341123170507687154351302,56.16559839782867267575725378751763198621,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('2011-12-21 11:05:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'301b8578-8cc8-48a8-8446-541f31482f86',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.190150115937,56.189108084217,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('2019-02-28 20:39:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'7ae0fe55-075a-4d21-8de1-4daee63d0de5',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.1805394121386,56.187777271417,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('2015-11-26 09:31:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'4b4c5c17-32e8-495d-a598-cdf42e0892de',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.1893294601724,56.1895539111211,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('2015-11-26 09:31:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'b54a5515-d050-4049-bcb8-93a5e1039cc3',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.1897838269445,56.1895001202013,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('2019-04-30 16:32:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.1798368394234,56.1875902684707,NULL),NULL,NULL));
Insert into GEOMETRIOBJEKT (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,SAGSEVENTTILID,PUNKTID,GEOMETRI) values (to_timestamp_tz('2019-02-01 15:58:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000001',null,'fca43e51-5166-44b3-b941-c46915cd791b',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.1798186526554,56.1875938043434,NULL),NULL,NULL));

COMMIT;

-------------------------------------------------------------------------------
-- INDSÆT IDENTER OG ANDRE ATTRIBUTTER I PUNKTINFO
--
-- Der indsættes landsnumre og GNSS-identer. Desuden indsættes en enkelte test-
-- attribut med henblik på senere fjernelse.
-------------------------------------------------------------------------------

INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagid
) VALUES (
    'sagevent-aaaa-bbbb-0001-000000000002',
    sysdate,
    5, -- oprettelse af punktinfo
    'sag00001-aaaa-bbbb-cccc-000000000001'
);

INSERT INTO sagseventinfo (
    REGISTRERINGFRA,
    REGISTRERINGTIL,
    BESKRIVELSE,
    SAGSEVENTID
) VALUES (
    sysdate,
    null,
    'Indsættelse af punktinfo til punkter',
    'sagevent-aaaa-bbbb-0001-000000000002'
);

-- Indsæt punktinfo: identer
-- SELECT
--   pi.registreringfra, pi.registreringtil,
--   'sagevent-aaaa-bbbb-0001-000000000002' as sagseventfraid,
--   pi.infotypeid, pi.tal, pi.tekst, pi.punktid
-- FROM
--   punktinfo pi
-- WHERE
--   pi.PUNKTID IN (
--     SELECT punktid FROM punktinfo WHERE tekst IN (
--       'K-63-09946', -- G.M.902, Domkirken i Aarhus
--       'K-63-09944',
--       'K-63-09017',
--       'K-63-09933',
--       'K-63-09027',
--       'K-63-09451',
--       'K-63-09300',
--       'K-63-09191',
--       'K-63-09338',
--       'K-63-09141',
--       'K-63-09116',
--       'K-63-09446',
--       'K-63-09145',
--       'K-63-00909', -- RDIO, 5D-punkt ved Radiohuset, Aarhus
--       'K-63-19113',
--       'K-63-05436',
--       '102-08-09067',
--       '102-08-09060',
--       '102-08-00802' -- SKEJ, Permanent station i Aarhus
--     )
--   )
--     AND
--   pi.infotypeid IN (
--     SELECT infotypeid FROM punktinfotype WHERE infotype IN (
--       'IDENT:landsnr',
--       'IDENT:GNSS'
--     )
--   )
-- ;
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1946-11-07 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-09451','00380e23-ccf7-4655-9e55-8c299c8a0d6f');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1999-09-22 08:59:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',347,null,'RDIO','301b8578-8cc8-48a8-8446-541f31482f86');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1999-09-22 08:59:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-00909','301b8578-8cc8-48a8-8446-541f31482f86');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-09145','47285c0d-791d-4ca4-8d4a-e5a0db9f0746');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-09300','4871c57b-d325-45fa-a03a-fdcff49273c0');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('2015-11-25 13:23:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',347,null,'RDO1','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('2015-11-25 13:23:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-05436','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1991-02-03 00:34:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-09944','61c61847-ed54-4969-b94e-df74fd63f108');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1991-02-03 00:34:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-09946','67e3987a-dc6b-49ee-8857-417ef35777af');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-09191','7a45fb99-0772-4be5-9182-d651d429b3b7');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('2019-02-28 20:23:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'102-08-09067','7ae0fe55-075a-4d21-8de1-4daee63d0de5');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-09141','8608b23d-479f-43b9-9e17-2d07041db842');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-09338','8718db7f-ae22-4cd9-aa56-fc8cea3b8c46');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-09017','87d09ddc-42f3-41cf-a9b1-73f6ece692e6');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('2019-01-08 08:38:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',347,null,'SKEJ','8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('2019-01-08 08:38:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'102-08-00802','8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('2015-11-25 13:25:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-19113','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1988-03-21 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-09933','bfe1d698-09fb-450a-81e7-4e2832b6bea7');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1946-01-03 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-09446','d9cb77ab-2825-4f32-bb65-239aab7bfa67');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('2019-01-29 08:13:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'102-08-09060','fca43e51-5166-44b3-b941-c46915cd791b');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1946-07-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-09027','fd2627db-144d-4591-8bc7-d4c3afcdb92d');
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (to_timestamp_tz('1700-03-01 00:00:00','YYYY-MM-DD HH24:MI:SS'),null,'sagevent-aaaa-bbbb-0001-000000000002',346,null,'K-63-09116','c3d38a21-329e-474a-a4d1-068e8219b622');


-- Manuel indsættelse
Insert into PUNKTINFO (REGISTRERINGFRA,REGISTRERINGTIL,SAGSEVENTFRAID,INFOTYPEID,TAL,TEKST,PUNKTID) values (sysdate, null,'sagevent-aaaa-bbbb-0001-000000000002',1,null,null,'d9cb77ab-2825-4f32-bb65-239aab7bfa67');

COMMIT;

-------------------------------------------------------------------------------
-- INDSÆT EKSISTERENDE KOORDINATER
--
-- Der indsættes koordinater på få af de ældre punkter i datasættet. Disse
-- opdateres ikke senere i forløbet, og kan fx bruges som fastholdte koter i
-- testudjævninger.
-------------------------------------------------------------------------------

INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagid
) VALUES (
    'sagevent-aaaa-bbbb-0001-000000000003',
    sysdate,
    1, -- koordinat beregnet
    'sag00001-aaaa-bbbb-cccc-000000000001'
);

INSERT INTO sagseventinfo (
    REGISTRERINGFRA,
    REGISTRERINGTIL,
    BESKRIVELSE,
    SAGSEVENTID
) VALUES (
    sysdate,
    null,
    'Indsættelse af koordinater',
    'sagevent-aaaa-bbbb-0001-000000000003'
);

SELECT
  k.registreringfra, 'sagevent-aaaa-bbbb-0001-000000000003' as sagseventfraid,
  k.sridid, k.x, k.y, k.z, k.sx, k.sy, k.sz, k.t, k.transformeret,
  k.artskode,  k.punktid
FROM
  koordinat k
JOIN punktinfo pi ON k.punktid = pi.punktid
WHERE
  k.sridid IN (SELECT sridid FROM sridtype WHERE srid = 'EPSG:5799')
    AND
  pi.infotypeid = (SELECT infotypeid FROM punktinfotype WHERE infotype = 'IDENT:landsnr')
    AND
  pi.tekst IN (
    'K-63-09946', -- G.M.902, Domkirken i Aarhus
    'K-63-09944',
    'K-63-00909' -- RDIO, 5D-punkt ved Radiohuset, Aarhus
) AND k.registreringtil IS NULL;

Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2009-10-20 12:11:07','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0001-000000000003',8,null,null,2.8318,null,null,0,to_timestamp_tz('2000-02-11 13:30:00','YYYY-MM-DD HH24:MI:SS'),'false',1,'61c61847-ed54-4969-b94e-df74fd63f108');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2001-07-31 12:32:02','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0001-000000000003',8,null,null,5.5700000000000003,null,null,0,to_timestamp_tz('2001-07-31 08:54:00','YYYY-MM-DD HH24:MI:SS'),'false',1,'67e3987a-dc6b-49ee-8857-417ef35777af');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2003-11-07 10:53:02','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0001-000000000003',8,null,null,85.181,null,null,0,to_timestamp_tz('2001-02-28 12:45:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'301b8578-8cc8-48a8-8446-541f31482f86');

INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagid
) VALUES (
    'false',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Indsættelse punkter mellem Aarhus Domkirke og GNSS station SKEJ via 5D-punkt RDIO',
    'sag00001-aaaa-bbbb-cccc-000000000001'
);

COMMIT;


-------------------------------------------------------------------------------
-- OPMÅLINGSKAMPAGNE 2015

-- Indsæt observationer, koordinater og beregning
-------------------------------------------------------------------------------

INSERT INTO sag (
    id,
    registreringfra
) VALUES (
    'sag00002-aaaa-bbbb-cccc-000000000001',
    sysdate
);

COMMIT;

INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagid
) VALUES (
    'true',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Opmålingskampagne 2015',
    'sag00002-aaaa-bbbb-cccc-000000000001'
);

COMMIT;



INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagid
) VALUES (
    'sagevent-aaaa-bbbb-0002-000000000001',
    sysdate,
    3, -- indsættelse af observationer
    'sag00002-aaaa-bbbb-cccc-000000000001'
);

COMMIT;

INSERT INTO sagseventinfo (
    REGISTRERINGFRA,
    REGISTRERINGTIL,
    BESKRIVELSE,
    SAGSEVENTID
) VALUES (
    sysdate,
    null,
    'Indsættelse af observationer',
    'sagevent-aaaa-bbbb-0002-000000000001'
);

COMMIT;

-- SELECT
--   o.registreringfra,
--   o.value1, o.value2, o.value3, o.value4, o.value5, o.value6, o.value7,
--   'sagevent-aaaa-bbbb-0002-000000000001' as sagseventfraid,
--   o.observationstypeid, o.antal, o.gruppe, o.observationstidspunkt,
--   o.opstillingspunktid, o.sigtepunktid
-- FROM
--   observation o
-- JOIN punktinfo pio ON pio.punktid = o.opstillingspunktid
-- JOIN punktinfo pis ON pis.punktid = o.sigtepunktid
-- WHERE
--   pio.infotypeid = (SELECT infotypeid FROM punktinfotype WHERE infotype = 'IDENT:landsnr')
--     AND
--   pio.tekst IN (
--     'K-63-09946', -- G.M.902, Domkirken i Aarhus
--     'K-63-09944',
--     'K-63-09017',
--     'K-63-09933',
--     'K-63-09027',
--     'K-63-09451',
--     'K-63-09300',
--     'K-63-09191',
--     'K-63-09338',
--     'K-63-09141',
--     'K-63-09446',
--     'K-63-09145',
--     'K-63-00909', -- RDIO, 5D-punkt ved Radiohuset, Aarhus
--     'K-63-19113',
--     'K-63-05436',
--     '102-08-09067',
--     '102-08-09060',
--     '102-08-00802') -- SKEJ, Permanent station i Aarhus
--     AND
--   pis.infotypeid = (SELECT infotypeid FROM punktinfotype WHERE infotype = 'IDENT:landsnr')
--     AND
--   pis.tekst IN (
--     'K-63-09946', -- G.M.902, Domkirken i Aarhus
--     'K-63-09944',
--     'K-63-09017',
--     'K-63-09933',
--     'K-63-09027',
--     'K-63-09451',
--     'K-63-09300',
--     'K-63-09191',
--     'K-63-09338',
--     'K-63-09141',
--     'K-63-09446',
--     'K-63-09145',
--     'K-63-00909', -- RDIO, 5D-punkt ved Radiohuset, Aarhus
--     'K-63-19113',
--     'K-63-05436',
--     '102-08-09067',
--     '102-08-09060',
--     '102-08-00802') -- SKEJ, Permanent station i Aarhus;
--     AND
--   to_char(o.registreringfra, 'YYYY') = '2016'
-- ;

Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),1.01596,230,4,0,0.00000023,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,42861,to_timestamp_tz('2015-11-11 11:27:00','YYYY-MM-DD HH24:MI:SS'),'bfe1d698-09fb-450a-81e7-4e2832b6bea7','87d09ddc-42f3-41cf-a9b1-73f6ece692e6');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),2.18702,182,2,0,0.000000182,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85401,to_timestamp_tz('2015-11-11 10:05:00','YYYY-MM-DD HH24:MI:SS'),'61c61847-ed54-4969-b94e-df74fd63f108','87d09ddc-42f3-41cf-a9b1-73f6ece692e6');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),1.79568,205,3,0,0.000000205,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,42868,to_timestamp_tz('2015-11-11 11:40:00','YYYY-MM-DD HH24:MI:SS'),'bfe1d698-09fb-450a-81e7-4e2832b6bea7','fd2627db-144d-4591-8bc7-d4c3afcdb92d');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-20.22457,540,12,0,0.00000054,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85404,to_timestamp_tz('2015-11-12 14:45:00','YYYY-MM-DD HH24:MI:SS'),'00380e23-ccf7-4655-9e55-8c299c8a0d6f','fd2627db-144d-4591-8bc7-d4c3afcdb92d');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),12.75784,281,7,0,0.000000281,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,14536,to_timestamp_tz('2015-11-11 12:25:00','YYYY-MM-DD HH24:MI:SS'),'00380e23-ccf7-4655-9e55-8c299c8a0d6f','4871c57b-d325-45fa-a03a-fdcff49273c0');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-8.91615,579,9,0,0.000000579,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85423,to_timestamp_tz('2015-11-12 13:46:00','YYYY-MM-DD HH24:MI:SS'),'7a45fb99-0772-4be5-9182-d651d429b3b7','4871c57b-d325-45fa-a03a-fdcff49273c0');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-13.1971,522,8,0,0.000000522,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85414,to_timestamp_tz('2015-11-12 12:53:00','YYYY-MM-DD HH24:MI:SS'),'8608b23d-479f-43b9-9e17-2d07041db842','8718db7f-ae22-4cd9-aa56-fc8cea3b8c46');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),8.11043,441,7,0,0.000000441,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,14513,to_timestamp_tz('2015-11-11 13:12:00','YYYY-MM-DD HH24:MI:SS'),'7a45fb99-0772-4be5-9182-d651d429b3b7','8718db7f-ae22-4cd9-aa56-fc8cea3b8c46');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-1.01612,229,4,0,0.000000229,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,42861,to_timestamp_tz('2015-11-11 11:19:00','YYYY-MM-DD HH24:MI:SS'),'87d09ddc-42f3-41cf-a9b1-73f6ece692e6','bfe1d698-09fb-450a-81e7-4e2832b6bea7');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-1.79588,243,3,0,0.000000243,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,42868,to_timestamp_tz('2015-11-12 14:55:00','YYYY-MM-DD HH24:MI:SS'),'fd2627db-144d-4591-8bc7-d4c3afcdb92d','bfe1d698-09fb-450a-81e7-4e2832b6bea7');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-2.73684,27,2,0,0.000000027,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,57168,to_timestamp_tz('2015-11-24 15:30:00','YYYY-MM-DD HH24:MI:SS'),'67e3987a-dc6b-49ee-8857-417ef35777af','61c61847-ed54-4969-b94e-df74fd63f108');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-2.18711,182,2,0,0.000000182,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85401,to_timestamp_tz('2015-11-11 10:12:00','YYYY-MM-DD HH24:MI:SS'),'87d09ddc-42f3-41cf-a9b1-73f6ece692e6','61c61847-ed54-4969-b94e-df74fd63f108');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),2.73689,27,2,0,0.000000027,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,57168,to_timestamp_tz('2015-11-24 15:26:00','YYYY-MM-DD HH24:MI:SS'),'61c61847-ed54-4969-b94e-df74fd63f108','67e3987a-dc6b-49ee-8857-417ef35777af');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-5.62311,325,5,0,0.000000325,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,99524,to_timestamp_tz('2015-11-12 12:36:00','YYYY-MM-DD HH24:MI:SS'),'d9cb77ab-2825-4f32-bb65-239aab7bfa67','8608b23d-479f-43b9-9e17-2d07041db842');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),13.19823,481,7,0,0.000000481,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85414,to_timestamp_tz('2015-11-11 13:31:00','YYYY-MM-DD HH24:MI:SS'),'8718db7f-ae22-4cd9-aa56-fc8cea3b8c46','8608b23d-479f-43b9-9e17-2d07041db842');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),7.90343,680,8,0,0.00000068,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,28723,to_timestamp_tz('2015-11-11 14:13:00','YYYY-MM-DD HH24:MI:SS'),'d9cb77ab-2825-4f32-bb65-239aab7bfa67','47285c0d-791d-4ca4-8d4a-e5a0db9f0746');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-2.65984,839,10,0,0.000000839,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,71352,to_timestamp_tz('2015-11-11 16:11:00','YYYY-MM-DD HH24:MI:SS'),'301b8578-8cc8-48a8-8446-541f31482f86','47285c0d-791d-4ca4-8d4a-e5a0db9f0746');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),8.91614,500,8,0,0.0000005,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85423,to_timestamp_tz('2015-11-11 12:48:00','YYYY-MM-DD HH24:MI:SS'),'4871c57b-d325-45fa-a03a-fdcff49273c0','7a45fb99-0772-4be5-9182-d651d429b3b7');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-8.11047,435,6,0,0.000000435,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,14513,to_timestamp_tz('2015-11-12 13:19:00','YYYY-MM-DD HH24:MI:SS'),'8718db7f-ae22-4cd9-aa56-fc8cea3b8c46','7a45fb99-0772-4be5-9182-d651d429b3b7');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),5.62317,293,4,0,0.000000293,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,99524,to_timestamp_tz('2015-11-11 13:43:00','YYYY-MM-DD HH24:MI:SS'),'8608b23d-479f-43b9-9e17-2d07041db842','d9cb77ab-2825-4f32-bb65-239aab7bfa67');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-7.90367,587,8,0,0.000000587,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,28723,to_timestamp_tz('2015-11-12 12:23:00','YYYY-MM-DD HH24:MI:SS'),'47285c0d-791d-4ca4-8d4a-e5a0db9f0746','d9cb77ab-2825-4f32-bb65-239aab7bfa67');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-12.75732,335,7,0,0.000000335,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,14536,to_timestamp_tz('2015-11-12 14:09:00','YYYY-MM-DD HH24:MI:SS'),'4871c57b-d325-45fa-a03a-fdcff49273c0','00380e23-ccf7-4655-9e55-8c299c8a0d6f');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),20.22451,505,10,0,0.000000505,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85404,to_timestamp_tz('2015-11-11 12:10:00','YYYY-MM-DD HH24:MI:SS'),'fd2627db-144d-4591-8bc7-d4c3afcdb92d','00380e23-ccf7-4655-9e55-8c299c8a0d6f');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),2.66051,899,11,0,0.000000899,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,71352,to_timestamp_tz('2015-11-11 15:25:00','YYYY-MM-DD HH24:MI:SS'),'47285c0d-791d-4ca4-8d4a-e5a0db9f0746','301b8578-8cc8-48a8-8446-541f31482f86');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-0.75308,69,1,0,0.000000069,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,5671,to_timestamp_tz('2015-11-24 13:30:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','301b8578-8cc8-48a8-8446-541f31482f86');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-0.75308,68,1,0,0.000000068,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,5671,to_timestamp_tz('2015-11-24 13:35:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','301b8578-8cc8-48a8-8446-541f31482f86');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),0.2431,31,1,0,0.000000031,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,106103,to_timestamp_tz('2015-11-24 13:09:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),0.24311,30,1,0,0.00000003,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,106103,to_timestamp_tz('2015-11-25 11:19:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),0.75314,69,1,0,0.000000069,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,5671,to_timestamp_tz('2015-11-24 13:27:00','YYYY-MM-DD HH24:MI:SS'),'301b8578-8cc8-48a8-8446-541f31482f86','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),0.753,68,1,0,0.000000068,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,5671,to_timestamp_tz('2015-11-24 13:33:00','YYYY-MM-DD HH24:MI:SS'),'301b8578-8cc8-48a8-8446-541f31482f86','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-0.24307,31,1,0,0.000000031,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,106103,to_timestamp_tz('2015-11-24 13:11:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-0.24308,30,1,0,0.00000003,0.0000000001,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,106103,to_timestamp_tz('2015-11-25 11:21:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','b54a5515-d050-4049-bcb8-93a5e1039cc3');

COMMIT;


INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagid
) VALUES (
    'sagevent-aaaa-bbbb-0002-000000000002',
    sysdate,
    1, -- indsættelse af koordinater
    'sag00002-aaaa-bbbb-cccc-000000000001'
);

INSERT INTO sagseventinfo (
    REGISTRERINGFRA,
    REGISTRERINGTIL,
    BESKRIVELSE,
    SAGSEVENTID
) VALUES (
    sysdate,
    null,
    'Indsættelse af koordinater',
    'sagevent-aaaa-bbbb-0002-000000000002'
);

COMMIT;

-- SELECT
--   k.registreringfra, 'sagevent-aaaa-bbbb-0002-000000000002' as sagseventfraid,
--   k.sridid, k.x, k.y, k.z, k.sx, k.sy, k.sz, k.t, k.transformeret,
--   k.artskode,  k.punktid
-- FROM
--   koordinat k
-- JOIN punktinfo pi ON k.punktid = pi.punktid
-- WHERE
--   k.sridid IN (SELECT sridid FROM sridtype WHERE srid = 'EPSG:5799')
--     AND
--   pi.infotypeid = (SELECT infotypeid FROM punktinfotype WHERE infotype = 'IDENT:landsnr')
--     AND
--   pi.tekst IN (
--     'K-63-09946', -- G.M.902, Domkirken i Aarhus
--     'K-63-09944',
--     'K-63-09017',
--     'K-63-09933',
--     'K-63-09027',
--     'K-63-09451',
--     'K-63-09300',
--     'K-63-09191',
--     'K-63-09338',
--     'K-63-09141',
--     'K-63-09446',
--     'K-63-09145',
--     'K-63-00909', -- RDIO, 5D-punkt ved Radiohuset, Aarhus
--     'K-63-19113',
--     'K-63-05436',
--     '102-08-09067',
--     '102-08-09060',
--     '102-08-00802' -- SKEJ, Permanent station i Aarhus
-- )
--      AND
--   to_char(k.registreringfra, 'YYYY-MM-DD') = '2016-01-25'
-- ;
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:02','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,26.01279,null,null,1,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'00380e23-ccf7-4655-9e55-8c299c8a0d6f');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:08','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,82.52137,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'47285c0d-791d-4ca4-8d4a-e5a0db9f0746');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:05','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,38.77039,null,null,1,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'4871c57b-d325-45fa-a03a-fdcff49273c0');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:38:58','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,86.17772,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:01','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,47.68654,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'7a45fb99-0772-4be5-9182-d651d429b3b7');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:03','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,68.99467,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'8608b23d-479f-43b9-9e17-2d07041db842');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:05','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,55.79699,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'8718db7f-ae22-4cd9-aa56-fc8cea3b8c46');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:04','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,5.00852,null,null,1,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'87d09ddc-42f3-41cf-a9b1-73f6ece692e6');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:38:58','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,85.93462,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:07','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,3.99248,null,null,1,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'bfe1d698-09fb-450a-81e7-4e2832b6bea7');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:04','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,74.61782,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'d9cb77ab-2825-4f32-bb65-239aab7bfa67');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:05','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,5.78825,null,null,1,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'fd2627db-144d-4591-8bc7-d4c3afcdb92d');

-- Opretning beregning
INSERT INTO beregning (registreringfra, sagseventfraid) VALUES (sysdate, 'sagevent-aaaa-bbbb-0002-000000000002');

INSERT INTO beregning_observation (beregningobjectid, observationobjectid)
SELECT (SELECT objectid FROM beregning WHERE sagseventfraid = 'sagevent-aaaa-bbbb-0002-000000000002'), o.objectid
FROM observation o
WHERE o.sagseventfraid = 'sagevent-aaaa-bbbb-0002-000000000001';

INSERT INTO beregning_koordinat (beregningobjectid, koordinatobjectid)
SELECT (SELECT objectid FROM beregning WHERE sagseventfraid = 'sagevent-aaaa-bbbb-0002-000000000002'), k.objectid
FROM koordinat k
WHERE k.sagseventfraid = 'sagevent-aaaa-bbbb-0002-000000000002';


INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagid
) VALUES (
    'false',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Opmålingskampagne 2015',
    'sag00002-aaaa-bbbb-cccc-000000000001'
);

COMMIT;



-------------------------------------------------------------------------------
-- TABTGÅET PUNKT

-- Meld punkt 'K-63-09446' tabtgået
-------------------------------------------------------------------------------


INSERT INTO sag (
    id,
    registreringfra
) VALUES (
    'sag00003-aaaa-bbbb-cccc-000000000001',
    sysdate
);

COMMIT;

INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagid
) VALUES (
    'true',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Punkt K-63-09446 tabtgået',
    'sag00003-aaaa-bbbb-cccc-000000000001'
);

COMMIT;



INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagid
) VALUES (
    'sagevent-aaaa-bbbb-0003-000000000001',
    sysdate,
    5, -- punktinfo tilføjet
    'sag00003-aaaa-bbbb-cccc-000000000001'
);

COMMIT;

INSERT INTO sagseventinfo (
    REGISTRERINGFRA,
    REGISTRERINGTIL,
    BESKRIVELSE,
    SAGSEVENTID
) VALUES (
    sysdate,
    null,
    'Tilføjelse af ATTR:tabtgået til punkt K-63-09446',
    'sagevent-aaaa-bbbb-0003-000000000001'
);

COMMIT;


INSERT INTO punktinfo (
    registreringfra,
    sagseventfraid,
    infotypeid,
    punktid
) VALUES (
    sysdate,
    'sagevent-aaaa-bbbb-0003-000000000001',
    (SELECT infotypeid FROM punktinfotype WHERE infotype='ATTR:tabtgået'),
    (SELECT punktid FROM punktinfo WHERE tekst='K-63-09446')
);

COMMIT;

INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagid
) VALUES (
    'false',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Punkt K-63-09446 tabtgået',
    'sag00003-aaaa-bbbb-cccc-000000000001'
);

COMMIT;

-------------------------------------------------------------------------------
-- OPMÅLINGSKAMPAGNE 2019

-- Indsæt observationer, koordinater og beregning
-------------------------------------------------------------------------------


INSERT INTO sag (
    id,
    registreringfra
) VALUES (
    'sag00004-aaaa-bbbb-cccc-000000000001',
    sysdate
);

COMMIT;

INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagid
) VALUES (
    'true',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Opmålingskampagne 2019',
    'sag00004-aaaa-bbbb-cccc-000000000001'
);

COMMIT;



INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagid
) VALUES (
    'sagevent-aaaa-bbbb-0004-000000000001',
    sysdate,
    3, -- observationer indsat
    'sag00004-aaaa-bbbb-cccc-000000000001'
);

COMMIT;

INSERT INTO sagseventinfo (
    REGISTRERINGFRA,
    REGISTRERINGTIL,
    BESKRIVELSE,
    SAGSEVENTID
) VALUES (
    sysdate,
    null,
    'Indsættelse af observationer',
    'sagevent-aaaa-bbbb-0004-000000000001'
);

COMMIT;

-- SELECT
--   o.registreringfra,
--   o.value1, o.value2, o.value3, o.value4, o.value5, o.value6, o.value7,
--   'sagevent-aaaa-bbbb-0004-000000000001' as sagseventfraid,
--   o.observationstypeid, o.antal, o.gruppe, o.observationstidspunkt,
--   o.opstillingspunktid, o.sigtepunktid
-- FROM
--   observation o
-- JOIN punktinfo pio ON pio.punktid = o.opstillingspunktid
-- JOIN punktinfo pis ON pis.punktid = o.sigtepunktid
-- WHERE
--  pio.infotypeid = (SELECT infotypeid FROM punktinfotype WHERE infotype = 'IDENT:landsnr')
--     AND
--   pio.tekst IN (
--     'K-63-09946', -- G.M.902, Domkirken i Aarhus
--     'K-63-09944',
--     'K-63-09017',
--     'K-63-09933',
--     'K-63-09027',
--     'K-63-09451',
--     'K-63-09300',
--     'K-63-09191',
--     'K-63-09338',
--     'K-63-09141',
--     'K-63-09116',
--     'K-63-09145',
--     'K-63-00909', -- RDIO, 5D-punkt ved Radiohuset, Aarhus
--     'K-63-19113',
--     'K-63-05436',
--     '102-08-09067',
--     '102-08-09060',
--     '102-08-00802') -- SKEJ, Permanent station i Aarhus
--     AND
--   pis.infotypeid = (SELECT infotypeid FROM punktinfotype WHERE infotype = 'IDENT:landsnr')
--     AND
--   pis.tekst IN (
--     'K-63-09946', -- G.M.902, Domkirken i Aarhus
--     'K-63-09944',
--     'K-63-09017',
--     'K-63-09933',
--     'K-63-09027',
--     'K-63-09451',
--     'K-63-09300',
--     'K-63-09191',
--     'K-63-09338',
--     'K-63-09141',
--     'K-63-09116',
--     'K-63-09145',
--     'K-63-00909', -- RDIO, 5D-punkt ved Radiohuset, Aarhus
--     'K-63-19113',
--     'K-63-05436',
--     '102-08-09067',
--     '102-08-09060',
--     '102-08-00802') -- SKEJ, Permanent station i Aarhus;
--     AND
--   to_char(o.registreringfra, 'YYYY') = '2019'
-- ;
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),1.01643,255,5,0.00000000057375,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,13527,to_timestamp_tz('2019-02-25 22:06:00','YYYY-MM-DD HH24:MI:SS'),'bfe1d698-09fb-450a-81e7-4e2832b6bea7','87d09ddc-42f3-41cf-a9b1-73f6ece692e6');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),1.79599,250,3,0.0000000005625,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,13528,to_timestamp_tz('2019-02-25 22:29:00','YYYY-MM-DD HH24:MI:SS'),'bfe1d698-09fb-450a-81e7-4e2832b6bea7','fd2627db-144d-4591-8bc7-d4c3afcdb92d');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),2.18838,195,3,0.00000000043875,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,70306,to_timestamp_tz('2019-02-27 16:15:00','YYYY-MM-DD HH24:MI:SS'),'61c61847-ed54-4969-b94e-df74fd63f108','87d09ddc-42f3-41cf-a9b1-73f6ece692e6');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-8.915,603,5,0.00000000135675,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41912,to_timestamp_tz('2019-02-25 21:06:00','YYYY-MM-DD HH24:MI:SS'),'7a45fb99-0772-4be5-9182-d651d429b3b7','4871c57b-d325-45fa-a03a-fdcff49273c0');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),8.1094,431,4,0.00000000096975,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,98588,to_timestamp_tz('2019-02-27 20:14:00','YYYY-MM-DD HH24:MI:SS'),'7a45fb99-0772-4be5-9182-d651d429b3b7','8718db7f-ae22-4cd9-aa56-fc8cea3b8c46');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-20.22509,535,4,0.00000000120375,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,98586,to_timestamp_tz('2019-02-25 21:30:00','YYYY-MM-DD HH24:MI:SS'),'00380e23-ccf7-4655-9e55-8c299c8a0d6f','fd2627db-144d-4591-8bc7-d4c3afcdb92d');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),12.7601,293,3,0.00000000065925,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41913,to_timestamp_tz('2019-02-25 22:53:00','YYYY-MM-DD HH24:MI:SS'),'00380e23-ccf7-4655-9e55-8c299c8a0d6f','4871c57b-d325-45fa-a03a-fdcff49273c0');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-13.19936,446,4,0.0000000010035,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41910,to_timestamp_tz('2019-02-25 20:28:00','YYYY-MM-DD HH24:MI:SS'),'8608b23d-479f-43b9-9e17-2d07041db842','8718db7f-ae22-4cd9-aa56-fc8cea3b8c46');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-1.0162,302,4,0.0000000006795,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,13527,to_timestamp_tz('2019-02-25 22:20:00','YYYY-MM-DD HH24:MI:SS'),'87d09ddc-42f3-41cf-a9b1-73f6ece692e6','bfe1d698-09fb-450a-81e7-4e2832b6bea7');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-1.79608,248,3,0.000000000558,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,13528,to_timestamp_tz('2019-02-25 21:43:00','YYYY-MM-DD HH24:MI:SS'),'fd2627db-144d-4591-8bc7-d4c3afcdb92d','bfe1d698-09fb-450a-81e7-4e2832b6bea7');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-2.73713,28,2,0,0.00000001008,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,14612,to_timestamp_tz('2019-02-26 17:01:00','YYYY-MM-DD HH24:MI:SS'),'67e3987a-dc6b-49ee-8857-417ef35777af','61c61847-ed54-4969-b94e-df74fd63f108');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-2.18808,195,3,0.00000000043875,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,70306,to_timestamp_tz('2019-02-27 16:06:00','YYYY-MM-DD HH24:MI:SS'),'87d09ddc-42f3-41cf-a9b1-73f6ece692e6','61c61847-ed54-4969-b94e-df74fd63f108');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),2.73707,28,2,0,0.00000001008,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,14612,to_timestamp_tz('2019-02-26 16:58:00','YYYY-MM-DD HH24:MI:SS'),'61c61847-ed54-4969-b94e-df74fd63f108','67e3987a-dc6b-49ee-8857-417ef35777af');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),13.19944,504,4,0.000000001134,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41910,to_timestamp_tz('2019-02-25 23:40:00','YYYY-MM-DD HH24:MI:SS'),'8718db7f-ae22-4cd9-aa56-fc8cea3b8c46','8608b23d-479f-43b9-9e17-2d07041db842');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-3.41304,1015,8,0.00000000228375,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41911,to_timestamp_tz('2019-02-27 21:39:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','47285c0d-791d-4ca4-8d4a-e5a0db9f0746');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-8.10913,430,4,0.0000000009675,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,98588,to_timestamp_tz('2019-02-27 20:29:00','YYYY-MM-DD HH24:MI:SS'),'8718db7f-ae22-4cd9-aa56-fc8cea3b8c46','7a45fb99-0772-4be5-9182-d651d429b3b7');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),20.22464,536,4,0.000000001206,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,98586,to_timestamp_tz('2019-02-25 22:45:00','YYYY-MM-DD HH24:MI:SS'),'fd2627db-144d-4591-8bc7-d4c3afcdb92d','00380e23-ccf7-4655-9e55-8c299c8a0d6f');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),8.91522,551,5,0.00000000123975,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41912,to_timestamp_tz('2019-02-25 23:11:00','YYYY-MM-DD HH24:MI:SS'),'4871c57b-d325-45fa-a03a-fdcff49273c0','7a45fb99-0772-4be5-9182-d651d429b3b7');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-12.75941,345,3,0.00000000077625,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41913,to_timestamp_tz('2019-02-25 21:16:00','YYYY-MM-DD HH24:MI:SS'),'4871c57b-d325-45fa-a03a-fdcff49273c0','00380e23-ccf7-4655-9e55-8c299c8a0d6f');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 14:01:00','YYYY-MM-DD HH24:MI:SS'),-0.75299,65,1,0,0.0000000234,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,76348,to_timestamp_tz('2016-03-08 15:27:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','301b8578-8cc8-48a8-8446-541f31482f86');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-18.10154,860,6,0.000000001935,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,84638,to_timestamp_tz('2019-02-27 18:12:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','7ae0fe55-075a-4d21-8de1-4daee63d0de5');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 14:01:00','YYYY-MM-DD HH24:MI:SS'),-0.99594,107,2,0,0.00000003852,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,90341,to_timestamp_tz('2016-03-08 15:42:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','301b8578-8cc8-48a8-8446-541f31482f86');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-18.1019,802,6,0.0000000018045,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,84638,to_timestamp_tz('2019-02-27 17:17:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','7ae0fe55-075a-4d21-8de1-4daee63d0de5');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),0.24352,42,1,0,0.00000001512,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,91840,to_timestamp_tz('2019-02-27 13:25:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 14:01:00','YYYY-MM-DD HH24:MI:SS'),0.24304,42,1,0,0.00000001512,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,7076,to_timestamp_tz('2016-03-08 15:01:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),18.10244,861,6,0.00000000193725,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,84638,to_timestamp_tz('2019-02-27 17:46:00','YYYY-MM-DD HH24:MI:SS'),'7ae0fe55-075a-4d21-8de1-4daee63d0de5','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),18.10169,789,6,0.00000000177525,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,84638,to_timestamp_tz('2019-02-27 18:40:00','YYYY-MM-DD HH24:MI:SS'),'7ae0fe55-075a-4d21-8de1-4daee63d0de5','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-0.16099,48,1,0,0.00000001728,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,7066,to_timestamp_tz('2019-02-28 11:29:00','YYYY-MM-DD HH24:MI:SS'),'fca43e51-5166-44b3-b941-c46915cd791b','7ae0fe55-075a-4d21-8de1-4daee63d0de5');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 14:01:00','YYYY-MM-DD HH24:MI:SS'),0.99616,107,2,0,0.00000003852,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,90341,to_timestamp_tz('2016-03-08 15:35:00','YYYY-MM-DD HH24:MI:SS'),'301b8578-8cc8-48a8-8446-541f31482f86','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 14:01:00','YYYY-MM-DD HH24:MI:SS'),0.75304,65,1,0,0.0000000234,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,76348,to_timestamp_tz('2016-03-08 15:24:00','YYYY-MM-DD HH24:MI:SS'),'301b8578-8cc8-48a8-8446-541f31482f86','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 14:01:00','YYYY-MM-DD HH24:MI:SS'),-0.24303,42,1,0,0.00000001512,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,7076,to_timestamp_tz('2016-03-08 15:03:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),3.41236,1027,8,0.00000000231075,0.00000025,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41911,to_timestamp_tz('2019-02-27 23:48:00','YYYY-MM-DD HH24:MI:SS'),'47285c0d-791d-4ca4-8d4a-e5a0db9f0746','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-0.24356,42,1,0,0.00000001512,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,91840,to_timestamp_tz('2019-02-27 13:29:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:33:00','YYYY-MM-DD HH24:MI:SS'),3.79152,16,1,0,0.000000016,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,63647,to_timestamp_tz('2019-01-30 12:00:00','YYYY-MM-DD HH24:MI:SS'),'fca43e51-5166-44b3-b941-c46915cd791b','8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),0.16114,48,1,0,0.00000001728,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,7066,to_timestamp_tz('2019-02-28 11:27:00','YYYY-MM-DD HH24:MI:SS'),'7ae0fe55-075a-4d21-8de1-4daee63d0de5','fca43e51-5166-44b3-b941-c46915cd791b');
Insert into OBSERVATION (REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values (to_timestamp_tz('2019-12-02 18:33:00','YYYY-MM-DD HH24:MI:SS'),-3.79149,16,1,0,0.000000016,0.0000000001,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,20964,to_timestamp_tz('2019-01-30 12:00:00','YYYY-MM-DD HH24:MI:SS'),'8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c','fca43e51-5166-44b3-b941-c46915cd791b');

COMMIT;

INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagid
) VALUES (
    'sagevent-aaaa-bbbb-0004-000000000002',
    sysdate,
    1, -- koordinater beregnet
    'sag00004-aaaa-bbbb-cccc-000000000001'
);

COMMIT;

INSERT INTO sagseventinfo (
    REGISTRERINGFRA,
    REGISTRERINGTIL,
    BESKRIVELSE,
    SAGSEVENTID
) VALUES (
    sysdate,
    null,
    'Indsættelse af koordinater og beregning',
    'sagevent-aaaa-bbbb-0004-000000000002'
);

COMMIT;

-- SELECT
--   k.registreringfra, 'sagevent-aaaa-bbbb-0004-000000000002' as sagseventfraid,
--   k.sridid, k.x, k.y, k.z, k.sx, k.sy, k.sz, k.t, k.transformeret,
--   k.artskode,  k.punktid
-- FROM
--   koordinat k
-- JOIN punktinfo pi ON k.punktid = pi.punktid
-- WHERE
--   k.sridid IN (SELECT sridid FROM sridtype WHERE srid = 'EPSG:5799')
--     AND
--   pi.infotypeid = (SELECT infotypeid FROM punktinfotype WHERE infotype = 'IDENT:landsnr')
--     AND
--   pi.tekst IN (
--     'K-63-09946', -- G.M.902, Domkirken i Aarhus
--     'K-63-09944',
--     'K-63-09017',
--     'K-63-09933',
--     'K-63-09027',
--     'K-63-09451',
--     'K-63-09300',
--     'K-63-09191',
--     'K-63-09338',
--     'K-63-09141',
--     'K-63-09416',
--     'K-63-09145',
--     'K-63-00909', -- RDIO, 5D-punkt ved Radiohuset, Aarhus
--     'K-63-19113',
--     'K-63-05436',
--     '102-08-09067',
--     '102-08-09060',
--     '102-08-00802' -- SKEJ, Permanent station i Aarhus
-- )
--      AND
--   to_char(k.registreringfra, 'YYYY-MM-DD') = '2019-12-02'
-- ;
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:19','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,26.01127,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'00380e23-ccf7-4655-9e55-8c299c8a0d6f');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:25','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,82.52192,null,null,0,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'47285c0d-791d-4ca4-8d4a-e5a0db9f0746');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:22','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,38.77105,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'4871c57b-d325-45fa-a03a-fdcff49273c0');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:11','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,86.17772,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:18','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,47.68617,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'7a45fb99-0772-4be5-9182-d651d429b3b7');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:14','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,68.07583,null,null,0,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'7ae0fe55-075a-4d21-8de1-4daee63d0de5');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:19','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,68.99483,null,null,0,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'8608b23d-479f-43b9-9e17-2d07041db842');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:22','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,55.79543,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'8718db7f-ae22-4cd9-aa56-fc8cea3b8c46');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:21','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,5.00669,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'87d09ddc-42f3-41cf-a9b1-73f6ece692e6');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:29:02','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,72.0283,null,null,0,to_timestamp_tz('2019-12-02 18:26:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:14','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,85.93462,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:25','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,3.99037,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'bfe1d698-09fb-450a-81e7-4e2832b6bea7');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:14','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,68.23683,null,null,0,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'fca43e51-5166-44b3-b941-c46915cd791b');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:29:02','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,68.23683,null,null,0,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'fca43e51-5166-44b3-b941-c46915cd791b');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:21','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,5.7864,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false',2,'fd2627db-144d-4591-8bc7-d4c3afcdb92d');

-- Opretning beregning
INSERT INTO beregning (registreringfra, sagseventfraid) VALUES (sysdate, 'sagevent-aaaa-bbbb-0004-000000000002');

INSERT INTO beregning_observation (beregningobjectid, observationobjectid)
SELECT (SELECT objectid FROM beregning WHERE sagseventfraid = 'sagevent-aaaa-bbbb-0004-000000000002'), o.objectid
FROM observation o
WHERE o.sagseventfraid = 'sagevent-aaaa-bbbb-0004-000000000001';

INSERT INTO beregning_koordinat (beregningobjectid, koordinatobjectid)
SELECT (SELECT objectid FROM beregning WHERE sagseventfraid = 'sagevent-aaaa-bbbb-0004-000000000002'), k.objectid
FROM koordinat k
WHERE k.sagseventfraid = 'sagevent-aaaa-bbbb-0004-000000000002';


INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagid
) VALUES (
    'false',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Opmålingskampagne 2019',
    'sag00004-aaaa-bbbb-cccc-000000000001'
);


COMMIT;


-------------------------------------------------------------------------------
-- EVENTS OG HISTORIK

-- Nedlæggelse, afregistrering og korrektion af punkter, koordinater,
-- observationer, punktinfo, sagsevents, sagsinfo
-------------------------------------------------------------------------------


INSERT INTO sag (
    id,
    registreringfra
) VALUES (
    'sag00005-aaaa-bbbb-cccc-000000000001',
    sysdate
);

COMMIT;

INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagid
) VALUES (
    'true',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Events og historik',
    'sag00005-aaaa-bbbb-cccc-000000000001'
);

COMMIT;



INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagid
) VALUES (
    'sagevent-aaaa-bbbb-0005-000000000001',
    sysdate,
    2, -- koordinat nedlagt
    'sag00005-aaaa-bbbb-cccc-000000000001'
);

COMMIT;

INSERT INTO sagseventinfo (
    REGISTRERINGFRA,
    REGISTRERINGTIL,
    BESKRIVELSE,
    SAGSEVENTID
) VALUES (
    sysdate,
    null,
    'Afregistrer DVR90 kote for K-63-09446',
    'sagevent-aaaa-bbbb-0005-000000000001'
);

COMMIT;

UPDATE koordinat
SET registreringtil = sysdate, sagseventtilid='sagevent-aaaa-bbbb-0005-000000000001'
WHERE objectid = (
        SELECT k.objectid
        FROM koordinat k
        JOIN punktinfo pi ON k.punktid = pi.punktid
        WHERE pi.tekst = 'K-63-09446'
);


INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagid
) VALUES (
    'sagevent-aaaa-bbbb-0005-000000000002',
    sysdate,
    4, -- observation nedlagt
    'sag00005-aaaa-bbbb-cccc-000000000001'
);

COMMIT;

INSERT INTO sagseventinfo (
    REGISTRERINGFRA,
    REGISTRERINGTIL,
    BESKRIVELSE,
    SAGSEVENTID
) VALUES (
    sysdate,
    null,
    'Afregistrer observation mellem K-63-09446 og K-63-09145',
    'sagevent-aaaa-bbbb-0005-000000000002'
);

COMMIT;

UPDATE observation
SET registreringtil = sysdate, sagseventtilid='sagevent-aaaa-bbbb-0005-000000000002'
WHERE objectid = (
        SELECT o.objectid
        FROM observation o
        JOIN punktinfo pi1 ON o.opstillingspunktid = pi1.punktid
        JOIN punktinfo pi2 ON o.sigtepunktid = pi2.punktid
        WHERE pi1.tekst = 'K-63-09446' AND pi2.tekst='K-63-09145'
 );

COMMIT;

INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagid
) VALUES (
    'sagevent-aaaa-bbbb-0005-000000000003',
    sysdate,
    6, -- punktinformation nedlagt
    'sag00005-aaaa-bbbb-cccc-000000000001'
);

COMMIT;

INSERT INTO sagseventinfo (
    REGISTRERINGFRA,
    REGISTRERINGTIL,
    BESKRIVELSE,
    SAGSEVENTID
) VALUES (
    sysdate,
    null,
    'Fjern ATTR:test fra K-63-09446',
    'sagevent-aaaa-bbbb-0005-000000000003'
);

UPDATE punktinfo
SET
    registreringtil = sysdate,
    sagseventtilid='sagevent-aaaa-bbbb-0005-000000000003'
WHERE objectid = (
        SELECT pi.objectid
        FROM punktinfo pi
        WHERE registreringtil IS NULL
            AND infotypeid = (
                SELECT infotypeid
                FROM punktinfotype
                WHERE infotype='ATTR:test'
        )   AND punktid= (
                SELECT punktid
                FROM punktinfo
                WHERE tekst = 'K-63-09446'
        )
);

COMMIT;

INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagid
) VALUES (
    'sagevent-aaaa-bbbb-0005-000000000004',
    sysdate,
    8, -- punkt+geometri nedlagt
    'sag00005-aaaa-bbbb-cccc-000000000001'
);

COMMIT;

INSERT INTO sagseventinfo (
    REGISTRERINGFRA,
    REGISTRERINGTIL,
    BESKRIVELSE,
    SAGSEVENTID
) VALUES (
    sysdate,
    null,
    'Afregistrer punkt K-63-09446 samt geometri',
    'sagevent-aaaa-bbbb-0005-000000000004'
);

COMMIT;

UPDATE geometriobjekt
SET
    registreringtil = sysdate,
    sagseventtilid='sagevent-aaaa-bbbb-0005-000000000004'
WHERE registreringtil IS NULL AND punktid = (
        SELECT punktid
        FROM punktinfo
        WHERE tekst = 'K-63-09446'
);

UPDATE punkt
SET
    registreringtil = sysdate,
    sagseventtilid='sagevent-aaaa-bbbb-0005-000000000004'
WHERE registreringtil IS NULL AND id = (
        SELECT punktid
        FROM punktinfo
        WHERE tekst = 'K-63-09446'
);

COMMIT;

INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagid
) VALUES (
    'sagevent-aaaa-bbbb-0005-000000000005',
    sysdate,
    9, -- kommentar
    'sag00005-aaaa-bbbb-cccc-000000000001'
);

COMMIT;

INSERT INTO sagseventinfo (
    REGISTRERINGFRA,
    REGISTRERINGTIL,
    BESKRIVELSE,
    SAGSEVENTID
) VALUES (
    sysdate,
    null,
    'Tilføjelse af notat om K-63-09446',
    'sagevent-aaaa-bbbb-0005-000000000005'
);

COMMIT;

INSERT INTO sagseventinfo_materiale (
    sti,
    md5sum,
    sagseventinfoobjectid
) VALUES (
    'materiale/K-63-09446.pdf',
    'af8f278306a057ba41bef6c29911df79',
    (SELECT objectid
     FROM sagseventinfo
     WHERE sagseventid='sagevent-aaaa-bbbb-0005-000000000005'
       AND registreringtil IS NULL)
);

INSERT INTO sagseventinfo_html (
    html,
    sagseventinfoobjectid
) VALUES (
    '<html><body>K-63-09446.pdf</body></html>',
    (SELECT objectid
     FROM sagseventinfo
     WHERE sagseventid='sagevent-aaaa-bbbb-0005-000000000005'
       AND registreringtil IS NULL)
);

COMMIT;


