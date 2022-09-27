-----------------------------------------------------------------------------------------
--                                FJERN ALLE TABELLER
--
-- Fjerner alle tabeller og tilhørende index, triggers m.m. med henblik på let at kunne
-- reetablere databasen i forbindelse med tests af ændringer i DDL eller testmateriale.
--
-- Som udgangspunkt fjernes 'herredsogn'-tabellen IKKE, da den typisk ikke ændrer sig
-- og tager en del tid at indlæse.
-----------------------------------------------------------------------------------------

DROP TABLE  beregning               CASCADE CONSTRAINTS;
DROP TABLE  beregning_koordinat     CASCADE CONSTRAINTS;
DROP TABLE  beregning_observation   CASCADE CONSTRAINTS;
DROP TABLE  eventtype               CASCADE CONSTRAINTS;
DROP TABLE  geometriobjekt          CASCADE CONSTRAINTS;
DROP TABLE  herredsogn              CASCADE CONSTRAINTS;
DROP TABLE  koordinat               CASCADE CONSTRAINTS;
DROP TABLE  tidsserie               CASCADE CONSTRAINTS;
DROP TABLE  tidsserie_koordinat     CASCADE CONSTRAINTS;
DROP TABLE  observation             CASCADE CONSTRAINTS;
DROP TABLE  observationstype        CASCADE CONSTRAINTS;
DROP TABLE  punkt                   CASCADE CONSTRAINTS;
DROP TABLE  punktsamling            CASCADE CONSTRAINTS;
DROP TABLE  punktsamling_punkt      CASCADE CONSTRAINTS;
DROP TABLE  punktinfo               CASCADE CONSTRAINTS;
DROP TABLE  punktinfotype           CASCADE CONSTRAINTS;
DROP TABLE  grafik                  CASCADE CONSTRAINTS;
DROP TABLE  sag                     CASCADE CONSTRAINTS;
DROP TABLE  sagsevent               CASCADE CONSTRAINTS;
DROP TABLE  sagseventinfo           CASCADE CONSTRAINTS;
DROP TABLE  sagseventinfo_html      CASCADE CONSTRAINTS;
DROP TABLE  sagseventinfo_materiale CASCADE CONSTRAINTS;
DROP TABLE  sagsinfo                CASCADE CONSTRAINTS;
DROP TABLE  sridtype                CASCADE CONSTRAINTS;

DELETE FROM user_sdo_geom_metadata WHERE table_name='GEOMETRIOBJEKT';
DELETE FROM user_sdo_geom_metadata WHERE table_name='HERREDSOGN';

COMMIT;
