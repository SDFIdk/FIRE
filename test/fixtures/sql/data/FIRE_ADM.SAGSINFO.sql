SET DEFINE OFF;
--SQL Statement which produced this data:
--
--  SELECT * FROM FIRE_ADM.SAGSINFO;
--
Insert into SAGSINFO
   (OBJECTID, AKTIV, REGISTRERINGFRA, BEHANDLER, BESKRIVELSE, 
    SAGID)
 Values
   (1, 'true', TO_TIMESTAMP_TZ('01/10/2018 00:00:00.000000 +01:00','DD/MM/YYYY HH24:MI:SS.FF TZH:TZM'), 'Thomas Knudsen', 'Sagen er oprette i forbindelse med migrering af data fra REFGEO til FIRE', 
    '4f8f29c8-c38f-4c69-ae28-c7737178de1f');
COMMIT;
