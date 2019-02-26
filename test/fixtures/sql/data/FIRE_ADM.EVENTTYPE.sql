SET DEFINE OFF;
--SQL Statement which produced this data:
--
--  SELECT * FROM FIRE_ADM.EVENTTYPE;
--
Insert into EVENTTYPE
   (OBJECTID, BESKRIVELSE, EVENT, EVENTTYPEID)
 Values
   (1, 'bruges når koordinater indsættes efter en beregning', 'koordinat_beregnet', 1);
Insert into EVENTTYPE
   (OBJECTID, BESKRIVELSE, EVENT, EVENTTYPEID)
 Values
   (2, 'bruges når en koordinat nedlægges', 'koordinat_nedlagt', 2);
Insert into EVENTTYPE
   (OBJECTID, BESKRIVELSE, EVENT, EVENTTYPEID)
 Values
   (3, 'Indsættelse af en eller flere observationer', 'observation_indsat', 3);
Insert into EVENTTYPE
   (OBJECTID, BESKRIVELSE, EVENT, EVENTTYPEID)
 Values
   (4, 'bruges når en observation aflyses fordi den er fejlbehæftet', 'observation_nedlagt', 4);
Insert into EVENTTYPE
   (OBJECTID, BESKRIVELSE, EVENT, EVENTTYPEID)
 Values
   (5, 'bruges når der tilføjes Punkinfo til et eller flere punkter', 'punktinfo_tilføjet', 5);
Insert into EVENTTYPE
   (OBJECTID, BESKRIVELSE, EVENT, EVENTTYPEID)
 Values
   (6, 'bruges når Punktinfo fjernes fra et eller flere punkter', 'punktinfo_fjernet', 6);
Insert into EVENTTYPE
   (OBJECTID, BESKRIVELSE, EVENT, EVENTTYPEID)
 Values
   (7, 'bruges når et punkt og tilhørende geometri oprettes', 'punkt_oprettet', 7);
Insert into EVENTTYPE
   (OBJECTID, BESKRIVELSE, EVENT, EVENTTYPEID)
 Values
   (8, 'bruges når et punkt og tilhørende geometri nedlægges', 'punkt_nedlagt', 8);
Insert into EVENTTYPE
   (OBJECTID, BESKRIVELSE, EVENT, EVENTTYPEID)
 Values
   (9, 'bruges når nye koordinater skabes. Knytter observationer til koordinater', 'beregning', 9);
Insert into EVENTTYPE
   (OBJECTID, BESKRIVELSE, EVENT, EVENTTYPEID)
 Values
   (10, 'bruges til at tilføje fritekst kommentarer til sagen i tilfælde af at der er behov for at påhæfte sagen yderligere information som ikke passer i andre hændelser. Bruges fx også til påhæftning af materiale på sagen.', 'kommentar', 10);
COMMIT;
