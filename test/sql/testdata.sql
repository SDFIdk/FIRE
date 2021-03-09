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
    dir_skitser
) VALUES (
    'F:\GDB\FIRE\skitser'
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
INSERT INTO punktinfotype (infotypeid, infotype, anvendelse, beskrivelse) VALUES (360, 'ATTR:beskrivelse', 'TEKST', 'Tekstbeskrivelse af punktet');
INSERT INTO punktinfotype (infotypeid, infotype, anvendelse, beskrivelse) VALUES (362, 'AFM:højde_over_terræn', 'TAL', 'Fikspunkts højde over terræn');
INSERT INTO punktinfotype (infotypeid, infotype, anvendelse, beskrivelse) VALUES (363, 'AFM:4999', 'FLAG', 'Ukendt fikspunktstype');
INSERT INTO punktinfotype (infotypeid, infotype, anvendelse, beskrivelse) VALUES (364, 'AFM:2700', 'FLAG', 'Bolt');
INSERT INTO punktinfotype (infotypeid, infotype, anvendelse, beskrivelse) VALUES (365, 'AFM:2701', 'FLAG', 'Lodret bolt');
INSERT INTO punktinfotype (infotypeid, infotype, anvendelse, beskrivelse) VALUES (366, 'AFM:2950', 'FLAG', 'Skruepløk');
INSERT INTO punktinfotype (infotypeid, infotype, anvendelse, beskrivelse) VALUES (367, 'AFM:5998', 'FLAG', 'Ingen');
INSERT INTO punktinfotype (infotypeid, infotype, anvendelse, beskrivelse) VALUES (370, 'ATTR:muligt_datumstabil', 'FLAG', 'Markering af om punkt potentielt er datumstabilt');
INSERT INTO punktinfotype (infotypeid, infotype, anvendelse, beskrivelse) VALUES (371, 'REGION:DK', 'FLAG', 'Punkter i Danmark');

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

INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagsid
) VALUES (
    'true',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Indsættelse punkter mellem Aarhus Domkirke og GNSS station SKEJ via 5D-punkt RDIO',
    'sag00001-aaaa-bbbb-cccc-000000000001'
);

INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagsid
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
    sagsid
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
    sagsid
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

-- SELECT
--   k.registreringfra, 'sagevent-aaaa-bbbb-0001-000000000003' as sagseventfraid,
--   k.sridid, k.x, k.y, k.z, k.sx, k.sy, k.sz, k.t, k.transformeret,
--   k.fejlmeldt, k.artskode,  k.punktid
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
--     'K-63-00909' -- RDIO, 5D-punkt ved Radiohuset, Aarhus
-- ) AND k.registreringtil IS NULL;

Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2009-10-20 12:11:07','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0001-000000000003',8,null,null,2.8318,null,null,0,to_timestamp_tz('2000-02-11 13:30:00','YYYY-MM-DD HH24:MI:SS'),'false','false',1,'61c61847-ed54-4969-b94e-df74fd63f108');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2001-07-31 12:32:02','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0001-000000000003',8,null,null,5.5700000000000003,null,null,0,to_timestamp_tz('2001-07-31 08:54:00','YYYY-MM-DD HH24:MI:SS'),'false','false',1,'67e3987a-dc6b-49ee-8857-417ef35777af');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2003-11-07 10:53:02','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0001-000000000003',8,null,null,85.181,null,null,0,to_timestamp_tz('2001-02-28 12:45:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'301b8578-8cc8-48a8-8446-541f31482f86');

COMMIT;

INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagsid
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

INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagsid
) VALUES (
    'true',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Opmålingskampagne 2015',
    'sag00002-aaaa-bbbb-cccc-000000000001'
);


INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagsid
) VALUES (
    'sagevent-aaaa-bbbb-0002-000000000001',
    sysdate,
    3, -- indsættelse af observationer
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
    'Indsættelse af observationer',
    'sagevent-aaaa-bbbb-0002-000000000001'
);

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

Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('b11c101-2ba8-4aeb-a776-953cdc0e3ae2',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),1.01596,230,4,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,42861,to_timestamp_tz('2015-11-11 11:27:00','YYYY-MM-DD HH24:MI:SS'),'bfe1d698-09fb-450a-81e7-4e2832b6bea7','87d09ddc-42f3-41cf-a9b1-73f6ece692e6');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('a10e0400-c573-4251-9dd1-8b29bd9cc147',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),2.18702,182,2,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85401,to_timestamp_tz('2015-11-11 10:05:00','YYYY-MM-DD HH24:MI:SS'),'61c61847-ed54-4969-b94e-df74fd63f108','87d09ddc-42f3-41cf-a9b1-73f6ece692e6');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('55b499b1-e1c2-4b69-a7d1-c8844cd645a6',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),1.79568,205,3,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,42868,to_timestamp_tz('2015-11-11 11:40:00','YYYY-MM-DD HH24:MI:SS'),'bfe1d698-09fb-450a-81e7-4e2832b6bea7','fd2627db-144d-4591-8bc7-d4c3afcdb92d');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('7bcaf5d2-6a8e-458d-94db-e1273f9af83e',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-20.22457,540,12,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85404,to_timestamp_tz('2015-11-12 14:45:00','YYYY-MM-DD HH24:MI:SS'),'00380e23-ccf7-4655-9e55-8c299c8a0d6f','fd2627db-144d-4591-8bc7-d4c3afcdb92d');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('6314291f-32b9-469a-91b9-f291a1827ce6',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),12.75784,281,7,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,14536,to_timestamp_tz('2015-11-11 12:25:00','YYYY-MM-DD HH24:MI:SS'),'00380e23-ccf7-4655-9e55-8c299c8a0d6f','4871c57b-d325-45fa-a03a-fdcff49273c0');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('7ba0c3f8-283e-4e54-b639-fcc6202d82cb',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-8.91615,579,9,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85423,to_timestamp_tz('2015-11-12 13:46:00','YYYY-MM-DD HH24:MI:SS'),'7a45fb99-0772-4be5-9182-d651d429b3b7','4871c57b-d325-45fa-a03a-fdcff49273c0');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('1a8d206b-045d-412f-bc82-0e47f7f2e75e',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-13.1971,522,8,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85414,to_timestamp_tz('2015-11-12 12:53:00','YYYY-MM-DD HH24:MI:SS'),'8608b23d-479f-43b9-9e17-2d07041db842','8718db7f-ae22-4cd9-aa56-fc8cea3b8c46');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('f0764685-a39d-4508-b7d6-e5edf770affb',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),8.11043,441,7,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,14513,to_timestamp_tz('2015-11-11 13:12:00','YYYY-MM-DD HH24:MI:SS'),'7a45fb99-0772-4be5-9182-d651d429b3b7','8718db7f-ae22-4cd9-aa56-fc8cea3b8c46');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('e6161b52-36dd-4522-a871-e2376bb06447',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-1.01612,229,4,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,42861,to_timestamp_tz('2015-11-11 11:19:00','YYYY-MM-DD HH24:MI:SS'),'87d09ddc-42f3-41cf-a9b1-73f6ece692e6','bfe1d698-09fb-450a-81e7-4e2832b6bea7');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('36004090-3cf4-4c26-9ea4-83b8416cf264',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-1.79588,243,3,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,42868,to_timestamp_tz('2015-11-12 14:55:00','YYYY-MM-DD HH24:MI:SS'),'fd2627db-144d-4591-8bc7-d4c3afcdb92d','bfe1d698-09fb-450a-81e7-4e2832b6bea7');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('a5802a63-0bce-41e0-9a31-e7af4af96798',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-2.73684,27,2,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,57168,to_timestamp_tz('2015-11-24 15:30:00','YYYY-MM-DD HH24:MI:SS'),'67e3987a-dc6b-49ee-8857-417ef35777af','61c61847-ed54-4969-b94e-df74fd63f108');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('ec05cbc4-0b54-4d90-afe2-8585286bd931',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-2.18711,182,2,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85401,to_timestamp_tz('2015-11-11 10:12:00','YYYY-MM-DD HH24:MI:SS'),'87d09ddc-42f3-41cf-a9b1-73f6ece692e6','61c61847-ed54-4969-b94e-df74fd63f108');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('4031a2e1-5ae7-4fbb-9ebe-0f8d78802c5b',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),2.73689,27,2,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,57168,to_timestamp_tz('2015-11-24 15:26:00','YYYY-MM-DD HH24:MI:SS'),'61c61847-ed54-4969-b94e-df74fd63f108','67e3987a-dc6b-49ee-8857-417ef35777af');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('58341f16-2226-440d-ad9d-6e5c5ad51045',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-5.62311,325,5,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,99524,to_timestamp_tz('2015-11-12 12:36:00','YYYY-MM-DD HH24:MI:SS'),'d9cb77ab-2825-4f32-bb65-239aab7bfa67','8608b23d-479f-43b9-9e17-2d07041db842');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('fa574da5-bb30-4fba-afbd-507b721c3586',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),13.19823,481,7,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85414,to_timestamp_tz('2015-11-11 13:31:00','YYYY-MM-DD HH24:MI:SS'),'8718db7f-ae22-4cd9-aa56-fc8cea3b8c46','8608b23d-479f-43b9-9e17-2d07041db842');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('bcdb1a07-39a0-4911-ae6b-9b7138f4219f',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),7.90343,680,8,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,28723,to_timestamp_tz('2015-11-11 14:13:00','YYYY-MM-DD HH24:MI:SS'),'d9cb77ab-2825-4f32-bb65-239aab7bfa67','47285c0d-791d-4ca4-8d4a-e5a0db9f0746');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('df43666e-625e-4f23-9318-359a01b58883',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-2.65984,839,10,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,71352,to_timestamp_tz('2015-11-11 16:11:00','YYYY-MM-DD HH24:MI:SS'),'301b8578-8cc8-48a8-8446-541f31482f86','47285c0d-791d-4ca4-8d4a-e5a0db9f0746');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('4ec9611f-9a27-4790-8c83-02a7be26d8e6',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),8.91614,500,8,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85423,to_timestamp_tz('2015-11-11 12:48:00','YYYY-MM-DD HH24:MI:SS'),'4871c57b-d325-45fa-a03a-fdcff49273c0','7a45fb99-0772-4be5-9182-d651d429b3b7');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('b4f1f0fb-d191-44f0-9fc5-9e9b0fa8e109',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-8.11047,435,6,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,14513,to_timestamp_tz('2015-11-12 13:19:00','YYYY-MM-DD HH24:MI:SS'),'8718db7f-ae22-4cd9-aa56-fc8cea3b8c46','7a45fb99-0772-4be5-9182-d651d429b3b7');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('cb32e02b-8ecd-448d-9f95-d49b48a0402f',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),5.62317,293,4,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,99524,to_timestamp_tz('2015-11-11 13:43:00','YYYY-MM-DD HH24:MI:SS'),'8608b23d-479f-43b9-9e17-2d07041db842','d9cb77ab-2825-4f32-bb65-239aab7bfa67');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('0944be81-36d0-4885-8aef-88104a1ddb5b',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-7.90367,587,8,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,28723,to_timestamp_tz('2015-11-12 12:23:00','YYYY-MM-DD HH24:MI:SS'),'47285c0d-791d-4ca4-8d4a-e5a0db9f0746','d9cb77ab-2825-4f32-bb65-239aab7bfa67');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('ab6428d1-3719-411c-8028-7edcd8e00a38',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-12.75732,335,7,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,14536,to_timestamp_tz('2015-11-12 14:09:00','YYYY-MM-DD HH24:MI:SS'),'4871c57b-d325-45fa-a03a-fdcff49273c0','00380e23-ccf7-4655-9e55-8c299c8a0d6f');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('3770aa08-b7b2-4e67-a2cf-e97f4720d7c8',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),20.22451,505,10,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,85404,to_timestamp_tz('2015-11-11 12:10:00','YYYY-MM-DD HH24:MI:SS'),'fd2627db-144d-4591-8bc7-d4c3afcdb92d','00380e23-ccf7-4655-9e55-8c299c8a0d6f');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('94d4eaad-b381-49c5-a062-31285b357de3',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),2.66051,899,11,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,71352,to_timestamp_tz('2015-11-11 15:25:00','YYYY-MM-DD HH24:MI:SS'),'47285c0d-791d-4ca4-8d4a-e5a0db9f0746','301b8578-8cc8-48a8-8446-541f31482f86');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('4b4d4ac0-f8bb-417f-85db-36aa8373c46e',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-0.75308,69,1,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,5671,to_timestamp_tz('2015-11-24 13:30:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','301b8578-8cc8-48a8-8446-541f31482f86');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('56532800-ef8a-423a-bf5e-58421b9c0e2d',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-0.75308,68,1,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,5671,to_timestamp_tz('2015-11-24 13:35:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','301b8578-8cc8-48a8-8446-541f31482f86');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('2304234b-992c-4b89-8492-d30a933f78aa',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),0.2431,31,1,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,106103,to_timestamp_tz('2015-11-24 13:09:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('c7c8ac0c-b57f-42e4-aaf6-7a56c632cf32',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),0.24311,30,1,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,106103,to_timestamp_tz('2015-11-25 11:19:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('c54370e9-bffd-48af-a10d-67608f5a10ac',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),0.75314,69,1,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,5671,to_timestamp_tz('2015-11-24 13:27:00','YYYY-MM-DD HH24:MI:SS'),'301b8578-8cc8-48a8-8446-541f31482f86','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('c261e415-d52f-4cd4-ae36-88832ed0848a',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),0.753,68,1,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,5671,to_timestamp_tz('2015-11-24 13:33:00','YYYY-MM-DD HH24:MI:SS'),'301b8578-8cc8-48a8-8446-541f31482f86','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('d7d81b13-cdae-4d47-b285-ecbf1fac65ce',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-0.24307,31,1,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,106103,to_timestamp_tz('2015-11-24 13:11:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('ef245d7b-e37a-4f27-bb9d-d9971b6e4dfa',to_timestamp_tz('2016-01-25 13:51:00','YYYY-MM-DD HH24:MI:SS'),-0.24308,30,1,0,1.0,0.01,0,'sagevent-aaaa-bbbb-0002-000000000001',1,1,106103,to_timestamp_tz('2015-11-25 11:21:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','b54a5515-d050-4049-bcb8-93a5e1039cc3');

COMMIT;


INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagsid
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

-- SELECT
--   k.registreringfra, 'sagevent-aaaa-bbbb-0002-000000000002' as sagseventfraid,
--   k.sridid, k.x, k.y, k.z, k.sx, k.sy, k.sz, k.t, k.transformeret,
--   k.fejlmeldt, k.artskode,  k.punktid
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
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:02','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,26.01279,null,null,1,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'00380e23-ccf7-4655-9e55-8c299c8a0d6f');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:08','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,82.52137,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'47285c0d-791d-4ca4-8d4a-e5a0db9f0746');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:05','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,38.77039,null,null,1,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'4871c57b-d325-45fa-a03a-fdcff49273c0');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:38:58','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,86.17772,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:01','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,47.68654,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'7a45fb99-0772-4be5-9182-d651d429b3b7');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:03','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,68.99467,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'8608b23d-479f-43b9-9e17-2d07041db842');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:05','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,55.79699,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'8718db7f-ae22-4cd9-aa56-fc8cea3b8c46');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:04','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,5.00852,null,null,1,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'87d09ddc-42f3-41cf-a9b1-73f6ece692e6');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:38:58','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,85.93462,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:07','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,3.99248,null,null,1,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'bfe1d698-09fb-450a-81e7-4e2832b6bea7');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:04','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,74.61782,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'d9cb77ab-2825-4f32-bb65-239aab7bfa67');
Insert into koordinat (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2016-01-25 13:39:05','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0002-000000000002',8,null,null,5.78825,null,null,1,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'fd2627db-144d-4591-8bc7-d4c3afcdb92d');

-- Opretning beregning
INSERT INTO beregning (registreringfra, sagseventfraid) VALUES (sysdate, 'sagevent-aaaa-bbbb-0002-000000000002');

INSERT INTO beregning_observation (beregningobjektid, observationobjektid)
SELECT (SELECT objektid FROM beregning WHERE sagseventfraid = 'sagevent-aaaa-bbbb-0002-000000000002'), o.objektid
FROM observation o
WHERE o.sagseventfraid = 'sagevent-aaaa-bbbb-0002-000000000001';

INSERT INTO beregning_koordinat (beregningobjektid, koordinatobjektid)
SELECT (SELECT objektid FROM beregning WHERE sagseventfraid = 'sagevent-aaaa-bbbb-0002-000000000002'), k.objektid
FROM koordinat k
WHERE k.sagseventfraid = 'sagevent-aaaa-bbbb-0002-000000000002';

COMMIT;

INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagsid
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


INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagsid
) VALUES (
    'true',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Punkt K-63-09446 tabtgået',
    'sag00003-aaaa-bbbb-cccc-000000000001'
);


INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagsid
) VALUES (
    'sagevent-aaaa-bbbb-0003-000000000001',
    sysdate,
    5, -- punktinfo tilføjet
    'sag00003-aaaa-bbbb-cccc-000000000001'
);


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
    sagsid
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


INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagsid
) VALUES (
    'true',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Opmålingskampagne 2019',
    'sag00004-aaaa-bbbb-cccc-000000000001'
);


INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagsid
) VALUES (
    'sagevent-aaaa-bbbb-0004-000000000001',
    sysdate,
    3, -- observationer indsat
    'sag00004-aaaa-bbbb-cccc-000000000001'
);


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
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('a5fa57e1-75b9-49c7-b672-f43e7375bd2d',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),1.01643,255,5,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,13527,to_timestamp_tz('2019-02-25 22:06:00','YYYY-MM-DD HH24:MI:SS'),'bfe1d698-09fb-450a-81e7-4e2832b6bea7','87d09ddc-42f3-41cf-a9b1-73f6ece692e6');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('40237d35-5284-454d-bae0-b7b851a86153',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),1.79599,250,3,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,13528,to_timestamp_tz('2019-02-25 22:29:00','YYYY-MM-DD HH24:MI:SS'),'bfe1d698-09fb-450a-81e7-4e2832b6bea7','fd2627db-144d-4591-8bc7-d4c3afcdb92d');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('a7a6534a-500b-42eb-889e-2ffd97916671',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),2.18838,195,3,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,70306,to_timestamp_tz('2019-02-27 16:15:00','YYYY-MM-DD HH24:MI:SS'),'61c61847-ed54-4969-b94e-df74fd63f108','87d09ddc-42f3-41cf-a9b1-73f6ece692e6');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('60f7e3eb-a1a6-4d0f-ab04-0023f49798f7',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-8.915,603,5,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41912,to_timestamp_tz('2019-02-25 21:06:00','YYYY-MM-DD HH24:MI:SS'),'7a45fb99-0772-4be5-9182-d651d429b3b7','4871c57b-d325-45fa-a03a-fdcff49273c0');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('2b9a81c0-a23b-4d6c-824e-54a376170a30',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),8.1094,431,4,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,98588,to_timestamp_tz('2019-02-27 20:14:00','YYYY-MM-DD HH24:MI:SS'),'7a45fb99-0772-4be5-9182-d651d429b3b7','8718db7f-ae22-4cd9-aa56-fc8cea3b8c46');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('b3daf20d-f4d8-4b4f-b4d0-4db94c3d6289',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-20.22509,535,4,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,98586,to_timestamp_tz('2019-02-25 21:30:00','YYYY-MM-DD HH24:MI:SS'),'00380e23-ccf7-4655-9e55-8c299c8a0d6f','fd2627db-144d-4591-8bc7-d4c3afcdb92d');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('b2a04b98-5ae7-456b-94e4-a56153f2bd3b',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),12.7601,293,3,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41913,to_timestamp_tz('2019-02-25 22:53:00','YYYY-MM-DD HH24:MI:SS'),'00380e23-ccf7-4655-9e55-8c299c8a0d6f','4871c57b-d325-45fa-a03a-fdcff49273c0');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('daa17576-463e-4cc1-949a-35e334473cc9',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-13.19936,446,4,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41910,to_timestamp_tz('2019-02-25 20:28:00','YYYY-MM-DD HH24:MI:SS'),'8608b23d-479f-43b9-9e17-2d07041db842','8718db7f-ae22-4cd9-aa56-fc8cea3b8c46');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('886e32dd-8b4d-41b6-9af7-b56c3126c8b0',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-1.0162,302,4,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,13527,to_timestamp_tz('2019-02-25 22:20:00','YYYY-MM-DD HH24:MI:SS'),'87d09ddc-42f3-41cf-a9b1-73f6ece692e6','bfe1d698-09fb-450a-81e7-4e2832b6bea7');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('3b50bfcf-93e0-4dc2-95b5-d59087e366f4',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-1.79608,248,3,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,13528,to_timestamp_tz('2019-02-25 21:43:00','YYYY-MM-DD HH24:MI:SS'),'fd2627db-144d-4591-8bc7-d4c3afcdb92d','bfe1d698-09fb-450a-81e7-4e2832b6bea7');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('371cac6f-ca12-456b-ab75-c287a2669af1',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-2.73713,28,2,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,14612,to_timestamp_tz('2019-02-26 17:01:00','YYYY-MM-DD HH24:MI:SS'),'67e3987a-dc6b-49ee-8857-417ef35777af','61c61847-ed54-4969-b94e-df74fd63f108');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('bdc13223-789f-48c1-8ce2-4cfbc19444c0',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-2.18808,195,3,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,70306,to_timestamp_tz('2019-02-27 16:06:00','YYYY-MM-DD HH24:MI:SS'),'87d09ddc-42f3-41cf-a9b1-73f6ece692e6','61c61847-ed54-4969-b94e-df74fd63f108');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('ece8041c-a6ab-4a6a-98c6-4c0d490c3220',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),2.73707,28,2,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,14612,to_timestamp_tz('2019-02-26 16:58:00','YYYY-MM-DD HH24:MI:SS'),'61c61847-ed54-4969-b94e-df74fd63f108','67e3987a-dc6b-49ee-8857-417ef35777af');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('b5b90547-fb36-4b83-9734-74d3934f0080',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),13.19944,504,4,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41910,to_timestamp_tz('2019-02-25 23:40:00','YYYY-MM-DD HH24:MI:SS'),'8718db7f-ae22-4cd9-aa56-fc8cea3b8c46','8608b23d-479f-43b9-9e17-2d07041db842');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('f413b018-55bf-4ca8-8c56-d31130e8e7e6',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-3.41304,1015,8,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41911,to_timestamp_tz('2019-02-27 21:39:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','47285c0d-791d-4ca4-8d4a-e5a0db9f0746');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('56a6ad80-66ef-484e-a4f8-8ec3079a8269',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-8.10913,430,4,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,98588,to_timestamp_tz('2019-02-27 20:29:00','YYYY-MM-DD HH24:MI:SS'),'8718db7f-ae22-4cd9-aa56-fc8cea3b8c46','7a45fb99-0772-4be5-9182-d651d429b3b7');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('0e4837c5-0413-4aae-b4b2-89094fc514b9',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),20.22464,536,4,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,98586,to_timestamp_tz('2019-02-25 22:45:00','YYYY-MM-DD HH24:MI:SS'),'fd2627db-144d-4591-8bc7-d4c3afcdb92d','00380e23-ccf7-4655-9e55-8c299c8a0d6f');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('1e12debb-c179-4ceb-b0e4-3c7b7627c6e3',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),8.91522,551,5,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41912,to_timestamp_tz('2019-02-25 23:11:00','YYYY-MM-DD HH24:MI:SS'),'4871c57b-d325-45fa-a03a-fdcff49273c0','7a45fb99-0772-4be5-9182-d651d429b3b7');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('56c67a3d-0158-47ab-8736-3dc51b55faaf',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-12.75941,345,3,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41913,to_timestamp_tz('2019-02-25 21:16:00','YYYY-MM-DD HH24:MI:SS'),'4871c57b-d325-45fa-a03a-fdcff49273c0','00380e23-ccf7-4655-9e55-8c299c8a0d6f');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('da6da9cc-b17a-4787-a474-494eb5072e8a',to_timestamp_tz('2019-12-02 14:01:00','YYYY-MM-DD HH24:MI:SS'),-0.75299,65,1,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,76348,to_timestamp_tz('2016-03-08 15:27:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','301b8578-8cc8-48a8-8446-541f31482f86');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('66643bde-fdd2-4494-be31-27380fb4fbff',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-18.10154,860,6,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,84638,to_timestamp_tz('2019-02-27 18:12:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','7ae0fe55-075a-4d21-8de1-4daee63d0de5');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('f3a1664c-c963-41e5-9161-21f2b628ce2b',to_timestamp_tz('2019-12-02 14:01:00','YYYY-MM-DD HH24:MI:SS'),-0.99594,107,2,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,90341,to_timestamp_tz('2016-03-08 15:42:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','301b8578-8cc8-48a8-8446-541f31482f86');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('efff15ef-9a03-41bd-ab96-9c94b13feda2',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-18.1019,802,6,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,84638,to_timestamp_tz('2019-02-27 17:17:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','7ae0fe55-075a-4d21-8de1-4daee63d0de5');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('7839258e-640a-4279-85aa-0f58dd022bae',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),0.24352,42,1,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,91840,to_timestamp_tz('2019-02-27 13:25:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('872dc7e7-4fb7-46fa-9565-15b85a952828',to_timestamp_tz('2019-12-02 14:01:00','YYYY-MM-DD HH24:MI:SS'),0.24304,42,1,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,7076,to_timestamp_tz('2016-03-08 15:01:00','YYYY-MM-DD HH24:MI:SS'),'b54a5515-d050-4049-bcb8-93a5e1039cc3','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('3c2d8c38-ebb0-4c82-a46e-c7d723ab4430',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),18.10244,861,6,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,84638,to_timestamp_tz('2019-02-27 17:46:00','YYYY-MM-DD HH24:MI:SS'),'7ae0fe55-075a-4d21-8de1-4daee63d0de5','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('ca5dc4e0-10e9-4732-972a-0ae1355453de',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),18.10169,789,6,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,84638,to_timestamp_tz('2019-02-27 18:40:00','YYYY-MM-DD HH24:MI:SS'),'7ae0fe55-075a-4d21-8de1-4daee63d0de5','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('8f9966b0-8741-4fc2-8922-f00507de4d73',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-0.16099,48,1,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,7066,to_timestamp_tz('2019-02-28 11:29:00','YYYY-MM-DD HH24:MI:SS'),'fca43e51-5166-44b3-b941-c46915cd791b','7ae0fe55-075a-4d21-8de1-4daee63d0de5');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('f41b464c-c0e4-4748-b519-f9faa0192da4',to_timestamp_tz('2019-12-02 14:01:00','YYYY-MM-DD HH24:MI:SS'),0.99616,107,2,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,90341,to_timestamp_tz('2016-03-08 15:35:00','YYYY-MM-DD HH24:MI:SS'),'301b8578-8cc8-48a8-8446-541f31482f86','4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('43479bad-ecbb-4ab9-8d37-7069bae6c6a6',to_timestamp_tz('2019-12-02 14:01:00','YYYY-MM-DD HH24:MI:SS'),0.75304,65,1,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,76348,to_timestamp_tz('2016-03-08 15:24:00','YYYY-MM-DD HH24:MI:SS'),'301b8578-8cc8-48a8-8446-541f31482f86','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('dff25c52-9d0a-451e-84b7-e7970660ba44',to_timestamp_tz('2019-12-02 14:01:00','YYYY-MM-DD HH24:MI:SS'),-0.24303,42,1,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,7076,to_timestamp_tz('2016-03-08 15:03:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('1370b813-0056-4781-98e4-63934f3be0bf',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),3.41236,1027,8,0.05,0.5,null,null,'sagevent-aaaa-bbbb-0004-000000000001',2,1,41911,to_timestamp_tz('2019-02-27 23:48:00','YYYY-MM-DD HH24:MI:SS'),'47285c0d-791d-4ca4-8d4a-e5a0db9f0746','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('0c060dca-c969-42be-a68b-69b82beb9792',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),-0.24356,42,1,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,91840,to_timestamp_tz('2019-02-27 13:29:00','YYYY-MM-DD HH24:MI:SS'),'4b4c5c17-32e8-495d-a598-cdf42e0892de','b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('e28827e0-1db9-416a-9c46-21f3669dc64d',to_timestamp_tz('2019-12-02 18:33:00','YYYY-MM-DD HH24:MI:SS'),3.79152,16,1,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,63647,to_timestamp_tz('2019-01-30 12:00:00','YYYY-MM-DD HH24:MI:SS'),'fca43e51-5166-44b3-b941-c46915cd791b','8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('4a65eeef-39c6-4a16-b446-2b8fa4f9111e',to_timestamp_tz('2019-12-02 18:17:00','YYYY-MM-DD HH24:MI:SS'),0.16114,48,1,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,7066,to_timestamp_tz('2019-02-28 11:27:00','YYYY-MM-DD HH24:MI:SS'),'7ae0fe55-075a-4d21-8de1-4daee63d0de5','fca43e51-5166-44b3-b941-c46915cd791b');
Insert into OBSERVATION (id,REGISTRERINGFRA,VALUE1,VALUE2,VALUE3,VALUE4,VALUE5,VALUE6,VALUE7,SAGSEVENTFRAID,OBSERVATIONSTYPEID,ANTAL,GRUPPE,OBSERVATIONSTIDSPUNKT,OPSTILLINGSPUNKTID,SIGTEPUNKTID) values ('7725a94a-809c-4d43-934d-44b4ac2784aa',to_timestamp_tz('2019-12-02 18:33:00','YYYY-MM-DD HH24:MI:SS'),-3.79149,16,1,0,0.05,0.5,0,'sagevent-aaaa-bbbb-0004-000000000001',1,1,20964,to_timestamp_tz('2019-01-30 12:00:00','YYYY-MM-DD HH24:MI:SS'),'8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c','fca43e51-5166-44b3-b941-c46915cd791b');

COMMIT;

INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagsid
) VALUES (
    'sagevent-aaaa-bbbb-0004-000000000002',
    sysdate,
    1, -- koordinater beregnet
    'sag00004-aaaa-bbbb-cccc-000000000001'
);


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

-- SELECT
--   k.registreringfra, 'sagevent-aaaa-bbbb-0004-000000000002' as sagseventfraid,
--   k.sridid, k.x, k.y, k.z, k.sx, k.sy, k.sz, k.t, k.transformeret,
--   k.fejlmeldt, k.artskode,  k.punktid
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
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:19','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,26.01127,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'00380e23-ccf7-4655-9e55-8c299c8a0d6f');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:25','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,82.52192,null,null,0,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'47285c0d-791d-4ca4-8d4a-e5a0db9f0746');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:22','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,38.77105,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'4871c57b-d325-45fa-a03a-fdcff49273c0');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:11','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,86.17772,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'4b4c5c17-32e8-495d-a598-cdf42e0892de');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:18','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,47.68617,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'7a45fb99-0772-4be5-9182-d651d429b3b7');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:14','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,68.07583,null,null,0,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'7ae0fe55-075a-4d21-8de1-4daee63d0de5');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:19','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,68.99483,null,null,0,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'8608b23d-479f-43b9-9e17-2d07041db842');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:22','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,55.79543,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'8718db7f-ae22-4cd9-aa56-fc8cea3b8c46');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:21','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,5.00669,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'87d09ddc-42f3-41cf-a9b1-73f6ece692e6');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:29:02','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,72.0283,null,null,0,to_timestamp_tz('2019-12-02 18:26:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'8e5e57f8-d3c4-45f2-a2a9-492f52d7df1c');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:14','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,85.93462,null,null,0,to_timestamp_tz('2016-01-05 15:53:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'b54a5515-d050-4049-bcb8-93a5e1039cc3');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:25','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,3.99037,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'bfe1d698-09fb-450a-81e7-4e2832b6bea7');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:14','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,68.23683,null,null,0,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'fca43e51-5166-44b3-b941-c46915cd791b');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:29:02','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,68.23683,null,null,0,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'fca43e51-5166-44b3-b941-c46915cd791b');
Insert into KOORDINAT (REGISTRERINGFRA,SAGSEVENTFRAID,SRIDID,X,Y,Z,SX,SY,SZ,T,TRANSFORMERET,FEJLMELDT,ARTSKODE,PUNKTID) values (to_timestamp_tz('2019-12-02 18:17:21','YYYY-MM-DD HH24:MI:SS'),'sagevent-aaaa-bbbb-0004-000000000002',8,null,null,5.7864,null,null,1,to_timestamp_tz('2019-12-02 16:13:00','YYYY-MM-DD HH24:MI:SS'),'false','false',2,'fd2627db-144d-4591-8bc7-d4c3afcdb92d');

