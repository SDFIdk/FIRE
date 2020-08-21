.. _workshop:

Workshop
=======================

Indledning
---------------------------------

Velkommen til arbejdet med FIRE! Vi vil starte med at give en gennemgang af hvad 
man kan med det nuværende setup, og løbende vil der komme mere på.

Men før vi kommer rigtigt i gang, skal vi have noget basisviden om kommandolinjen.


Generelle kommandoer i linjen 
-----------------------------------------------------

Navigation
+++++++++++++++++++++++++

Her følger en kort liste over hvordan man i Windows navigerer rundt på sin pc 
vha. en terminal (fx miniconda) og kommandoer på linjen her. 

===================  ===========================================  ===========================================
**Kommando**         **Beskrivelse**                              **Eksempel på brug**
-------------------  -------------------------------------------  -------------------------------------------
ls                   Oplist mapper og filer                       > ls
dir eller ls -l      Oplist mapper og filer med detaljer          > ls -l
cd *dir*             Skift mappe (change directory)               > cd Users\\b031422\\Desktop
cd ..                Skift mappe et niveau op                     > cd ..
cd\                  Hop til roden af server                      > cd\\
*Drev*:              Skift drev (uafh. af aktuel placering        > F:
md *dir*             Opret ny mappe (make directory)              > md TEST
vim *fil*            Opret ny asciifil (fx med vim)               > vim TEST\\test
cp *fil1* *fil2*     Kopier (copy) en given *fil1* til *fil2*     > cp test ..\\testkopi	
mv *fil1* *fil2*     Flyt (move) en given *fil1* til *fil2*       > mv test ..\\. 
rm *fil*             Slet (remove) en given *fil*                 > rm test
rmdir *dir*          Slet tom mappe (remove directory)            > rmdir TEST
\*                   Indikerer *alt*                              > rm TEST\\\*
.                    Indikerer den aktuelle placering             > cp TEST\\test .
\| eller >           Information pipes videre i kommandokaldet    > cat test1 test2 >testsamlet
===================  ===========================================  ===========================================

De fleste kommandoer dur også på unix, dog husk at man på unix benytter slash, /, 
mens man på Windows benytter backslash, *\\*.

Hvis en sti er skrevet helt ud med */*, kan Windows dog godt genkende og oversætte 
til *\\*, men autocomplete funktionen *tab* fungerer ikke.
Det skyldes, at Windows læser */* som en "escape character"-funktion, som man kan 
sætte foran specielle tegn eller mellemrum, så karakteren læses korrekt, og ikke 
fx som et mellemrum i kommandolinjen.  

I de fleste terminaler (fx PuTTY, UltraEdit, miniconda...) fungerer *tab* som en 
autocomplete. Dvs. man kan starte på at skrive et mappenavn eller filnavn, og 
derefter trykke på tab. Terminalen vil da liste eller cykle igennem de givne 
muligheder man har. Det er meget praktisk ved især lange fil- og mappenavne.

Øvelse
+++++++++++++++++++++

Prøv selv at navigér rundt i terminalen og forsøg fx:

 | 1) at lave to mapper
 | 2) at oprette filer
 | 3) at flytte filer rundt mellem mapper
 | 4) at rydde op efter jer selv ved at slette filer og mapper
 | 5) at kopier en hel mappe og dens undermapper med indhold over et andet sted på 
      drevet (hint: */s* er et eksempel på en parameter, der kan tilføjes kommandolinjen. 
      Søg selv videre på nettet)
 
 
Diverse programmer
+++++++++++++++++++++++++++++++++++++++

Nedenfor følger en liste over brugbare standardprogrammers anvendelse i terminalen.

=============  ==========================================================  ===========================================
**Program**    **Beskrivelse**                                             **Eksempel på brug**
-------------  ----------------------------------------------------------  -------------------------------------------
cat            Sammensæt flere filer til en samlet og vis på skærm         > cat test1 test2 >testsamlet
echo           Gentag input på skærmen, som kan pipes videre, fx til proj  > echo 12.4 55.8 36 | cct +proj=cart 
grep           Søg efter bestemte udtryk i asciitekst og print til skærm   > grep -n DK test1
vim            Tekstbehandlingsprogram, som notesblok, Notepad++ osv.      > vim test1
=============  ==========================================================  ===========================================

Alle programmer kan yderligere udforskes ved at bruge parameteren *--help*, fx::
 
	> grep --help

Præsentation af FIRE 
---------------------
FIRE indeholder alt den relevante information, som refgeo gør. Der er punktnumre,
identer, skitser, koordinater, tidsserier, beskrivelse, afmærkningstyper osv. osv.
Strukturen er dog en helt anden og meget mere overskuelig og vedligeholdelsesvenlig
nede i maven på databasen, hvilket gør FIRE til en markant forbedring af et af 
vores vigtigste dataarkiver. 

Dog er alt vores nuværende udjævnings- og datahåndteringssoftware (fx. ADJ, 
``valde`` og ``vedl.pl``) tilpasset refgeo og det famøse KSM-format, hvilket ikke kan
bruges i det nye setup. 
Derfor har vi udviklet adskillige kommandolinjekald, som har til formål at lade 
brugeren se ned i databasen, udtrække det data der er relevant, putte ny data 
ned i databasen osv. 
Det er en løbende opgave, hvor der bliver udviklet den funktionalitet, som viser 
sig nødvendig og brugbar til et gentagent formål.

Hvis nogen havde håbet på en lækkert designet brugergrænseflade med søgebokse og 
kasser, der kan hakkes af og en knap med *beregn* til til at lave en udjævning, 
som derefter bliver vist i QGIS, så må vi skuffe. 
Det er ikke der vi er; vi er slet ikke nok folk til at kunne retfærdiggøre at 
bruge tid og penge på at udvikle sådan noget, og desuden vil det være et hejs at 
vedligeholde og videudvikle kode til, hvilket vi helst vil gøre selv.
Derfor er det altså stadig kommandolinjekald, som er vejen frem! Men dermed bliver 
overgangen til ny database og beregningssoftware nok ikke så slem alligevel.

Nedenfor uddybes de funktionaliteter vi på nuværende tidspunkt har udviklet. Det er 
alle underprogrammer under fire og køres derfor ved først at kalde ``fire`` efterfulgt 
af underkommandoen.

info
++++++++++++++++++++

En grundliggende funktionalitet er at kunne se hvilken data, der ligger i databasen, 
altså hvilken info man har i arkivet. Til det er der udviklet et kommandolinjeprogram 
kaldet `fire info`. Man kan se hvad programmet indeholder ved at taste 

fremsøge et punkt og se hvilke oplysninger,
der knytter sig til det. Det kunne man før med ``valde``, eller Valdemar i tjenesten,
og det kan man selvfølgelig også med FIRE. Her hedder funktionen blot ``info`` og kaldes 
via fire::

	> fire info --help

Hvis du vil have oplysninger om givent punkt, skrives fx:

	> fire info g.i.2010

	Det er ligegyldet om der skrives med stort eller småt


mtl
++++++++++++++++++++++++++++++++
Der er blevet udviklet et kommandolinjeprogram til udjævningsberegning kaldet ``mtl``. 
Læs om hvordan programmet kaldes :ref:`her <kommandolinjeprogrammer_mtl>`


Revision
++++++++++++++++


Opdatering af database
++++++++++++++++++++++

Beregning
++++++++++++++++

Visualisering i QGIS
------------------------




