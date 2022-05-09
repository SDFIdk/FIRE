-- OM VIEWS I FIRE
-- ---------------
--
-- En række materialized views er oprettet i FIRE-databasen med henblik på at
-- gøre databasens indhold lettere tilgængeligt i et GIS-program. For at
-- databasens geometrier er praktisk anvendelige, er det nødvendigt at bygge et
-- spatialt index over dem. Det lader sig i Oracle kun gøre på materialized
-- views. Materialized views opdateres ikke automatisk på samme måde som
-- almindelige views. For at holde informationerne relativt friske opdateres de
-- materialiserede views en gang i døgnet.


-- ÆNDRING AF VIEWS
-------------------
-- Ved ændring af queries i views er det nødvendigt først at
-- fjerne det
--
--   DROP MATERIALIZED VIEW v_view;
--
-- og dernæst oprette det med nyt indhold
--
--   CREATE MATERIALIZED VIEW v_view ...
--
-- Når viewet er oprettet igen skal der desuden tilføjes et
-- nyt spatialt index, eksempelvis
--
--   CREATE INDEX v_view_geometri_idx
--	 ON v_view (geometri)
-- 	 INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');

-- DEBUGGING
------------
-- Ved debugging af views kan følgende queries være nyttige.
--
-- Oversigt over materialized views og deres status
--
--		SELECT * FROM user_mviews ORDER BY mview_name;
--
-- Oversigt over registrerede tabeller og views med geometrier
--
-- 		SELECT * FROM user_sdo_geom_metadata;
--
-- Oversigt over spatiale index på tabeller og views
--
--		SELECT * FROM user_sdo_index_info;


-- V_FIKSPUNKTER_DK
--
-- Danske fikspunkter til brug i den kommunale vedligehold etc
CREATE MATERIALIZED VIEW v_fikspunkter_dk
REFRESH ON DEMAND
START WITH SYSDATE NEXT SYSDATE + 1 / 24
AS
WITH
  landsnr AS (
    SELECT infotypeid id
    FROM punktinfotype
    WHERE infotype = 'IDENT:landsnr'
  ),
  landsnumre AS (
    SELECT
      pi.punktid punktid,
	  -- I tilfælde af flere landsnumre er registret. De *bør* der ikke være,
	  -- men det kan ske og derfor er det smart med en safe-guard
      MIN(tekst) KEEP (DENSE_RANK FIRST ORDER BY tekst) landsnummer
    FROM punktinfo pi, landsnr
    WHERE
        pi.infotypeid = landsnr.id
      AND
        pi.registreringtil IS NULL
    GROUP BY pi.punktid
  ),
  -- punkter med følgende attributter er uønskede (listen bør korrespondere med "fire niv udtræk-revision")
  irrelevantpkt AS (
    SELECT infotypeid id
    FROM punktinfotype
    WHERE infotype IN (
    	'ATTR:MV_punkt',
    	'ATTR:hjælpepunkt',
    	'ATTR:teknikpunkt',
    	'ATTR:tabtgået',
    	'REGION:EE',
    	'REGION:FO',
    	'REGION:GL',
    	'REGION:SE',
    	'REGION:SJ'
    )
  ),
  irrelevantepunkter AS (
    SELECT pi.punktid
    FROM punktinfo pi, irrelevantpkt
    WHERE
        pi.infotypeid IN irrelevantpkt.id
      AND
        pi.registreringtil IS NULL
    ),
  -- geometrier
  geometrier AS (
    SELECT go.geometri, go.punktid
    FROM geometriobjekt go
    WHERE go.registreringtil IS NULL
  ),
  -- koordinater
  dvr90 AS (
    SELECT sridid id
    FROM sridtype
    WHERE sridtype.srid = 'EPSG:5799'
  ),
  koter AS (
    SELECT k.z, k.sz, k.t, k.transformeret, k.punktid
    FROM koordinat k, dvr90
    WHERE
        k.registreringtil IS NULL
      AND
        k.sridid = dvr90.id
  ),
  beskrivelser AS (
	SELECT pi.punktid, pi.tekst FROM punktinfo pi
	JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
	WHERE pit.infotype='ATTR:beskrivelse' AND pi.registreringtil IS NULL
  )