-- Opretning beregning
INSERT INTO beregning (registreringfra, sagseventfraid) VALUES (sysdate, 'sagevent-aaaa-bbbb-0004-000000000002');

INSERT INTO beregning_observation (beregningobjektid, observationobjektid)
SELECT (SELECT objektid FROM beregning WHERE sagseventfraid = 'sagevent-aaaa-bbbb-0004-000000000002'), o.objektid
FROM observation o
WHERE o.sagseventfraid = 'sagevent-aaaa-bbbb-0004-000000000001';

INSERT INTO beregning_koordinat (beregningobjektid, koordinatobjektid)
SELECT (SELECT objektid FROM beregning WHERE sagseventfraid = 'sagevent-aaaa-bbbb-0004-000000000002'), k.objektid
FROM koordinat k
WHERE k.sagseventfraid = 'sagevent-aaaa-bbbb-0004-000000000002';


INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagsid
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


INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagsid
) VALUES (
    'true',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Events og historik',
    'sag00005-aaaa-bbbb-cccc-000000000001'
);


INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagsid
) VALUES (
    'sagevent-aaaa-bbbb-0005-000000000001',
    sysdate,
    2, -- koordinat nedlagt
    'sag00005-aaaa-bbbb-cccc-000000000001'
);

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

