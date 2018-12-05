SET DEFINE OFF;
--SQL Statement which produced this data:
--
--  SELECT * FROM FIRE_ADM.OBSERVATIONTYPE;
--
Insert into OBSERVATIONTYPE
   (OBJECTID, BESKRIVELSE, OBSERVATIONSTYPE, SIGTEPUNKTID, VALUE1, 
    VALUE2, VALUE3, VALUE4, VALUE5, VALUE6, 
    VALUE7, VALUE8)
 Values
   (1, 'Koteforskel fra fikspunkt1 til fikspunkt2 (h2-h1) opmålt geometrisk ', 'geometrisk_koteforskel', 'true', 'Koteforskel [m]', 
    'Nivellementslængde [m]', 'Antal opstillinger', 'Variabel vedr. eta_1 (refraktion) [m^3]', 'Afstandsafhængig varians koteforskel pr. målt koteforskel [m^2/m]', 'Afstandsuafhængig varians koteforskel pr. målt koteforskel [m^2]', 
    'Total varians koteforskel [m^2]', 'Præcisionsnivellement [0,1,2,3]');
Insert into OBSERVATIONTYPE
   (OBJECTID, BESKRIVELSE, OBSERVATIONSTYPE, SIGTEPUNKTID, VALUE1, 
    VALUE2, VALUE3, VALUE4, VALUE5, VALUE6)
 Values
   (2, 'Koteforskel fra fikspunkt1 til fikspunkt2 (h2-h1) opmålt trigonometrisk', 'trigonometrisk_koteforskel', 'true', 'Koteforskel [m]', 
    'Nivellementslængde [m]', 'Antal opstillinger', 'Afstandsafhængig varians pr. målt koteforskel [m^2/m^2]', 'Afstandsuafhængig varians pr. målt koteforskel [m^2]', 'Total varians koteforskel [m^2]');
Insert into OBSERVATIONTYPE
   (OBJECTID, BESKRIVELSE, OBSERVATIONSTYPE, SIGTEPUNKTID, VALUE1, 
    VALUE2, VALUE3, VALUE4)
 Values
   (3, 'Horisontal retning med uret fra opstilling til sigtepunkt (reduceret til ellipsoiden)', 'retning', 'true', 'Retning [m]', 
    'Varians  retning hidrørende instrument, pr. sats  [rad^2]', 'Samlet centreringsvarians for instrument prisme [m^2]', 'Total varians retning [rad^2]');
Insert into OBSERVATIONTYPE
   (OBJECTID, BESKRIVELSE, OBSERVATIONSTYPE, SIGTEPUNKTID, VALUE1, 
    VALUE2, VALUE3, VALUE4)
 Values
   (4, 'Horisontal afstand mellem opstilling og sigtepunkt (reduceret til ellipsoiden)', 'horisontalafstand', 'true', 'Afstand [m]', 
    'Afstandsafhængig varians afstandsmåler [m^2/m^2]', 'Samlet varians for centrering af instrument og prisme, samt grundfejl på afstandsmåler [m^2]', 'Total varians horisontalafstand [m^2]');
Insert into OBSERVATIONTYPE
   (OBJECTID, BESKRIVELSE, OBSERVATIONSTYPE, SIGTEPUNKTID, VALUE1, 
    VALUE2, VALUE3, VALUE4)
 Values
   (5, 'Skråafstand mellem opstilling og sigtepunkt', 'skråafstand', 'true', 'Afstand [m]', 
    'Afstandsafhængig varians afstandsmåler pr. måling [m^2/m^2]', 'Samlet varians for centrering af instrument og prisme, samt grundfejl på afstandsmåler pr. måling [m^2]', 'Total varians skråafstand [m^2]');
Insert into OBSERVATIONTYPE
   (OBJECTID, BESKRIVELSE, OBSERVATIONSTYPE, SIGTEPUNKTID, VALUE1, 
    VALUE2, VALUE3, VALUE4, VALUE5, VALUE6)
 Values
   (6, 'Zenitvinkel mellem opstilling og sigtepunkt', 'zenitvinkel', 'true', 'Zenitvinkel [rad]', 
    'Instrumenthøjde [m]', 'Højde sigtepunkt [m]', 'Varians zenitvinkel hidrørende instrument, pr. sats  [rad^2]', 'Samlet varians instrumenthøjde/højde sigtepunkt [m^2]', 'Total varians zenitvinkel [rad^2]');
Insert into OBSERVATIONTYPE
   (OBJECTID, BESKRIVELSE, OBSERVATIONSTYPE, SIGTEPUNKTID, VALUE1, 
    VALUE2, VALUE3, VALUE4, VALUE5, VALUE6, 
    VALUE7, VALUE8, VALUE9, VALUE10, VALUE11, 
    VALUE12)
 Values
   (7, 'Vektor der beskriver koordinatforskellen fra punkt 1 til punkt 1 (v2-v1)', 'vektor', 'true', 'dx [m]', 
    'dy [m]', 'dz [m]', 'Afstandsafhængig varians [m^2/m^2]', 'Samlet varians for centrering af antenner [m^2]', 'Total varians [m^2]', 
    'Varians dx [m^2]', 'Varians dy [m^2]', 'Varians dz [m^2]', 'Covarians dx, dy [m^2]', 'Covarians dx, dz [m^2]', 
    'Covarians dy, dz [m^2]');
COMMIT;