SELECT
  geometrier.geometri geometri,
  p.id punktid,
  landsnumre.landsnummer landsnr,
  koter.z dvr90_kote,
  koter.sz kotespredning,
  koter.t beregningstidspunkt,
  koter.transformeret transformeret,
  beskrivelser.tekst beskrivelse
FROM punkt p
JOIN landsnumre ON landsnumre.punktid = p.id
JOIN geometrier ON geometrier.punktid = p.id
-- ikke alle punkter har beskrivelse m.m.
LEFT JOIN beskrivelser ON beskrivelser.punktid = p.id
LEFT JOIN koter ON koter.punktid = p.id
LEFT JOIN irrelevantepunkter ON irrelevantepunkter.punktid = p.id
WHERE
    p.registreringtil IS NULL
  AND
    irrelevantepunkter.punktid IS NULL -- vi sorterer irrelevante punkter fra
  AND
    SDO_INSIDE(
      geometrier.geometri,
      SDO_GEOMETRY(
        2003,
        4326,
        NULL,
        MDSYS.SDO_ELEM_INFO_ARRAY(1,1003,3),
        SDO_ORDINATE_ARRAY(3,54,16,59) -- cirka bounding box for Danmark
      )
    ) = 'TRUE'
;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_FIKSPUNKTER_DK',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_fikspunkter_dk_geometri_idx
ON v_fikspunkter_dk (geometri)
INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');

-- V_CORS_DK
--
-- Danske CORS stationer (NET:CORS), inklusiv
--  ETRS89 koordinater
--  DVR90 koter
CREATE MATERIALIZED VIEW v_cors_dk
REFRESH ON DEMAND
START WITH SYSDATE NEXT SYSDATE + 1 / 24
AS
WITH
	punkter AS (
		SELECT pi.punktid FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='NET:CORS' AND pi.registreringtil IS NULL
	),
	gnss_ident AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:GNSS' AND pi.registreringtil IS NULL
	),
	landsnr AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:landsnr' AND pi.registreringtil IS NULL
	),
	etrs89 AS (
		SELECT k.punktid,k.t,k.x,k.y,k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:4937' AND k.registreringtil IS NULL
	),
	dvr90 AS (
		SELECT k.punktid, k.t, k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:5799' AND k.registreringtil IS NULL
	),
	geometrier AS (
		SELECT geometri, punktid FROM geometriobjekt go
		WHERE go.registreringtil IS NULL
	),
	tabtgaaet AS (
		SELECT pi.punktid, 'TRUE' AS tabtgaaet FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='ATTR:tabtgået' AND pi.registreringtil IS NULL
	)
SELECT
	geometrier.geometri,
	landsnr.ident LANDSNR,
	gnss_ident.ident GNSS_NAVN,
	etrs89.t  ETRS89_T,
	etrs89.x  ETRS89_LON,
	etrs89.y  ETRS89_LAT,
	etrs89.z  ETRS89_ELLPSH,
	dvr90.t   DVR90_T,
	dvr90.z   DVR90_KOTE
FROM punkter
LEFT JOIN gnss_ident ON punkter.punktid=gnss_ident.punktid
LEFT JOIN landsnr ON punkter.punktid=landsnr.punktid
LEFT JOIN etrs89 ON punkter.punktid=etrs89.punktid
LEFT JOIN dvr90 ON punkter.punktid=dvr90.punktid
LEFT JOIN tabtgaaet ON punkter.punktid=tabtgaaet.punktid
JOIN geometrier ON punkter.punktid=geometrier.punktid
WHERE tabtgaaet.tabtgaaet IS NULL;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_CORS_DK',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_cors_dk_geometri_idx ON v_cors_dk (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');