UPDATE koordinat
SET registreringtil = sysdate, sagseventtilid='sagevent-aaaa-bbbb-0005-000000000001'
WHERE objektid = (
        SELECT k.objektid
        FROM koordinat k
        JOIN punktinfo pi ON k.punktid = pi.punktid
        WHERE pi.tekst = 'K-63-09446'
);


INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagsid
) VALUES (
    'sagevent-aaaa-bbbb-0005-000000000002',
    sysdate,
    4, -- observation nedlagt
    'sag00005-aaaa-bbbb-cccc-000000000001'
);


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


UPDATE observation
SET registreringtil = sysdate, sagseventtilid='sagevent-aaaa-bbbb-0005-000000000002'
WHERE objektid = (
        SELECT o.objektid
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
    sagsid
) VALUES (
    'sagevent-aaaa-bbbb-0005-000000000003',
    sysdate,
    6, -- punktinformation nedlagt
    'sag00005-aaaa-bbbb-cccc-000000000001'
);


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
WHERE objektid = (
        SELECT pi.objektid
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
    sagsid
) VALUES (
    'sagevent-aaaa-bbbb-0005-000000000004',
    sysdate,
    8, -- punkt+geometri nedlagt
    'sag00005-aaaa-bbbb-cccc-000000000001'
);

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
    sagsid
) VALUES (
    'sagevent-aaaa-bbbb-0005-000000000005',
    sysdate,
    9, -- kommentar
    'sag00005-aaaa-bbbb-cccc-000000000001'
);

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

INSERT INTO sagseventinfo_materiale (
    materiale,
    sagseventinfoobjektid
) VALUES (
    TO_BLOB('f1cba4f8bc04d5c4809b1daccb63bd7b'),
    (SELECT objektid
     FROM sagseventinfo
     WHERE sagseventid='sagevent-aaaa-bbbb-0005-000000000005'
       AND registreringtil IS NULL)
);

INSERT INTO sagseventinfo_html (
    html,
    sagseventinfoobjektid
) VALUES (
    '<html><body>K-63-09446.pdf</body></html>',
    (SELECT objektid
     FROM sagseventinfo
     WHERE sagseventid='sagevent-aaaa-bbbb-0005-000000000005'
       AND registreringtil IS NULL)
);

COMMIT;


-------------------------------------------------------------------------------
-- PUNKTER TIL TEST AF FireDb.tilknyt_landsnumre()

-- FireDb.tilknyt_landsnumre() forudsætter at de adspurgte punkter findes i
-- databasen og at de ikke har et landsnr-ident i punktinformationstabellen.
-- Derfor indsættes her "tomme" punkter der kun har GeometriObjekter som eneste
-- anden information. Ud fra dette kan nye landsnumre genereres.
-------------------------------------------------------------------------------

INSERT INTO sag (
    id,
    registreringfra
) VALUES (
    'sag00006-aaaa-bbbb-cccc-000000000001',
    sysdate
);


INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagsid
) VALUES (
    'true',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Tilføj testdata til FireDb.tilknyt_landsnumre()',
    'sag00006-aaaa-bbbb-cccc-000000000001'
);


INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagsid
) VALUES (
    'sagevent-aaaa-bbbb-0006-000000000001',
    sysdate,
    7, -- oprettelse af punkt+geometri
    'sag00006-aaaa-bbbb-cccc-000000000001'
);

INSERT INTO sagseventinfo (
    registreringfra,
    registreringtil,
    beskrivelse,
    sagseventid
) VALUES (
    sysdate,
    null,
    'Punkter+geometrier til test af FireDb.tilknyt_landsnumre()',
    'sagevent-aaaa-bbbb-0006-000000000001'
);


INSERT INTO punkt (id,registreringfra,registreringtil,sagseventfraid) VALUES ('b3d47ca0-cfaa-484c-84d6-c864bbed133a',SYSDATE,NULL,'sagevent-aaaa-bbbb-0006-000000000001');
INSERT INTO geometriobjekt (registreringfra,registreringtil,sagseventfraid,sagseventtilid,punktid,geometri) VALUES (SYSDATE,NULL,'sagevent-aaaa-bbbb-0006-000000000001',NULL,'b3d47ca0-cfaa-484c-84d6-c864bbed133a',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.209327,56.173717,NULL),NULL,NULL));