-- TAPAS PUNKTER
CREATE MATERIALIZED VIEW v_tapas
REFRESH ON DEMAND
START WITH SYSDATE NEXT SYSDATE + 1 / 24
AS
WITH
	punkter AS (
		SELECT pi.punktid FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='NET:TAPAS' AND pi.registreringtil IS NULL
	),
	gnss_ident AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:GNSS' AND pi.registreringtil IS NULL
	),
	landsnr AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:landsnr' AND pi.registreringtil IS NULL
	),
	etrs89 AS (
		SELECT k.punktid,k.t,k.x,k.y,k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:4937' AND k.registreringtil IS NULL
	),
	dvr90 AS (
		SELECT k.punktid, k.t, k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:5799' AND k.registreringtil IS NULL
	),
	geometrier AS (
		SELECT geometri, punktid FROM geometriobjekt go
		WHERE go.registreringtil IS NULL
	),
	tabtgaaet AS (
		SELECT pi.punktid, 'TRUE' AS tabtgaaet FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='ATTR:tabtgået' AND pi.registreringtil IS NULL
	)
SELECT
	geometrier.geometri,
	landsnr.ident LANDSNR,
	gnss_ident.ident GNSS_NAVN,
	etrs89.t  ETRS89_T,
	etrs89.x  ETRS89_LON,
	etrs89.y  ETRS89_LAT,
	etrs89.z  ETRS89_ELLPSH,
	dvr90.t   DVR90_T,
	dvr90.z   DVR90_KOTE
FROM punkter
LEFT JOIN gnss_ident ON punkter.punktid=gnss_ident.punktid
LEFT JOIN landsnr ON punkter.punktid=landsnr.punktid
LEFT JOIN etrs89 ON punkter.punktid=etrs89.punktid
LEFT JOIN dvr90 ON punkter.punktid=dvr90.punktid
LEFT JOIN tabtgaaet ON punkter.punktid=tabtgaaet.punktid
JOIN geometrier ON punkter.punktid=geometrier.punktid
WHERE tabtgaaet.tabtgaaet IS NULL;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_TAPAS',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_tapas_geometri_idx ON v_tapas (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');

-- 5D PUNKTER
CREATE MATERIALIZED VIEW v_5d_punkter
REFRESH ON DEMAND
START WITH SYSDATE NEXT SYSDATE + 1 / 24
AS
WITH
	punkter AS (
		SELECT pi.punktid FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='NET:5D' AND pi.registreringtil IS NULL
	),
	gnss_ident AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:GNSS' AND pi.registreringtil IS NULL
	),
	landsnr AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:landsnr' AND pi.registreringtil IS NULL
	),
	etrs89 AS (
		SELECT k.punktid,k.t,k.x,k.y,k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:4937' AND k.registreringtil IS NULL
	),
	dvr90 AS (
		SELECT k.punktid, k.t, k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:5799' AND k.registreringtil IS NULL
	),
	geometrier AS (
		SELECT geometri, punktid FROM geometriobjekt go
		WHERE go.registreringtil IS NULL
	),
	tabtgaaet AS (
		SELECT pi.punktid, 'TRUE' AS tabtgaaet FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='ATTR:tabtgået' AND pi.registreringtil IS NULL
	)
SELECT
	geometrier.geometri,
	landsnr.ident LANDSNR,
	gnss_ident.ident GNSS_NAVN,
	etrs89.t  ETRS89_T,
	etrs89.x  ETRS89_LON,
	etrs89.y  ETRS89_LAT,
	etrs89.z  ETRS89_ELLPSH,
	dvr90.t   DVR90_T,
	dvr90.z   DVR90_KOTE
FROM punkter
LEFT JOIN gnss_ident ON punkter.punktid=gnss_ident.punktid
LEFT JOIN landsnr ON punkter.punktid=landsnr.punktid
LEFT JOIN etrs89 ON punkter.punktid=etrs89.punktid
LEFT JOIN dvr90 ON punkter.punktid=dvr90.punktid
LEFT JOIN tabtgaaet ON punkter.punktid=tabtgaaet.punktid
JOIN geometrier ON punkter.punktid=geometrier.punktid
WHERE tabtgaaet.tabtgaaet IS NULL;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_5D_PUNKTER',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_5d_punkter_geometri_idx ON v_5d_punkter (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');


-- 10KM PUNKTER
CREATE MATERIALIZED VIEW v_10km_punkter
REFRESH ON DEMAND
START WITH SYSDATE NEXT SYSDATE + 1 / 24
AS
WITH
	punkter AS (
		SELECT pi.punktid FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='NET:10KM' AND pi.registreringtil IS NULL
	),
	gnss_ident AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:GNSS' AND pi.registreringtil IS NULL
	),
	landsnr AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:landsnr' AND pi.registreringtil IS NULL
	),
	etrs89 AS (
		SELECT k.punktid,k.t,k.x,k.y,k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:4937' AND k.registreringtil IS NULL
	),
	dvr90 AS (
		SELECT k.punktid, k.t, k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:5799' AND k.registreringtil IS NULL
	),
	geometrier AS (
		SELECT geometri, punktid FROM geometriobjekt go
		WHERE go.registreringtil IS NULL
	),
	tabtgaaet AS (
		SELECT pi.punktid, 'TRUE' AS tabtgaaet FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='ATTR:tabtgået' AND pi.registreringtil IS NULL
	)
SELECT
	geometrier.geometri,
	landsnr.ident LANDSNR,
	gnss_ident.ident GNSS_NAVN,
	etrs89.t  ETRS89_T,
	etrs89.x  ETRS89_LON,
	etrs89.y  ETRS89_LAT,
	etrs89.z  ETRS89_ELLPSH,
	dvr90.t   DVR90_T,
	dvr90.z   DVR90_KOTE
FROM punkter
LEFT JOIN gnss_ident ON punkter.punktid=gnss_ident.punktid
LEFT JOIN landsnr ON punkter.punktid=landsnr.punktid
LEFT JOIN etrs89 ON punkter.punktid=etrs89.punktid
LEFT JOIN dvr90 ON punkter.punktid=dvr90.punktid
LEFT JOIN tabtgaaet ON punkter.punktid=tabtgaaet.punktid
JOIN geometrier ON punkter.punktid=geometrier.punktid
WHERE tabtgaaet.tabtgaaet IS NULL;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_10KM_PUNKTER',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_10km_punkter_geometri_idx ON v_10km_punkter (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');


-- DMI Vandstandsmålere
CREATE MATERIALIZED VIEW v_dmi_vandstandsmaalere
REFRESH ON DEMAND
START WITH SYSDATE NEXT SYSDATE + 1 / 24
AS
WITH
	punkter AS (
		SELECT pi.punktid FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='NET:DMI' AND pi.registreringtil IS NULL
	),
	gnss_ident AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:GNSS' AND pi.registreringtil IS NULL
	),
	landsnr AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:landsnr' AND pi.registreringtil IS NULL
	),
	etrs89 AS (
		SELECT k.punktid,k.t,k.x,k.y,k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:4937' AND k.registreringtil IS NULL
	),
	dvr90 AS (
		SELECT k.punktid, k.t, k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:5799' AND k.registreringtil IS NULL
	),
	geometrier AS (
		SELECT geometri, punktid FROM geometriobjekt go
		WHERE go.registreringtil IS NULL
	),
	tabtgaaet AS (
		SELECT pi.punktid, 'TRUE' AS tabtgaaet FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='ATTR:tabtgået' AND pi.registreringtil IS NULL
	)
SELECT
	geometrier.geometri,
	landsnr.ident LANDSNR,
	gnss_ident.ident GNSS_NAVN,
	etrs89.t  ETRS89_T,
	etrs89.x  ETRS89_LON,
	etrs89.y  ETRS89_LAT,
	etrs89.z  ETRS89_ELLPSH,
	dvr90.t   DVR90_T,
	dvr90.z   DVR90_KOTE
FROM punkter
LEFT JOIN gnss_ident ON punkter.punktid=gnss_ident.punktid
LEFT JOIN landsnr ON punkter.punktid=landsnr.punktid
LEFT JOIN etrs89 ON punkter.punktid=etrs89.punktid
LEFT JOIN dvr90 ON punkter.punktid=dvr90.punktid
LEFT JOIN tabtgaaet ON punkter.punktid=tabtgaaet.punktid
JOIN geometrier ON punkter.punktid=geometrier.punktid
WHERE tabtgaaet.tabtgaaet IS NULL;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_DMI_VANDSTANDSMAALERE',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_dmi_vandstandsmaalere_geometri_idx ON v_dmi_vandstandsmaalere (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');