INSERT INTO punkt (id,registreringfra,registreringtil,sagseventfraid) VALUES ('182a6be2-b048-48f9-8af7-093cc891f43d',SYSDATE,NULL,'sagevent-aaaa-bbbb-0006-000000000001');
INSERT INTO geometriobjekt (registreringfra,registreringtil,sagseventfraid,sagseventtilid,punktid,geometri) VALUES (SYSDATE,NULL,'sagevent-aaaa-bbbb-0006-000000000001',NULL,'182a6be2-b048-48f9-8af7-093cc891f43d',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.209223,56.163423,NULL),NULL,NULL));

INSERT INTO punkt (id,registreringfra,registreringtil,sagseventfraid) VALUES ('e2122480-ee8c-48c1-b89c-eb7fad18490b',SYSDATE,NULL,'sagevent-aaaa-bbbb-0006-000000000001');
INSERT INTO geometriobjekt (registreringfra,registreringtil,sagseventfraid,sagseventtilid,punktid,geometri) VALUES (SYSDATE,NULL,'sagevent-aaaa-bbbb-0006-000000000001',NULL,'e2122480-ee8c-48c1-b89c-eb7fad18490b',MDSYS.SDO_GEOMETRY(2001,4326,MDSYS.SDO_POINT_TYPE(10.204990,56.155215,NULL),NULL,NULL));

COMMIT;

-------------------------------------------------------------------------------
-- PUNKTINFO TIL TEST AF FIRE NIV UDTRÆK/ILÆG-REVISION

-- Det forudsættes at forskellige punktinformationer er til stede i databasen.
-------------------------------------------------------------------------------

INSERT INTO sag (
    id,
    registreringfra
) VALUES (
    'sag00007-aaaa-bbbb-cccc-000000000001',
    sysdate
);


INSERT INTO sagsinfo (
    aktiv,
    registreringfra,
    registreringtil,
    journalnummer,
    behandler,
    beskrivelse,
    sagsid
) VALUES (
    'true',
    sysdate,
    null,
    null,
    'Kristian Evers',
    'Tilføj testdata til fire niv udtræk/ilæg-revision',
    'sag00007-aaaa-bbbb-cccc-000000000001'
);


INSERT INTO sagsevent (
    id,
    registreringfra,
    eventtypeid,
    sagsid
) VALUES (
    'sagevent-aaaa-bbbb-0007-000000000001',
    sysdate,
    5, -- oprettelse af punktinfo
    'sag00007-aaaa-bbbb-cccc-000000000001'
);

INSERT INTO sagseventinfo (
    registreringfra,
    registreringtil,
    beskrivelse,
    sagseventid
) VALUES (
    sysdate,
    null,
    'Punktinfo til test af fire niv udtræk/ilæg-revision',
    'sagevent-aaaa-bbbb-0007-000000000001'
);

INSERT INTO punktinfo (registreringfra, sagseventfraid, infotypeid, tekst, punktid)
VALUES (SYSDATE, 'sag00007-aaaa-bbbb-cccc-000000000001', 360, 'Radiohuset', '301b8578-8cc8-48a8-8446-541f31482f86');
INSERT INTO punktinfo (registreringfra, sagseventfraid, infotypeid, punktid)
VALUES (SYSDATE, 'sag00007-aaaa-bbbb-cccc-000000000001', 370,  '301b8578-8cc8-48a8-8446-541f31482f86');
INSERT INTO punktinfo (registreringfra, sagseventfraid, infotypeid, tekst, punktid)VALUES (SYSDATE, 'sag00007-aaaa-bbbb-cccc-000000000001', 360, 'Radiohuset 2', '4b4c5c17-32e8-495d-a598-cdf42e0892de');