-- DVR90 definerende vandstandsmålere
CREATE MATERIALIZED VIEW v_dvr90_vandstandsmaalere
REFRESH ON DEMAND
START WITH SYSDATE NEXT SYSDATE + 1 / 24
AS
WITH
	punkter AS (
		SELECT pi.punktid FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='NET:DEFVAND' AND pi.registreringtil IS NULL
	),
	gnss_ident AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:GNSS' AND pi.registreringtil IS NULL
	),
	landsnr AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:landsnr' AND pi.registreringtil IS NULL
	),
	etrs89 AS (
		SELECT k.punktid,k.t,k.x,k.y,k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:4937' AND k.registreringtil IS NULL
	),
	dvr90 AS (
		SELECT k.punktid, k.t, k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:5799' AND k.registreringtil IS NULL
	),
	geometrier AS (
		SELECT geometri, punktid FROM geometriobjekt go
		WHERE go.registreringtil IS NULL
	),
	tabtgaaet AS (
		SELECT pi.punktid, 'TRUE' AS tabtgaaet FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='ATTR:tabtgået' AND pi.registreringtil IS NULL
	)
SELECT
	geometrier.geometri,
	landsnr.ident LANDSNR,
	gnss_ident.ident GNSS_NAVN,
	etrs89.t  ETRS89_T,
	etrs89.x  ETRS89_LON,
	etrs89.y  ETRS89_LAT,
	etrs89.z  ETRS89_ELLPSH,
	dvr90.t   DVR90_T,
	dvr90.z   DVR90_KOTE
FROM punkter
LEFT JOIN gnss_ident ON punkter.punktid=gnss_ident.punktid
LEFT JOIN landsnr ON punkter.punktid=landsnr.punktid
LEFT JOIN etrs89 ON punkter.punktid=etrs89.punktid
LEFT JOIN dvr90 ON punkter.punktid=dvr90.punktid
LEFT JOIN tabtgaaet ON punkter.punktid=tabtgaaet.punktid
JOIN geometrier ON punkter.punktid=geometrier.punktid
WHERE tabtgaaet.tabtgaaet IS NULL;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_DVR90_VANDSTANDSMAALERE',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_dvr90_vandstandsmaalere_geometri_idx ON v_dvr90_vandstandsmaalere (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');

-- GPSNet PUNKTER
CREATE MATERIALIZED VIEW v_gpsnet
REFRESH ON DEMAND
START WITH SYSDATE NEXT SYSDATE + 1 / 24
AS
WITH
	punkter AS (
		SELECT pi.punktid FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='NET:GPSNET' AND pi.registreringtil IS NULL
	),
	gnss_ident AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:GNSS' AND pi.registreringtil IS NULL
	),
	landsnr AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:landsnr' AND pi.registreringtil IS NULL
	),
	etrs89 AS (
		SELECT k.punktid,k.t,k.x,k.y,k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:4937' AND k.registreringtil IS NULL
	),
	dvr90 AS (
		SELECT k.punktid, k.t, k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:5799' AND k.registreringtil IS NULL
	),
	geometrier AS (
		SELECT geometri, punktid FROM geometriobjekt go
		WHERE go.registreringtil IS NULL
	),
	tabtgaaet AS (
		SELECT pi.punktid, 'TRUE' AS tabtgaaet FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='ATTR:tabtgået' AND pi.registreringtil IS NULL
	)
SELECT
	geometrier.geometri,
	landsnr.ident LANDSNR,
	gnss_ident.ident GNSS_NAVN,
	etrs89.t  ETRS89_T,
	etrs89.x  ETRS89_LON,
	etrs89.y  ETRS89_LAT,
	etrs89.z  ETRS89_ELLPSH,
	dvr90.t   DVR90_T,
	dvr90.z   DVR90_KOTE
FROM punkter
LEFT JOIN gnss_ident ON punkter.punktid=gnss_ident.punktid
LEFT JOIN landsnr ON punkter.punktid=landsnr.punktid
LEFT JOIN etrs89 ON punkter.punktid=etrs89.punktid
LEFT JOIN dvr90 ON punkter.punktid=dvr90.punktid
LEFT JOIN tabtgaaet ON punkter.punktid=tabtgaaet.punktid
JOIN geometrier ON punkter.punktid=geometrier.punktid
WHERE tabtgaaet.tabtgaaet IS NULL;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_GPSNET',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_gpsnet_geometri_idx ON v_gpsnet (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');


-- SmartNet PUNKTER
CREATE MATERIALIZED VIEW v_smartnet
REFRESH ON DEMAND
START WITH SYSDATE NEXT SYSDATE + 1 / 24
AS
WITH
	punkter AS (
		SELECT pi.punktid FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='NET:SMARTNET' AND pi.registreringtil IS NULL
	),
	gnss_ident AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:GNSS' AND pi.registreringtil IS NULL
	),
	landsnr AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:landsnr' AND pi.registreringtil IS NULL
	),
	etrs89 AS (
		SELECT k.punktid,k.t,k.x,k.y,k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:4937' AND k.registreringtil IS NULL
	),
	dvr90 AS (
		SELECT k.punktid, k.t, k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:5799' AND k.registreringtil IS NULL
	),
	geometrier AS (
		SELECT geometri, punktid FROM geometriobjekt go
		WHERE go.registreringtil IS NULL
	),
	tabtgaaet AS (
		SELECT pi.punktid, 'TRUE' AS tabtgaaet FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='ATTR:tabtgået' AND pi.registreringtil IS NULL
	)
SELECT
	geometrier.geometri,
	landsnr.ident LANDSNR,
	gnss_ident.ident GNSS_NAVN,
	etrs89.t  ETRS89_T,
	etrs89.x  ETRS89_LON,
	etrs89.y  ETRS89_LAT,
	etrs89.z  ETRS89_ELLPSH,
	dvr90.t   DVR90_T,
	dvr90.z   DVR90_KOTE
FROM punkter
LEFT JOIN gnss_ident ON punkter.punktid=gnss_ident.punktid
LEFT JOIN landsnr ON punkter.punktid=landsnr.punktid
LEFT JOIN etrs89 ON punkter.punktid=etrs89.punktid
LEFT JOIN dvr90 ON punkter.punktid=dvr90.punktid
LEFT JOIN tabtgaaet ON punkter.punktid=tabtgaaet.punktid
JOIN geometrier ON punkter.punktid=geometrier.punktid
WHERE tabtgaaet.tabtgaaet IS NULL;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_SMARTNET',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_smartnet_geometri_idx ON v_smartnet (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');

-- RTKConnect PUNKTER
CREATE MATERIALIZED VIEW v_rtkconnect
REFRESH ON DEMAND
START WITH SYSDATE NEXT SYSDATE + 1 / 24
AS
WITH
	punkter AS (
		SELECT pi.punktid FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='NET:RTKCONNECT' AND pi.registreringtil IS NULL
	),
	gnss_ident AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:GNSS' AND pi.registreringtil IS NULL
	),
	landsnr AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:landsnr' AND pi.registreringtil IS NULL
	),
	etrs89 AS (
		SELECT k.punktid,k.t,k.x,k.y,k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:4937' AND k.registreringtil IS NULL
	),
	dvr90 AS (
		SELECT k.punktid, k.t, k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:5799' AND k.registreringtil IS NULL
	),
	geometrier AS (
		SELECT geometri, punktid FROM geometriobjekt go
		WHERE go.registreringtil IS NULL
	),
	tabtgaaet AS (
		SELECT pi.punktid, 'TRUE' AS tabtgaaet FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='ATTR:tabtgået' AND pi.registreringtil IS NULL
	)
SELECT
	geometrier.geometri,
	landsnr.ident LANDSNR,
	gnss_ident.ident GNSS_NAVN,
	etrs89.t  ETRS89_T,
	etrs89.x  ETRS89_LON,
	etrs89.y  ETRS89_LAT,
	etrs89.z  ETRS89_ELLPSH,
	dvr90.t   DVR90_T,
	dvr90.z   DVR90_KOTE
FROM punkter
LEFT JOIN gnss_ident ON punkter.punktid=gnss_ident.punktid
LEFT JOIN landsnr ON punkter.punktid=landsnr.punktid
LEFT JOIN etrs89 ON punkter.punktid=etrs89.punktid
LEFT JOIN dvr90 ON punkter.punktid=dvr90.punktid
LEFT JOIN tabtgaaet ON punkter.punktid=tabtgaaet.punktid
JOIN geometrier ON punkter.punktid=geometrier.punktid
WHERE tabtgaaet.tabtgaaet IS NULL;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_RTKCONNECT',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_rtkconnect_geometri_idx ON v_rtkconnect (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');

-- Tabtgåede punkter
CREATE MATERIALIZED VIEW v_tabte_punkter
REFRESH ON DEMAND
START WITH SYSDATE NEXT SYSDATE + 1 / 24
AS
WITH
	punkter AS (
		SELECT pi.punktid FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='ATTR:tabtgået' AND pi.registreringtil IS NULL
	),
	landsnr AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:landsnr' AND pi.registreringtil IS NULL
	),
	beskrivelser AS (
		SELECT pi.punktid, pi.tekst tekst FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='ATTR:beskrivelse' AND pi.registreringtil IS NULL
	),
	geometrier AS (
		SELECT geometri, punktid FROM geometriobjekt go
		WHERE go.registreringtil IS NULL
	)
SELECT
	geometrier.geometri,
	landsnr.ident landsnr,
	beskrivelser.tekst
FROM punkter
JOIN landsnr ON punkter.punktid=landsnr.punktid
JOIN beskrivelser ON punkter.punktid=beskrivelser.punktid
JOIN geometrier ON punkter.punktid=geometrier.punktid;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_TABTE_PUNKTER',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_tabte_punkter_geometri_idx ON v_tabte_punkter (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');

--  GNET Stationer
CREATE MATERIALIZED VIEW v_gnet
REFRESH ON DEMAND
START WITH SYSDATE NEXT SYSDATE + 1 / 24
AS
WITH
	punkter AS (
		SELECT pi.punktid FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='NET:GNET' AND pi.registreringtil IS NULL
	),
	gnss_ident AS (
		SELECT pi.punktid, pi.tekst ident FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='IDENT:GNSS' AND pi.registreringtil IS NULL
	),
	gr96 AS (
		SELECT k.punktid,k.t,k.x,k.y,k.z FROM koordinat k
		JOIN sridtype st ON k.sridid=st.sridid
		WHERE st.srid = 'EPSG:4909' AND k.registreringtil IS NULL
	),
	geometrier AS (
		SELECT geometri, punktid FROM geometriobjekt go
		WHERE go.registreringtil IS NULL
	),
	tabtgaaet AS (
		SELECT pi.punktid, 'TRUE' AS tabtgaaet FROM punktinfo pi
		JOIN punktinfotype pit ON pi.infotypeid=pit.infotypeid
		WHERE pit.infotype='ATTR:tabtgået' AND pi.registreringtil IS NULL
	)
SELECT
	geometrier.geometri,
	gnss_ident.ident GNSS_NAVN,
	gr96.t  GR96_T,
	gr96.x  GR96_LON,
	gr96.y  GR96_LAT,
	gr96.z  GR96_ELLPSH
FROM punkter
LEFT JOIN gnss_ident ON punkter.punktid=gnss_ident.punktid
LEFT JOIN gr96 ON punkter.punktid=gr96.punktid
LEFT JOIN tabtgaaet ON punkter.punktid=tabtgaaet.punktid
JOIN geometrier ON punkter.punktid=geometrier.punktid
WHERE tabtgaaet.tabtgaaet IS NULL;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_GNET',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_gnet_geometri_idx ON v_gnet (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=point');


-- 3. præs observationer
CREATE MATERIALIZED VIEW v_pres3_obs AS
SELECT
	-- go1.geometri geometri_opstillingspunkt,
	-- go2.geometri geometri_sigtepunkt,
	sdo_geometry(
		2002,
		4326,
		NULL,
		sdo_elem_info_array (1,2,1),
		sdo_ordinate_array (go1.geometri.sdo_point.x, go1.geometri.sdo_point.y, go2.geometri.sdo_point.x, go2.geometri.sdo_point.y)) geometri,
	o.value1 koteforskel,
	o.value2 nivlaengde,
	o.value3 antal_opstillinger,
	o.value4 eta1,
	o.value5 spredning,
	o.value6 centreringsfejl
FROM observation o
JOIN observationstype ot ON ot.observationstypeid=o.observationstypeid
JOIN geometriobjekt go1 ON go1.PUNKTID=o.opstillingspunktid
JOIN geometriobjekt go2 ON go2.PUNKTID=o.sigtepunktid
WHERE
	ot.observationstype='geometrisk_koteforskel'
	AND
	o.value7=3
;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_PRES3_OBS',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_pres3_obs_geometri_idx ON v_pres3_obs (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=line');

-- 2. præs observationer

CREATE MATERIALIZED VIEW v_pres2_obs AS
SELECT
	-- go1.geometri geometri_opstillingspunkt,
	-- go2.geometri geometri_sigtepunkt,
	sdo_geometry(
		2002,
		4326,
		NULL,
		sdo_elem_info_array (1,2,1),
		sdo_ordinate_array (go1.geometri.sdo_point.x, go1.geometri.sdo_point.y, go2.geometri.sdo_point.x, go2.geometri.sdo_point.y)) geometri,
	o.value1 koteforskel,
	o.value2 nivlaengde,
	o.value3 antal_opstillinger,
	o.value4 eta1,
	o.value5 spredning,
	o.value6 centreringsfejl
FROM observation o
JOIN observationstype ot ON ot.observationstypeid=o.observationstypeid
JOIN geometriobjekt go1 ON go1.PUNKTID=o.opstillingspunktid
JOIN geometriobjekt go2 ON go2.PUNKTID=o.sigtepunktid
WHERE
	ot.observationstype='geometrisk_koteforskel'
	AND
	o.value7=2
;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_PRES2_OBS',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_pres2_obs_geometri_idx ON v_pres2_obs (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=line');


-- 1. præs observationer
CREATE MATERIALIZED VIEW v_pres1_obs AS
SELECT
	-- go1.geometri geometri_opstillingspunkt,
	-- go2.geometri geometri_sigtepunkt,
	sdo_geometry(
		2002,
		4326,
		NULL,
		sdo_elem_info_array (1,2,1),
		sdo_ordinate_array (go1.geometri.sdo_point.x, go1.geometri.sdo_point.y, go2.geometri.sdo_point.x, go2.geometri.sdo_point.y)) geometri,
	o.value1 koteforskel,
	o.value2 nivlaengde,
	o.value3 antal_opstillinger,
	o.value4 eta1,
	o.value5 spredning,
	o.value6 centreringsfejl
FROM observation o
JOIN observationstype ot ON ot.observationstypeid=o.observationstypeid
JOIN geometriobjekt go1 ON go1.PUNKTID=o.opstillingspunktid
JOIN geometriobjekt go2 ON go2.PUNKTID=o.sigtepunktid
WHERE
	ot.observationstype='geometrisk_koteforskel'
	AND
	o.value7=1
;

INSERT INTO
  user_sdo_geom_metadata (table_name, column_name, diminfo, srid)
VALUES
  (
    'V_PRES1_OBS',
    'GEOMETRI',
    MDSYS.SDO_DIM_ARRAY(
      MDSYS.SDO_DIM_ELEMENT('Longitude', -180.0000, 180.0000, 0.005),
      MDSYS.SDO_DIM_ELEMENT('Latitude', -90.0000, 90.0000, 0.005)
    ),
    4326
  );

CREATE INDEX v_pres1_obs_geometri_idx ON v_pres1_obs (geometri) INDEXTYPE IS MDSYS.SPATIAL_INDEX PARAMETERS('layer_gtype=line');
